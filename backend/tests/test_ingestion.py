import uuid

import pytest
from pypdf.errors import PdfReadError
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.models import Document, DocumentChunk, DocumentStatus, User
from app.documents.storage import LocalStorage
from app.ingestion.chunking import chunk_pages
from app.ingestion.extraction import ExtractedPage
from app.ingestion.tasks import ingest_document
from app.retrieval.embeddings import LocalHashEmbeddingProvider


def create_document(db: Session, storage: LocalStorage, data: bytes, file_type: str) -> Document:
    user = User(email=f"{uuid.uuid4()}@example.com", password_hash="not-used")
    db.add(user)
    db.flush()
    document = Document(
        user_id=user.id,
        filename=f"sample.{file_type}",
        file_type=file_type,
        storage_path="placeholder",
        file_size=len(data),
        content_hash="a" * 64,
    )
    db.add(document)
    db.flush()
    document.storage_path = storage.save(user.id, document.id, f".{file_type}", data)
    db.commit()
    return document


def test_ingestion_extracts_chunks_and_embeddings(db: Session, tmp_path) -> None:  # type: ignore[no-untyped-def]
    storage = LocalStorage(tmp_path / "uploads")
    text = ("# Risk\nSupply chain disruption is the primary operational risk. " * 150).encode()
    document = create_document(db, storage, text, "markdown")
    ingest_document(db, document, storage, LocalHashEmbeddingProvider())

    db.refresh(document)
    chunks = list(
        db.scalars(
            select(DocumentChunk)
            .where(DocumentChunk.document_id == document.id)
            .order_by(DocumentChunk.chunk_index)
        )
    )
    assert document.status == DocumentStatus.ready
    assert len(chunks) >= 2
    assert len(chunks[0].embedding) == 384
    assert chunks[0].section == "Risk"


def test_corrupted_pdf_is_marked_failed(db: Session, tmp_path) -> None:  # type: ignore[no-untyped-def]
    storage = LocalStorage(tmp_path / "uploads")
    document = create_document(db, storage, b"%PDF-not-really-a-pdf", "pdf")
    with pytest.raises((PdfReadError, ValueError)):
        ingest_document(db, document, storage, LocalHashEmbeddingProvider())
    db.refresh(document)
    assert document.status == DocumentStatus.failed
    assert document.error_message and "Processing failed" in document.error_message


def test_chunking_preserves_overlap_and_page_metadata() -> None:
    words = [f"word-{index}" for index in range(20)]
    chunks = chunk_pages([ExtractedPage(" ".join(words), 7)], chunk_size=10, overlap=2)
    assert len(chunks) == 3
    assert chunks[0].content.split()[-2:] == chunks[1].content.split()[:2]
    assert all(chunk.page_number == 7 for chunk in chunks)
