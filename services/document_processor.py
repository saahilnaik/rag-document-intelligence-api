from pathlib import Path

from langchain_community.document_loaders import Docx2txtLoader, PyPDFLoader, TextLoader
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

from core.config import get_settings


def extract_text(path: str, file_type: str) -> list[Document]:
    if file_type == ".pdf":
        loader = PyPDFLoader(path)
    elif file_type == ".docx":
        loader = Docx2txtLoader(path)
    elif file_type in {".txt", ".md"}:
        loader = TextLoader(path, encoding="utf-8")
    else:
        raise ValueError(f"Unsupported file type: {file_type}")
    return loader.load()


def chunk_documents(docs: list[Document], doc_id: str, filename: str) -> list[Document]:
    settings = get_settings()
    file_type = Path(filename).suffix.lower()

    for doc in docs:
        doc.metadata["doc_id"] = str(doc_id)
        doc.metadata["filename"] = filename
        doc.metadata["file_type"] = file_type
        if "page" in doc.metadata:
            doc.metadata["page_number"] = doc.metadata.pop("page") + 1

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=settings.CHUNK_SIZE,
        chunk_overlap=settings.CHUNK_OVERLAP,
    )
    return splitter.split_documents(docs)
