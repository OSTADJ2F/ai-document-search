from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.database.models import User  # noqa: F401
from app.database.session import Base, get_db
from app.documents.storage import LocalStorage, get_storage
from app.main import app


@pytest.fixture
def db(tmp_path) -> Generator[Session, None, None]:  # type: ignore[no-untyped-def]
    engine = create_engine(
        f"sqlite:///{tmp_path / 'test.db'}", connect_args={"check_same_thread": False}
    )
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, expire_on_commit=False)
    with factory() as session:
        yield session
    Base.metadata.drop_all(engine)


@pytest.fixture
def client(db: Session, tmp_path) -> Generator[TestClient, None, None]:  # type: ignore[no-untyped-def]
    def override_db() -> Generator[Session, None, None]:
        yield db

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_storage] = lambda: LocalStorage(tmp_path / "uploads")
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def auth_headers(client: TestClient) -> dict[str, str]:
    response = client.post(
        "/auth/register",
        json={"email": "owner@example.com", "password": "correct horse battery staple"},
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
