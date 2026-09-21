import time
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.auth.dependencies import CurrentUser
from app.database.models import AuditLog
from app.database.session import get_db
from app.generation.providers import (
    GenerationProvider,
    GenerationProviderNotConfiguredError,
    LlamaCppGenerationProvider,
    get_deepseek_generation_provider,
    get_generation_provider,
    get_groq_generation_provider,
)
from app.generation.schemas import AskRequest, AskResponse, Citation
from app.observability import GENERATION_LATENCY
from app.retrieval.embeddings import EmbeddingProvider, get_embedding_provider
from app.retrieval.search import hybrid_search
from app.security.rate_limit import enforce_rate_limit

router = APIRouter(tags=["question answering"], dependencies=[Depends(enforce_rate_limit)])
Database = Annotated[Session, Depends(get_db)]
Embeddings = Annotated[EmbeddingProvider, Depends(get_embedding_provider)]
Generator = Annotated[GenerationProvider, Depends(get_generation_provider)]
GroqGenerator = Annotated[GenerationProvider, Depends(get_groq_generation_provider)]
DeepSeekGenerator = Annotated[
    GenerationProvider, Depends(get_deepseek_generation_provider)
]


@router.post("/ask", response_model=AskResponse)
def ask_documents(
    payload: AskRequest,
    current_user: CurrentUser,
    db: Database,
    embeddings: Embeddings,
    local_generator: Generator,
    groq_generator: GroqGenerator,
    deepseek_generator: DeepSeekGenerator,
) -> AskResponse:
    results = hybrid_search(
        db=db,
        embeddings=embeddings,
        user_id=current_user.id,
        query=payload.question,
        document_ids=payload.document_ids,
        file_type=None,
        uploaded_after=None,
        limit=payload.retrieval_limit,
    )
    generators = {
        "local": local_generator,
        "groq": groq_generator,
        "deepseek": deepseek_generator,
    }
    generator = generators[payload.provider]
    if payload.local_server_port is not None and isinstance(
        generator, LlamaCppGenerationProvider
    ):
        generator = generator.with_port(payload.local_server_port)
    started = time.perf_counter()
    try:
        generated = generator.generate(payload.question, results)
    except GenerationProviderNotConfiguredError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=503, detail="The answer provider is temporarily unavailable"
        ) from exc
    finally:
        GENERATION_LATENCY.observe(time.perf_counter() - started)
    citations = [
        Citation(
            document_id=results[index].document_id,
            document_name=results[index].document_name,
            page=results[index].page_number,
            section=results[index].section,
            snippet=results[index].content[:500],
        )
        for index in generated.cited_result_indexes
        if 0 <= index < len(results)
    ]
    if generated.supported and not citations:
        raise HTTPException(
            status_code=503, detail="The answer provider returned unverifiable output"
        )
    db.add(
        AuditLog(
            user_id=current_user.id,
            action="answer.generate",
            metadata_json={
                "retrieved_chunks": len(results),
                "citations": len(citations),
                "supported": generated.supported,
                "provider": payload.provider,
            },
        )
    )
    db.commit()
    return AskResponse(
        answer=generated.text,
        citations=citations,
        retrieved_chunks=len(results),
        supported=generated.supported,
    )
