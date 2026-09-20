import hashlib
import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.auth.dependencies import CurrentUser
from app.config import get_settings
from app.database.models import AuditLog, Document, DocumentStatus
from app.database.session import get_db
from app.documents.schemas import DeleteResponse, DocumentListResponse, DocumentResponse
from app.documents.storage import StorageProvider, get_storage
from app.documents.validation import InvalidDocument, validate_document
from app.ingestion.tasks import enqueue_document

router = APIRouter(prefix="/documents", tags=["documents"])
Database = Annotated[Session, Depends(get_db)]
Storage = Annotated[StorageProvider, Depends(get_storage)]


def owned_document(db: Session, document_id: uuid.UUID, user_id: uuid.UUID) -> Document:
    document = db.scalar(
        select(Document).where(
            Document.id == document_id,
            Document.user_id == user_id,
            Document.status != DocumentStatus.deleted,
        )
    )
    if document is None:
        raise HTTPException(status_code=404, detail="Document not found")
    return document


@router.post("", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    current_user: CurrentUser,
    db: Database,
    storage: Storage,
    file: Annotated[UploadFile, File(description="PDF, UTF-8 text, or Markdown")],
) -> Document:
    settings = get_settings()
    data = await file.read(settings.max_upload_bytes + 1)
    if len(data) > settings.max_upload_bytes:
        raise HTTPException(
            status_code=413, detail=f"File exceeds the {settings.max_upload_size_mb} MB limit"
        )
    try:
        filename, file_type = validate_document(file.filename or "", data)
    except InvalidDocument as exc:
        raise HTTPException(status_code=415, detail=str(exc)) from exc

    content_hash = hashlib.sha256(data).hexdigest()
    duplicate = db.scalar(
        select(Document).where(
            Document.user_id == current_user.id,
            Document.content_hash == content_hash,
            Document.status != DocumentStatus.deleted,
        )
    )
    if duplicate:
        raise HTTPException(status_code=409, detail="This document has already been uploaded")

    document_id = uuid.uuid4()
    suffix = ".md" if file_type == "markdown" else f".{file_type}"
    storage_path = storage.save(current_user.id, document_id, suffix, data)
    document = Document(
        id=document_id,
        user_id=current_user.id,
        filename=filename,
        file_type=file_type,
        storage_path=storage_path,
        file_size=len(data),
        content_hash=content_hash,
        status=DocumentStatus.uploaded,
    )
    db.add(document)
    db.add(
        AuditLog(
            user_id=current_user.id,
            action="document.upload",
            resource_type="document",
            resource_id=str(document.id),
            metadata_json={"filename": filename, "size": len(data)},
        )
    )
    try:
        db.commit()
    except Exception:
        storage.delete(storage_path)
        raise
    db.refresh(document)
    enqueue_document(document.id)
    return document


@router.get("", response_model=DocumentListResponse)
def list_documents(
    current_user: CurrentUser,
    db: Database,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 25,
) -> DocumentListResponse:
    filters = (Document.user_id == current_user.id, Document.status != DocumentStatus.deleted)
    total = db.scalar(select(func.count()).select_from(Document).where(*filters)) or 0
    items = list(
        db.scalars(
            select(Document)
            .where(*filters)
            .order_by(Document.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
    )
    return DocumentListResponse(items=items, total=total, page=page, page_size=page_size)


@router.get("/{document_id}", response_model=DocumentResponse)
def get_document(document_id: uuid.UUID, current_user: CurrentUser, db: Database) -> Document:
    return owned_document(db, document_id, current_user.id)


@router.delete("/{document_id}", response_model=DeleteResponse)
def delete_document(
    document_id: uuid.UUID, current_user: CurrentUser, db: Database, storage: Storage
) -> DeleteResponse:
    document = owned_document(db, document_id, current_user.id)
    storage.delete(document.storage_path)
    document.status = DocumentStatus.deleted
    document.error_message = None
    db.add(
        AuditLog(
            user_id=current_user.id,
            action="document.delete",
            resource_type="document",
            resource_id=str(document.id),
        )
    )
    db.commit()
    return DeleteResponse(message="Document deleted")
