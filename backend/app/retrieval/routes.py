import time
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth.dependencies import CurrentUser
from app.database.session import get_db
from app.observability import CACHE_OPERATIONS, SEARCH_LATENCY
from app.retrieval.cache import SearchCache, get_search_cache
from app.retrieval.embeddings import EmbeddingProvider, get_embedding_provider
from app.retrieval.schemas import SearchRequest, SearchResponse
from app.retrieval.search import hybrid_search
from app.security.rate_limit import enforce_rate_limit

router = APIRouter(tags=["retrieval"], dependencies=[Depends(enforce_rate_limit)])
Database = Annotated[Session, Depends(get_db)]
Embeddings = Annotated[EmbeddingProvider, Depends(get_embedding_provider)]
Cache = Annotated[SearchCache, Depends(get_search_cache)]


@router.post("/search", response_model=SearchResponse)
def search_documents(
    payload: SearchRequest,
    current_user: CurrentUser,
    db: Database,
    embeddings: Embeddings,
    cache: Cache,
) -> SearchResponse:
    cache_key = cache.key(str(current_user.id), payload.model_dump(mode="json"))
    cached = cache.get(cache_key)
    if cached:
        CACHE_OPERATIONS.labels("hit").inc()
        return SearchResponse.model_validate_json(cached)
    CACHE_OPERATIONS.labels("miss").inc()
    started = time.perf_counter()
    try:
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
    finally:
        SEARCH_LATENCY.observe(time.perf_counter() - started)
    response = SearchResponse(query=payload.query, results=results, total=len(results))
    cache.set(cache_key, response.model_dump_json())
    return response
