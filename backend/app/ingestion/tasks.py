import uuid

import structlog
from redis import Redis
from rq import Queue, Retry
from sqlalchemy import delete
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database.models import Document, DocumentChunk, DocumentStatus
from app.database.session import SessionLocal
from app.documents.storage import StorageProvider, get_storage
from app.ingestion.chunking import chunk_pages
from app.ingestion.extraction import extract_document
from app.retrieval.embeddings import EmbeddingProvider, get_embedding_provider

logger = structlog.get_logger()


def enqueue_document(document_id: uuid.UUID) -> bool:
    settings = get_settings()
    try:
        queue = Queue("ingestion", connection=Redis.from_url(settings.redis_url))
        queue.enqueue(
            "app.ingestion.tasks.process_document_job",
            str(document_id),
            retry=Retry(max=3, interval=[10, 30, 90]),
            job_timeout="15m",
            result_ttl=3600,
        )
        return True
    except Exception as exc:
        logger.warning(
            "ingestion.enqueue_failed", document_id=str(document_id), error=type(exc).__name__
        )
        if settings.process_documents_inline:
            process_document_job(str(document_id))
            return True
        return False


def ingest_document(
    db: Session,
    document: Document,
    storage: StorageProvider,
    embeddings: EmbeddingProvider,
) -> None:
    document.status = DocumentStatus.processing
    document.error_message = None
    db.commit()
    try:
        pages = extract_document(storage.read(document.storage_path), document.file_type)
        chunks = chunk_pages(pages)
        if not chunks:
            raise ValueError("The document produced no searchable text chunks")
        vectors = embeddings.embed([chunk.content for chunk in chunks])
        db.execute(delete(DocumentChunk).where(DocumentChunk.document_id == document.id))
        db.add_all(
            [
                DocumentChunk(
                    document_id=document.id,
                    chunk_index=index,
                    content=chunk.content,
                    page_number=chunk.page_number,
                    section=chunk.section,
                    token_count=chunk.token_count,
                    embedding=vector,
                )
                for index, (chunk, vector) in enumerate(zip(chunks, vectors, strict=True))
            ]
        )
        document.status = DocumentStatus.ready
        db.commit()
        logger.info("ingestion.complete", document_id=str(document.id), chunks=len(chunks))
    except Exception as exc:
        db.rollback()
        document = db.get(Document, document.id)
        if document:
            document.status = DocumentStatus.failed
            document.error_message = f"Processing failed: {type(exc).__name__}"
            db.commit()
        logger.exception("ingestion.failed", document_id=str(document.id))
        raise


def process_document_job(document_id: str) -> None:
    with SessionLocal() as db:
        document = db.get(Document, uuid.UUID(document_id))
        if document is None or document.status == DocumentStatus.deleted:
            logger.warning("ingestion.document_missing", document_id=document_id)
            return
        ingest_document(db, document, get_storage(), get_embedding_provider())
