import uuid

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.database.models import Document, DocumentChunk, DocumentStatus, User
from app.retrieval.embeddings import LocalHashEmbeddingProvider


def add_ready_document(db: Session, user: User, name: str, passages: list[str]) -> Document:
    document = Document(
        user_id=user.id,
        filename=name,
        file_type="txt",
        storage_path=f"{uuid.uuid4()}.txt",
        file_size=100,
        content_hash=uuid.uuid4().hex * 2,
        status=DocumentStatus.ready,
    )
    db.add(document)
    db.flush()
    vectors = LocalHashEmbeddingProvider().embed(passages)
    db.add_all(
        [
            DocumentChunk(
                document_id=document.id,
                chunk_index=index,
                content=content,
                page_number=index + 1,
                token_count=len(content.split()),
                embedding=vectors[index],
            )
            for index, content in enumerate(passages)
        ]
    )
    db.commit()
    return document


def test_hybrid_search_ranks_relevant_owned_passage(
    client: TestClient, auth_headers: dict[str, str], db: Session
) -> None:
    owner = db.query(User).filter_by(email="owner@example.com").one()
    document = add_ready_document(
        db,
        owner,
        "risk-report.txt",
        [
            "The primary operational risk is supply chain disruption and supplier concentration.",
            "The company picnic is scheduled for a sunny Friday in July.",
        ],
    )
    response = client.post(
        "/search",
        headers=auth_headers,
        json={"query": "What is the supply chain risk?", "limit": 5},
    )
    assert response.status_code == 200
    results = response.json()["results"]
    assert results[0]["document_id"] == str(document.id)
    assert "supply chain" in results[0]["content"]
    assert results[0]["page_number"] == 1
    assert results[0]["score"] >= results[1]["score"]


def test_search_filters_and_user_isolation(
    client: TestClient, auth_headers: dict[str, str], db: Session
) -> None:
    owner = db.query(User).filter_by(email="owner@example.com").one()
    kept = add_ready_document(db, owner, "kept.txt", ["alpha launch schedule"])
    add_ready_document(db, owner, "ignored.txt", ["alpha secret alternative"])
    other = User(email="outsider@example.com", password_hash="unused")
    db.add(other)
    db.flush()
    add_ready_document(db, other, "private.txt", ["alpha private outsider data"])

    response = client.post(
        "/search",
        headers=auth_headers,
        json={"query": "alpha", "document_ids": [str(kept.id)]},
    )
    assert response.status_code == 200
    assert {item["document_id"] for item in response.json()["results"]} == {str(kept.id)}
