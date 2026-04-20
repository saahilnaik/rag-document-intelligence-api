import logging
from pathlib import Path
from uuid import UUID, uuid4

from fastapi import APIRouter, BackgroundTasks, HTTPException, UploadFile

from api.schemas import DocumentStatus, UploadResponse
from core.config import get_settings
from services.document_processor import chunk_documents, extract_text
from services.document_registry import document_registry
from services.vector_store import vector_store_manager

router = APIRouter()
logger = logging.getLogger(__name__)


def _ingest_document(doc_id: UUID, file_path: Path, file_type: str, filename: str) -> None:
    try:
        docs = extract_text(str(file_path), file_type)
        chunks = chunk_documents(docs, str(doc_id), filename)
        vector_store_manager.store_chunks(chunks)
        document_registry.mark_ready(doc_id, len(chunks))
    except Exception as exc:
        logger.error("Ingestion failed for %s: %s", doc_id, exc)
        document_registry.mark_failed(doc_id, str(exc))


@router.post("/upload", response_model=UploadResponse, status_code=202)
async def upload_document(file: UploadFile, background_tasks: BackgroundTasks) -> UploadResponse:
    settings = get_settings()

    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in settings.ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=415,
            detail=f"File type {suffix!r} not supported. Allowed: {sorted(settings.ALLOWED_EXTENSIONS)}",
        )

    contents = await file.read()
    if len(contents) > settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024:
        raise HTTPException(
            status_code=413,
            detail=f"File exceeds {settings.MAX_UPLOAD_SIZE_MB} MB limit.",
        )

    doc_id = uuid4()
    upload_dir = Path(settings.UPLOAD_DIR)
    upload_dir.mkdir(parents=True, exist_ok=True)
    file_path = upload_dir / f"{doc_id}{suffix}"
    file_path.write_bytes(contents)

    document_registry.register(doc_id, file.filename or "unknown")
    background_tasks.add_task(_ingest_document, doc_id, file_path, suffix, file.filename or "unknown")

    return UploadResponse(doc_id=doc_id, filename=file.filename or "unknown")


@router.get("/documents", response_model=list[DocumentStatus])
async def list_documents() -> list[DocumentStatus]:
    return document_registry.list_all()


@router.get("/documents/{doc_id}", response_model=DocumentStatus)
async def get_document(doc_id: UUID) -> DocumentStatus:
    entry = document_registry.get(doc_id)
    if not entry:
        raise HTTPException(status_code=404, detail=f"Document {doc_id} not found.")
    return entry


@router.delete("/documents/{doc_id}", status_code=204)
async def delete_document(doc_id: UUID) -> None:
    entry = document_registry.get(doc_id)
    if not entry:
        raise HTTPException(status_code=404, detail=f"Document {doc_id} not found.")
    vector_store_manager.delete_document(str(doc_id))
    document_registry.delete(doc_id)
