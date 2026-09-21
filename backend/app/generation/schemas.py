import uuid
from typing import Literal

from pydantic import BaseModel, Field, field_validator


class AskRequest(BaseModel):
    question: str = Field(min_length=2, max_length=2000)
    document_ids: list[uuid.UUID] = Field(default_factory=list, max_length=100)
    retrieval_limit: int = Field(default=8, ge=1, le=20)
    provider: Literal["local", "groq"] = "local"
    local_server_port: int | None = Field(default=None, ge=1, le=65535)

    @field_validator("question")
    @classmethod
    def question_must_contain_text(cls, value: str) -> str:
        value = value.strip()
        if len(value) < 2:
            raise ValueError("Question must contain at least two non-whitespace characters")
        return value


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
