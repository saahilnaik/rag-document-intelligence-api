import io
from uuid import uuid4


def test_health(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_upload_valid_pdf(client):
    resp = client.post(
        "/upload",
        files={"file": ("test.pdf", io.BytesIO(b"%PDF-1.4 fake"), "application/pdf")},
    )
    assert resp.status_code == 202
    body = resp.json()
    assert body["filename"] == "test.pdf"
    assert body["status"] == "processing"
    assert "doc_id" in body


def test_upload_invalid_extension(client):
    resp = client.post(
        "/upload",
        files={"file": ("malware.exe", io.BytesIO(b"data"), "application/octet-stream")},
    )
    assert resp.status_code == 415


def test_upload_too_large(client):
    large = b"x" * (26 * 1024 * 1024)  # 26 MB > 25 MB limit
    resp = client.post(
        "/upload",
        files={"file": ("big.pdf", io.BytesIO(large), "application/pdf")},
    )
    assert resp.status_code == 413


def test_list_documents_empty(client):
    resp = client.get("/documents")
    assert resp.status_code == 200
    assert resp.json() == []


def test_list_documents_after_upload(client):
    client.post(
        "/upload",
        files={"file": ("doc.pdf", io.BytesIO(b"%PDF-1.4"), "application/pdf")},
    )
    resp = client.get("/documents")
    docs = resp.json()
    assert len(docs) == 1
    assert docs[0]["filename"] == "doc.pdf"
    assert docs[0]["status"] == "processing"  # _ingest_document is mocked, stays processing


def test_get_document_not_found(client):
    assert client.get(f"/documents/{uuid4()}").status_code == 404


def test_get_document_after_upload(client):
    upload = client.post(
        "/upload",
        files={"file": ("doc.pdf", io.BytesIO(b"%PDF-1.4"), "application/pdf")},
    )
    doc_id = upload.json()["doc_id"]
    resp = client.get(f"/documents/{doc_id}")
    assert resp.status_code == 200
    assert resp.json()["doc_id"] == doc_id


def test_delete_document_not_found(client):
    assert client.delete(f"/documents/{uuid4()}").status_code == 404


def test_delete_document_success(client):
    upload = client.post(
        "/upload",
        files={"file": ("doc.pdf", io.BytesIO(b"%PDF-1.4"), "application/pdf")},
    )
    doc_id = upload.json()["doc_id"]
    assert client.delete(f"/documents/{doc_id}").status_code == 204
    assert client.get(f"/documents/{doc_id}").status_code == 404
