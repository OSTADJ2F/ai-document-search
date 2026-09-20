import math
import re
import uuid
from datetime import datetime

from sqlalchemy import bindparam, select, text
from sqlalchemy.orm import Session

from app.database.models import Document, DocumentChunk, DocumentStatus
from app.retrieval.embeddings import EmbeddingProvider
from app.retrieval.schemas import SearchResult


def _cosine(left: list[float], right: list[float]) -> float:
    numerator = sum(a * b for a, b in zip(left, right, strict=True))
    left_norm = math.sqrt(sum(value * value for value in left))
    right_norm = math.sqrt(sum(value * value for value in right))
    return numerator / (left_norm * right_norm) if left_norm and right_norm else 0.0


def _keyword_score(query: str, content: str) -> float:
    query_terms = set(re.findall(r"[a-z0-9]+", query.lower()))
    content_terms = set(re.findall(r"[a-z0-9]+", content.lower()))
    return len(query_terms & content_terms) / len(query_terms) if query_terms else 0.0


def hybrid_search(
    db: Session,
    embeddings: EmbeddingProvider,
    user_id: uuid.UUID,
    query: str,
    document_ids: list[uuid.UUID],
    file_type: str | None,
    uploaded_after: datetime | None,
    limit: int,
) -> list[SearchResult]:
    query_vector = embeddings.embed([query])[0]
    if db.bind and db.bind.dialect.name == "postgresql":
        return _postgres_search(
            db, user_id, query, query_vector, document_ids, file_type, uploaded_after, limit
        )
    return _portable_search(
        db, user_id, query, query_vector, document_ids, file_type, uploaded_after, limit
    )


def _portable_search(
    db: Session,
    user_id: uuid.UUID,
    query: str,
    query_vector: list[float],
    document_ids: list[uuid.UUID],
    file_type: str | None,
    uploaded_after: datetime | None,
    limit: int,
) -> list[SearchResult]:
    statement = (
        select(DocumentChunk, Document)
        .join(Document, Document.id == DocumentChunk.document_id)
        .where(Document.user_id == user_id, Document.status == DocumentStatus.ready)
    )
    if document_ids:
        statement = statement.where(Document.id.in_(document_ids))
    if file_type:
        statement = statement.where(Document.file_type == file_type)
    if uploaded_after:
        statement = statement.where(Document.created_at >= uploaded_after)
    results: list[SearchResult] = []
    for chunk, document in db.execute(statement):
        semantic = max(0.0, _cosine(query_vector, chunk.embedding))
        keyword = _keyword_score(query, chunk.content)
        score = semantic * 0.7 + keyword * 0.3
        results.append(
            SearchResult(
                chunk_id=chunk.id,
                document_id=document.id,
                document_name=document.filename,
                file_type=document.file_type,
                content=chunk.content,
                page_number=chunk.page_number,
                section=chunk.section,
                semantic_score=round(semantic, 6),
                keyword_score=round(keyword, 6),
                score=round(score, 6),
            )
        )
    return sorted(results, key=lambda item: item.score, reverse=True)[:limit]


def _postgres_search(
    db: Session,
    user_id: uuid.UUID,
    query: str,
    query_vector: list[float],
    document_ids: list[uuid.UUID],
    file_type: str | None,
    uploaded_after: datetime | None,
    limit: int,
) -> list[SearchResult]:
    filters = ["d.user_id = :user_id", "d.status = 'ready'"]
    params: dict[str, object] = {
        "user_id": user_id,
        "query": query,
        "embedding": "[" + ",".join(str(value) for value in query_vector) + "]",
        "limit": limit,
    }
    if document_ids:
        filters.append("d.id IN :document_ids")
        params["document_ids"] = document_ids
    if file_type:
        filters.append("d.file_type = :file_type")
        params["file_type"] = file_type
    if uploaded_after:
        filters.append("d.created_at >= :uploaded_after")
        params["uploaded_after"] = uploaded_after
    statement = text(
        f"""
        SELECT c.id AS chunk_id, d.id AS document_id, d.filename AS document_name,
               d.file_type, c.content, c.page_number, c.section,
               GREATEST(0, 1 - (c.embedding <=> CAST(:embedding AS vector))) AS semantic_score,
               ts_rank_cd(
                   to_tsvector('english', c.content),
                   websearch_to_tsquery('english', :query)
               ) AS keyword_score,
               GREATEST(0, 1 - (c.embedding <=> CAST(:embedding AS vector))) * 0.7 +
               ts_rank_cd(
                   to_tsvector('english', c.content),
                   websearch_to_tsquery('english', :query)
               ) * 0.3 AS score
        FROM document_chunks c JOIN documents d ON d.id = c.document_id
        WHERE {" AND ".join(filters)}
        ORDER BY score DESC LIMIT :limit
        """  # noqa: S608 -- filter fragments are controlled constants
    )
    if document_ids:
        statement = statement.bindparams(bindparam("document_ids", expanding=True))
    return [SearchResult(**dict(row)) for row in db.execute(statement, params).mappings()]
