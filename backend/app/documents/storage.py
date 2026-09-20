import uuid
from abc import ABC, abstractmethod
from functools import lru_cache
from pathlib import Path

from app.config import get_settings


class StorageProvider(ABC):
    @abstractmethod
    def save(self, user_id: uuid.UUID, document_id: uuid.UUID, suffix: str, data: bytes) -> str:
        raise NotImplementedError

    @abstractmethod
    def delete(self, storage_path: str) -> None:
        raise NotImplementedError

    @abstractmethod
    def read(self, storage_path: str) -> bytes:
        raise NotImplementedError


class LocalStorage(StorageProvider):
    def __init__(self, root: Path):
        self.root = root.resolve()
        self.root.mkdir(parents=True, exist_ok=True)

    def save(self, user_id: uuid.UUID, document_id: uuid.UUID, suffix: str, data: bytes) -> str:
        relative = Path(str(user_id)) / f"{document_id}{suffix}"
        destination = (self.root / relative).resolve()
        if self.root not in destination.parents:
            raise ValueError("Invalid storage path")
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(data)
        return relative.as_posix()

    def delete(self, storage_path: str) -> None:
        target = (self.root / storage_path).resolve()
        if self.root not in target.parents:
            raise ValueError("Invalid storage path")
        target.unlink(missing_ok=True)

    def read(self, storage_path: str) -> bytes:
        target = (self.root / storage_path).resolve()
        if self.root not in target.parents:
            raise ValueError("Invalid storage path")
        return target.read_bytes()


@lru_cache
def get_storage() -> StorageProvider:
    settings = get_settings()
    if settings.storage_backend != "local":
        raise RuntimeError(f"Unsupported storage backend: {settings.storage_backend}")
    return LocalStorage(settings.local_storage_path)
