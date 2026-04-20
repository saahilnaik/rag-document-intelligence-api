import threading
from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from api.schemas import DocumentStatus


class DocumentRegistry:
    def __init__(self):
        self._store: dict[str, DocumentStatus] = {}
        self._lock = threading.Lock()

    def register(self, doc_id: UUID, filename: str) -> DocumentStatus:
        entry = DocumentStatus(
            doc_id=doc_id,
            filename=filename,
            status="processing",
            created_at=datetime.now(timezone.utc),
        )
        with self._lock:
            self._store[str(doc_id)] = entry
        return entry

    def mark_ready(self, doc_id: UUID, chunk_count: int) -> None:
        with self._lock:
            entry = self._store.get(str(doc_id))
            if entry:
                self._store[str(doc_id)] = entry.model_copy(
                    update={"status": "ready", "chunk_count": chunk_count}
                )

    def mark_failed(self, doc_id: UUID, error: str) -> None:
        with self._lock:
            entry = self._store.get(str(doc_id))
            if entry:
                self._store[str(doc_id)] = entry.model_copy(
                    update={"status": "failed", "error": error}
                )

    def get(self, doc_id: UUID) -> Optional[DocumentStatus]:
        with self._lock:
            return self._store.get(str(doc_id))

    def list_all(self) -> list[DocumentStatus]:
        with self._lock:
            return list(self._store.values())

    def delete(self, doc_id: UUID) -> bool:
        with self._lock:
            return self._store.pop(str(doc_id), None) is not None


document_registry = DocumentRegistry()
