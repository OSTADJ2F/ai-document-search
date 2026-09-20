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


class S3Storage(StorageProvider):
    def __init__(
        self,
        bucket: str,
        endpoint_url: str | None,
        region: str,
        access_key_id: str | None,
        secret_access_key: str | None,
    ):
        import boto3

        self.bucket = bucket
        self.client = boto3.client(
            "s3",
            endpoint_url=endpoint_url,
            region_name=region,
            aws_access_key_id=access_key_id,
            aws_secret_access_key=secret_access_key,
        )

    def save(self, user_id: uuid.UUID, document_id: uuid.UUID, suffix: str, data: bytes) -> str:
        key = f"{user_id}/{document_id}{suffix}"
        self.client.put_object(Bucket=self.bucket, Key=key, Body=data)
        return key

    def delete(self, storage_path: str) -> None:
        self.client.delete_object(Bucket=self.bucket, Key=storage_path)

    def read(self, storage_path: str) -> bytes:
        response = self.client.get_object(Bucket=self.bucket, Key=storage_path)
        return response["Body"].read()


@lru_cache
def get_storage() -> StorageProvider:
    settings = get_settings()
    if settings.storage_backend == "local":
        return LocalStorage(settings.local_storage_path)
    if settings.storage_backend == "s3" and settings.s3_bucket:
        return S3Storage(
            settings.s3_bucket,
            settings.s3_endpoint_url,
            settings.s3_region,
            settings.s3_access_key_id,
            settings.s3_secret_access_key,
        )
    raise RuntimeError(f"Invalid or unsupported storage backend: {settings.storage_backend}")
