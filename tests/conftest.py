import os

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

# Set dummy env vars before any app imports so Settings validation passes
os.environ.setdefault("GROQ_API_KEY", "test-groq-key")
os.environ.setdefault("CHROMA_PERSIST_DIR", "/tmp/test-chroma")
os.environ.setdefault("UPLOAD_DIR", "/tmp/test-uploads")


@pytest.fixture(autouse=True)
def _reset_registries():
    from services.document_registry import document_registry
    from services.session_memory import session_memory

    document_registry._store.clear()
    session_memory._sessions.clear()
    yield
    document_registry._store.clear()
    session_memory._sessions.clear()


@pytest.fixture
def mock_vector_store():
    mock = MagicMock()
    with (
        patch("services.vector_store.vector_store_manager", mock),
        patch("api.routes.vector_store_manager", mock),
    ):
        yield mock


@pytest.fixture
def mock_qa():
    canned = MagicMock()
    canned.answer = "Canned answer"
    canned.sources = []
    canned.session_id = "00000000-0000-0000-0000-000000000001"

    async def fake_stream(*args, **kwargs):
        yield {"type": "token", "data": "Canned "}
        yield {"type": "token", "data": "answer"}
        yield {"type": "sources", "data": []}
        yield {"type": "done"}

    with (
        patch("api.routes.get_answer", return_value=canned),
        patch("api.routes.astream_answer", side_effect=fake_stream),
    ):
        yield


@pytest.fixture
def client(mock_vector_store, mock_qa):
    from main import app
    from fastapi.testclient import TestClient

    with TestClient(app) as c:
        yield c
