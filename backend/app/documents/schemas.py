import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.database.models import DocumentStatus


class DocumentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    filename: str
    file_type: str
    file_size: int
    status: DocumentStatus
    error_message: str | None
    created_at: datetime
    updated_at: datetime


class DocumentListResponse(BaseModel):
    items: list[DocumentResponse]
    total: int
    page: int = Field(ge=1)
    page_size: int = Field(ge=1)


class DeleteResponse(BaseModel):
    message: str
