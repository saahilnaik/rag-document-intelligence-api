import json
import time
from uuid import uuid4

import requests
import streamlit as st

API_URL = "http://localhost:8000"

st.set_page_config(page_title="RAG Document Intelligence", page_icon="🔍", layout="wide")

# ── Session state ─────────────────────────────────────────────────────────────
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid4())
if "messages" not in st.session_state:
    st.session_state.messages = []
if "selected_doc_id" not in st.session_state:
    st.session_state.selected_doc_id = None


# ── Helpers ───────────────────────────────────────────────────────────────────
def _status_badge(status: str) -> str:
    return {"ready": "🟢", "processing": "🟡", "failed": "🔴"}.get(status, "⚪")


def _fetch_documents() -> list[dict]:
    try:
        return requests.get(f"{API_URL}/documents", timeout=3).json()
    except Exception:
        return []


def _upload_file(file) -> dict | None:
    try:
        resp = requests.post(
            f"{API_URL}/upload",
            files={"file": (file.name, file.getvalue(), file.type or "application/octet-stream")},
            timeout=10,
        )
        resp.raise_for_status()
        return resp.json()
    except Exception as exc:
        st.sidebar.error(f"Upload failed: {exc}")
        return None


def _delete_document(doc_id: str) -> None:
    try:
        requests.delete(f"{API_URL}/documents/{doc_id}", timeout=5)
    except Exception:
        pass


# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.title("🗂 Documents")

    # File uploader
    uploaded_files = st.file_uploader(
        "Upload document(s)",
        type=["pdf", "txt", "docx", "md"],
        accept_multiple_files=True,
        label_visibility="collapsed",
    )
    if uploaded_files:
        for f in uploaded_files:
            result = _upload_file(f)
            if result:
                st.success(f"Queued: **{result['filename']}**")
        st.rerun()

    st.divider()

    # Document list
    docs = _fetch_documents()
    if not docs:
        st.caption("No documents yet. Upload one above.")
    else:
        for doc in docs:
            badge = _status_badge(doc["status"])
            col1, col2 = st.columns([5, 1])
            with col1:
                label = f"{badge} {doc['filename']}"
                if doc["status"] == "ready":
                    label += f" *({doc.get('chunk_count', '?')} chunks)*"
                st.markdown(label)
            with col2:
                if st.button("✕", key=f"del_{doc['doc_id']}", help="Delete"):
                    _delete_document(doc["doc_id"])
                    if st.session_state.selected_doc_id == doc["doc_id"]:
                        st.session_state.selected_doc_id = None
                    st.rerun()

    # Auto-refresh while any doc is still processing
    if any(d["status"] == "processing" for d in docs):
        time.sleep(2)
        st.rerun()

    st.divider()

    # Query scope selector
    ready_docs = [d for d in docs if d["status"] == "ready"]
    scope_options = {"🌐 All documents": None}
    for d in ready_docs:
        scope_options[f"📄 {d['filename']}"] = d["doc_id"]

    selected_label = st.selectbox(
        "Query scope",
        list(scope_options.keys()),
        help="Restrict retrieval to a specific document, or query across all.",
    )
    st.session_state.selected_doc_id = scope_options[selected_label]

    st.divider()
    if st.button("🗑 Clear chat history"):
        st.session_state.messages = []
        st.session_state.session_id = str(uuid4())
        st.rerun()


# ── Main chat ─────────────────────────────────────────────────────────────────
st.title("🔍 RAG Document Intelligence")
st.caption(
    f"Session `{st.session_state.session_id[:8]}…` · "
    f"Scope: **{selected_label}**"
)

# Render chat history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if msg.get("sources"):
            with st.expander(f"📎 Sources ({len(msg['sources'])})"):
                for src in msg["sources"]:
                    page = src.get("page_number") or "?"
                    st.markdown(
                        f"**{src['filename']}** — page {page} — "
                        f"score `{src['score']:.3f}`"
                    )
                    st.text(src["text"][:300])
                    st.divider()

# Chat input
if question := st.chat_input("Ask a question about your documents…"):
    # Show user message immediately
    st.session_state.messages.append({"role": "user", "content": question})
    with st.chat_message("user"):
        st.markdown(question)

    # Stream assistant response
    with st.chat_message("assistant"):
        token_placeholder = st.empty()
        full_response = ""
        sources: list[dict] = []

        payload: dict = {
            "question": question,
            "session_id": st.session_state.session_id,
        }
        if st.session_state.selected_doc_id:
            payload["doc_id"] = st.session_state.selected_doc_id

        try:
            with requests.post(
                f"{API_URL}/ask/stream",
                json=payload,
                stream=True,
                timeout=60,
            ) as resp:
                if resp.status_code != 200:
                    token_placeholder.error(
                        f"API error {resp.status_code}: {resp.text[:200]}"
                    )
                else:
                    for line in resp.iter_lines():
                        if not line:
                            continue
                        if isinstance(line, bytes):
                            line = line.decode()
                        if not line.startswith("data: "):
                            continue
                        event = json.loads(line[6:])
                        if event["type"] == "token":
                            full_response += event["data"]
                            token_placeholder.markdown(full_response + "▌")
                        elif event["type"] == "sources":
                            sources = event["data"]
                        elif event["type"] == "error":
                            token_placeholder.error(event["data"])
                            break
            token_placeholder.markdown(full_response)
        except requests.exceptions.ConnectionError:
            token_placeholder.error(
                f"Cannot reach API at `{API_URL}`. Is the server running?"
            )
        except Exception as exc:
            token_placeholder.error(f"Unexpected error: {exc}")

        if sources:
            with st.expander(f"📎 Sources ({len(sources)})"):
                for src in sources:
                    page = src.get("page_number") or "?"
                    st.markdown(
                        f"**{src['filename']}** — page {page} — "
                        f"score `{src['score']:.3f}`"
                    )
                    st.text(src["text"][:300])
                    st.divider()

    st.session_state.messages.append({
        "role": "assistant",
        "content": full_response,
        "sources": sources,
    })
