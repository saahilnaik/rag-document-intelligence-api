from datetime import datetime
from typing import Literal, Optional
from uuid import UUID

from pydantic import BaseModel


class UploadResponse(BaseModel):
    doc_id: UUID
    filename: str
    status: Literal["processing"] = "processing"


class DocumentStatus(BaseModel):
    doc_id: UUID
    filename: str
    status: Literal["processing", "ready", "failed"]
    error: Optional[str] = None
    created_at: datetime
    chunk_count: Optional[int] = None


class AskRequest(BaseModel):
    question: str
    session_id: UUID
    doc_id: Optional[UUID] = None


class SourceChunk(BaseModel):
    doc_id: str
    filename: str
    page_number: Optional[int] = None
    text: str
    score: float


class AnswerResponse(BaseModel):
    answer: str
    sources: list[SourceChunk]
    session_id: UUID


class EvaluateRequest(BaseModel):
    question: str
    answer: str
    contexts: list[str]
    ground_truth: Optional[str] = None


class EvaluateResponse(BaseModel):
    faithfulness: Optional[float] = None
    answer_relevancy: Optional[float] = None
    context_precision: Optional[float] = None
