import uuid

from pydantic import BaseModel, Field


class AskRequest(BaseModel):
    question: str = Field(min_length=2, max_length=2000)
    document_ids: list[uuid.UUID] = Field(default_factory=list, max_length=100)
    retrieval_limit: int = Field(default=8, ge=1, le=20)


class Citation(BaseModel):
    document_id: uuid.UUID
    document_name: str
    page: int | None
    section: str | None
    snippet: str


class AskResponse(BaseModel):
    answer: str
    citations: list[Citation]
    retrieved_chunks: int
    supported: bool
