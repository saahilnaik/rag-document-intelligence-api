import logging
import threading
from typing import Optional

from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_core.retrievers import BaseRetriever
from langchain_huggingface import HuggingFaceEmbeddings

from core.config import get_settings

logger = logging.getLogger(__name__)


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
        logger.info(f"Stored {len(chunks)} chunks in vector store")

    def retrieve(
        self, query: str, k: int, doc_id: Optional[str] = None
    ) -> list[tuple[Document, float]]:
        self._ensure_initialized()
        
        # Get embeddings for the query
        embeddings = self._store._embedding_function
        query_embedding = embeddings.embed_query(query)
        
        # Query Chroma collection with where filter
        where_filter = {"doc_id": doc_id} if doc_id else None
        results = self._store._collection.query(
            query_embeddings=[query_embedding],
            n_results=k,
            where=where_filter,
        )
        
        # Convert results back to (Document, score) tuples
        docs_with_scores = []
        if results and results.get("documents"):
            for i, doc_id_result in enumerate(results["ids"][0]):
                content = results["documents"][0][i]
                metadata = results["metadatas"][0][i] if results.get("metadatas") else {}
                distance = results["distances"][0][i] if results.get("distances") else 0.0
                # Convert distance to relevance score (Chroma uses cosine distance, convert to similarity)
                score = 1 - distance
                
                doc = Document(page_content=content, metadata=metadata)
                docs_with_scores.append((doc, score))
        
        logger.debug(f"Retrieved {len(docs_with_scores)} documents for query, doc_id={doc_id}")
        return docs_with_scores

    def delete_document(self, doc_id: str) -> None:
        self._ensure_initialized()
        self._store._collection.delete(where={"doc_id": doc_id})
        logger.info(f"Deleted document {doc_id} from vector store")

    def as_retriever(self, doc_id: Optional[str] = None, k: int = 5) -> BaseRetriever:
        self._ensure_initialized()
        search_kwargs: dict = {"k": k}
        if doc_id:
            search_kwargs["filter"] = {"doc_id": doc_id}
        return self._store.as_retriever(search_kwargs=search_kwargs)


vector_store_manager = VectorStoreManager()
