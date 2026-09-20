import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class SearchRequest(BaseModel):
    query: str = Field(min_length=2, max_length=1000)
    document_ids: list[uuid.UUID] = Field(default_factory=list, max_length=100)
    file_type: str | None = Field(default=None, pattern="^(pdf|txt|markdown)$")
    uploaded_after: datetime | None = None
    limit: int = Field(default=8, ge=1, le=50)


class SearchResult(BaseModel):
    chunk_id: uuid.UUID
    document_id: uuid.UUID
    document_name: str
    file_type: str
    content: str
    page_number: int | None
    section: str | None
    semantic_score: float
    keyword_score: float
    score: float


class SearchResponse(BaseModel):
    query: str
    results: list[SearchResult]
    total: int
