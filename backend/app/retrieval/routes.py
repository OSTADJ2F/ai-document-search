from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth.dependencies import CurrentUser
from app.database.session import get_db
from app.retrieval.embeddings import EmbeddingProvider, get_embedding_provider
from app.retrieval.schemas import SearchRequest, SearchResponse
from app.retrieval.search import hybrid_search

router = APIRouter(tags=["retrieval"])
Database = Annotated[Session, Depends(get_db)]
Embeddings = Annotated[EmbeddingProvider, Depends(get_embedding_provider)]


@router.post("/search", response_model=SearchResponse)
def search_documents(
    payload: SearchRequest,
    current_user: CurrentUser,
    db: Database,
    embeddings: Embeddings,
) -> SearchResponse:
    results = hybrid_search(
        db=db,
        embeddings=embeddings,
        user_id=current_user.id,
        query=payload.query,
        document_ids=payload.document_ids,
        file_type=payload.file_type,
        uploaded_after=payload.uploaded_after,
        limit=payload.limit,
    )
    return SearchResponse(query=payload.query, results=results, total=len(results))
