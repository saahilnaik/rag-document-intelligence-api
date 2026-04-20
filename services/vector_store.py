import threading
from typing import Optional

from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_core.retrievers import BaseRetriever
from langchain_huggingface import HuggingFaceEmbeddings

from core.config import get_settings


class VectorStoreManager:
    def __init__(self):
        self._store: Optional[Chroma] = None
        self._lock = threading.Lock()

    def _ensure_initialized(self) -> None:
        if self._store is not None:
            return
        with self._lock:
            if self._store is not None:
                return
            settings = get_settings()
            embeddings = HuggingFaceEmbeddings(
                model_name=settings.EMBEDDING_MODEL,
                model_kwargs={"device": settings.EMBEDDING_DEVICE},
                encode_kwargs={"normalize_embeddings": True},
            )
            self._store = Chroma(
                collection_name=settings.CHROMA_COLLECTION,
                embedding_function=embeddings,
                persist_directory=settings.CHROMA_PERSIST_DIR,
            )

    def store_chunks(self, chunks: list[Document]) -> None:
        self._ensure_initialized()
        self._store.add_documents(chunks)

    def retrieve(
        self, query: str, k: int, doc_id: Optional[str] = None
    ) -> list[tuple[Document, float]]:
        self._ensure_initialized()
        search_kwargs: dict = {"k": k}
        if doc_id:
            search_kwargs["filter"] = {"doc_id": doc_id}
        return self._store.similarity_search_with_relevance_scores(query, **search_kwargs)

    def delete_document(self, doc_id: str) -> None:
        self._ensure_initialized()
        self._store._collection.delete(where={"doc_id": doc_id})

    def as_retriever(self, doc_id: Optional[str] = None, k: int = 5) -> BaseRetriever:
        self._ensure_initialized()
        search_kwargs: dict = {"k": k}
        if doc_id:
            search_kwargs["filter"] = {"doc_id": doc_id}
        return self._store.as_retriever(search_kwargs=search_kwargs)


vector_store_manager = VectorStoreManager()
