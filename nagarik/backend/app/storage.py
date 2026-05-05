"""Object storage abstraction. Local filesystem now, S3-compatible interface for later."""
from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Protocol

from app.config import get_settings


class ObjectStore(Protocol):
    def put(self, key: str, content: bytes) -> str:
        """Persist `content` at `key`, return the storage path/URI."""
        ...

    def get(self, key: str) -> bytes:
        ...


class LocalFsStore:
    def __init__(self, base_path: Path) -> None:
        self.base = base_path
        self.base.mkdir(parents=True, exist_ok=True)

    def _resolve(self, key: str) -> Path:
        # Reject path traversal — keys are storage-internal, never user-supplied directly.
        path = (self.base / key).resolve()
        if not str(path).startswith(str(self.base)):
            raise ValueError(f"Refusing to write outside storage root: {key}")
        return path

    def put(self, key: str, content: bytes) -> str:
        path = self._resolve(key)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
        return str(path)

    def get(self, key: str) -> bytes:
        return self._resolve(key).read_bytes()


_store: ObjectStore | None = None


def get_store() -> ObjectStore:
    global _store
    if _store is None:
        settings = get_settings()
        if settings.storage_backend == "local":
            _store = LocalFsStore(settings.storage_local_path_abs)
        else:
            # Future: S3, GCS, etc. Same Protocol, swap-in.
            raise NotImplementedError(f"Storage backend '{settings.storage_backend}' not implemented")
    return _store


def make_storage_key(source_slug: str, raw_bytes: bytes, content_type: str) -> str:
    """
    Deterministic, content-addressed key. Same payload → same key → idempotent writes.
    Path is partitioned by date for sane filesystem listing.
    """
    digest = hashlib.sha256(raw_bytes).hexdigest()
    ext = {
        "text/html": "html",
        "application/pdf": "pdf",
        "application/json": "json",
    }.get(content_type, "bin")
    today = datetime.now(timezone.utc).strftime("%Y/%m/%d")
    return f"{source_slug}/{today}/{digest}.{ext}"


def checksum_of(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()
