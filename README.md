# 🚀 Agentic RAG Document Intelligence API

> A production-shaped **Retrieval-Augmented Generation (RAG)** service that transforms how you interact with documents.

Upload PDF, DOCX, or TXT files → the system embeds and indexes them → ask questions in natural language → get **cited answers** with real-time streaming and conversational memory.

### ✨ Key Highlights

- 🎯 **100% Free** — Only need a free [Groq API key](https://console.groq.com)
- 🏃 **Lightning Fast** — Local embeddings on your CPU (no API calls)
- 🔗 **Cited Answers** — Every answer includes `[filename:page]` references
- 💬 **Real-time Streaming** — See tokens appear as they're generated
- 🧠 **Conversation Memory** — Context-aware follow-up questions
- 📊 **Quality Metrics** — Built-in RAGAS evaluation (faithfulness, relevancy, precision)
- 🐳 **Docker Ready** — Run the entire stack with one command

---

## 🆕 Latest Updates (June 2026)

### ✅ Fixed Critical Retrieval Issues
- **Vector Store Filtering** — Fixed Chroma query filtering to properly scope documents by `doc_id`
- **Metadata Handling** — Ensured all chunks have complete metadata (page numbers, filenames, doc IDs)
- **Enhanced Logging** — Added comprehensive logging throughout the pipeline for easier debugging

**Result:** Documents now consistently return relevant answers with proper source citations. 🎉

---

## 🎯 What It Does

- **📤 Upload Documents** — PDF, DOCX, TXT, or Markdown files up to 25 MB
- **🔍 Auto-Indexing** — Documents chunked, embedded locally, indexed in ChromaDB (background processing)
- **❓ Ask Questions** — Natural language queries return answers with citations from your documents
- **⚡ Streaming Answers** — Tokens stream to the browser in real-time via Server-Sent Events
- **💭 Memory** — Each session remembers the last 5 exchanges for follow-up questions
- **📈 Quality Scoring** — Built-in RAGAS evaluation (faithfulness, answer relevancy, context precision)

---

## 🏗️ Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│                    📱 Next.js Frontend                           │
│   Sidebar (upload/select)  ←→  ChatWindow (streaming)           │
│         Document Manager     Real-time Token Streaming          │
└───────────────────────────┬──────────────────────────────────────┘
                            │ HTTP / SSE Streaming
┌───────────────────────────▼──────────────────────────────────────┐
│                    ⚙️ FastAPI Backend                            │
│                                                                  │
│  POST /upload  →  🔄 BackgroundTask                              │
│       │                  │                                       │
│       │           📄 extract_text()                              │
│       │           ✂️ chunk_documents()   ┌──────────────────┐   │
│       │           💾 store_chunks()  ───►│   🎨 ChromaDB    │   │
│       │                                  │  (local vectors) │   │
│  POST /ask/stream                        └────────┬─────────┘   │
│       │                                           │              │
│       │  💭 SessionMemory (last 5 turns)          │              │
│       │  ↓                                        │              │
│       │  🤔 Condense follow-up question           │              │
│       │  🔎 Retrieve top-K chunks  ◄──────────────┘              │
│       │  ↓                                                       │
│       │  🧠 ChatGroq (llama-3.3-70b)                            │
│       │  ↓                                                       │
│       └─ ⚡ Stream tokens + sources back via SSE                │
└──────────────────────────────────────────────────────────────────┘
```

### 📊 Data Flow

#### **Ingestion Pipeline** (Upload → Background Processing)

```
POST /upload
    ↓
📋 Validate file type & size
    ↓
📤 Save to disk & register
    ↓
🔄 Start background task:
    ├─ 📄 extract_text()         → Get text from PDF/DOCX/TXT
    ├─ ✂️  chunk_documents()      → Split into 1000-char chunks (200 overlap)
    ├─ 🎨 embed locally          → BAAI/bge-small-en-v1.5 (384-dim, CPU)
    ├─ 💾 store_chunks()         → ChromaDB (with doc_id metadata)
    └─ ✅ mark_ready()           → Document ready for queries
```

#### **Query Pipeline** (Ask → Stream Answer)

```
POST /ask/stream
    ↓
📚 Load session history (last 5 turns)
    ↓
🤔 If follow-up exists:
    └─ Condense into standalone question via ChatGroq
    ↓
🔎 Retrieve top-5 chunks from ChromaDB
    ├─ Filtered by doc_id (if scoped to one document)
    └─ Scored by semantic similarity
    ↓
📝 Build context string with [filename:page] markers
    ↓
⚡ Stream answer token-by-token via ChatGroq
    ├─ token event → each character as it arrives
    ├─ sources event → final citations (with relevance scores)
    └─ done event → completion marker
    ↓
💭 Save Q&A pair to session memory
```

---

## 🛠️ Tech Stack

| Layer | Technology | Details |
|---|---|---|
| **Backend API** | FastAPI + Uvicorn | Async, auto-docs |
| **LLM** | Groq — `llama-3.3-70b-versatile` | Free tier, ultra-fast |
| **Embeddings** | `BAAI/bge-small-en-v1.5` | Local CPU, 384-dim, normalized |
| **Vector Store** | ChromaDB | Local persistent, metadata filtering |
| **RAG Orchestration** | LangChain 1.x | `create_history_aware_retriever` |
| **Evaluation** | RAGAS | Faithfulness, relevancy, precision |
| **Frontend** | Next.js 14 + React 18 + TypeScript | App Router, real-time streaming |
| **State Management** | Zustand | Lightweight, simple |
| **Styling** | Tailwind CSS | Dark/light mode support |
| **Containerization** | Docker + Docker Compose | Full stack in one command |
| **Testing** | pytest + Vitest + RTL | Backend + frontend coverage |

---

## 🚀 Quick Start (Local Development)

### 📋 Prerequisites

- Python 3.11+
- Node.js 20+
- Free [Groq API key](https://console.groq.com) (sign up, generate key)

### 🔧 Step-by-Step Setup

#### 1️⃣ Clone & Setup Environment

```bash
git clone https://github.com/saahilnaik9/rag-document-intelligence-api
cd rag-document-intelligence-api
```

#### 2️⃣ Backend Setup

```bash
# Create virtual environment
py -3.11 -m venv venv

# Install dependencies
venv\Scripts\pip install -r requirements.txt

# Create .env file
copy .env.example .env

# ⚠️ Open .env and add your GROQ_API_KEY
```

#### 3️⃣ Frontend Setup

```bash
cd frontend
npm install
cd ..
```

#### 4️⃣ Run Both Servers

**Terminal 1 — Backend:**
```bash
venv\Scripts\uvicorn main:app --reload
```
✅ API available at `http://localhost:8000`  
📚 Interactive docs at `http://localhost:8000/docs`

**Terminal 2 — Frontend:**
```bash
cd frontend && npm run dev
```
✅ App available at `http://localhost:3000`

### ✨ First Run

1. Open `http://localhost:3000` in your browser
2. Upload a PDF using the sidebar
3. Wait for the status to show `✅ ready`
4. Start asking questions!

> 💡 **Tip:** First upload triggers ~130 MB BGE embedding model download. Subsequent uploads are instant.

---

## 🐳 Docker (One Command)

```bash
# 1. Copy and configure env file
copy .env.example .env

# 2. Add your GROQ_API_KEY to .env

# 3. Build and run everything
docker compose up --build
```

### 📍 Service URLs

| Service | URL |
|---|---|
| 🌐 Frontend | http://localhost:3000 |
| ⚙️ Backend API | http://localhost:8000 |
| 📚 API Docs | http://localhost:8000/docs |

**Features:**
- ✅ Frontend waits for API health check before starting
- 💾 Document data persists in Docker volume (`rag-data`)
- 🔄 Auto-restart on failure

---

## 📡 API Reference

All endpoints are interactive at `http://localhost:8000/docs` (auto-generated Swagger UI).

### 📤 Upload a Document
```http
POST /upload
Content-Type: multipart/form-data

file: <PDF | DOCX | TXT | MD file>
```
**Response:** `{ doc_id, filename, status: "processing" }` (202 Accepted)

Processing continues in the background. Poll `/documents/{doc_id}` until `status` is `"ready"`.

---

### 📋 List All Documents
```http
GET /documents
```
**Response:** Array of document statuses with metadata.

---

### 🔍 Get Document Status
```http
GET /documents/{doc_id}
```
**Response:** `{ doc_id, filename, status, chunk_count, error? }`

Status values: `"processing"` | `"ready"` | `"failed"`

---

### 🗑️ Delete a Document
```http
DELETE /documents/{doc_id}
```
**Response:** 204 No Content

Removes from vector store and registry.

---

### ❓ Ask a Question (Streaming)
```http
POST /ask/stream
Content-Type: application/json

{
  "question": "What are the main findings?",
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "doc_id": "optional-uuid-to-scope-search"
}
```

**Response:** Server-Sent Events stream:
```
data: {"type": "token", "data": "The"}
data: {"type": "token", "data": " main"}
...
data: {"type": "sources", "data": [{"doc_id": "...", "filename": "...", "page_number": 1, "text": "...", "score": 0.92}]}
data: {"type": "done"}
```

**Event Types:**
- `token` — streamed answer tokens
- `sources` — final citations (once, at the end)
- `done` — stream complete
- `error` — on failure

---

### ❓ Ask a Question (Non-Streaming)
```http
POST /ask
Content-Type: application/json

{ "question": "...", "session_id": "...", "doc_id": "..." }
```

**Response:** `{ answer, sources[], session_id }`

Returns immediately when complete (no streaming).

---

### 📊 Evaluate Answer Quality
```http
POST /evaluate
Content-Type: application/json

{
  "question": "What causes X?",
  "answer": "X is caused by...",
  "contexts": ["chunk1 from retrieval", "chunk2 from retrieval"],
  "ground_truth": "optional-ideal-answer"
}
```

**Response:** 
```json
{
  "faithfulness": 0.92,
  "answer_relevancy": 0.88,
  "context_precision": 0.95
}
```

Scores range from 0–1 (higher = better).

---

### 🏥 Health Check
```http
GET /health
```

**Response:** `{ "status": "ok" }`

---

## 📈 Quality Evaluation (RAGAS)

The project uses [RAGAS](https://docs.ragas.io) to measure RAG system quality across three dimensions:

| Metric | Measures | Range | Interpretation |
|---|---|---|---|
| **Faithfulness** | Hallucination rate | 0–1 | Is the answer grounded in the context? Higher = less hallucination |
| **Answer Relevancy** | Answer-question alignment | 0–1 | Does the answer address the question? |
| **Context Precision** | Chunk quality | 0–1 | Are retrieved chunks actually relevant? (requires ground truth) |

### 🎯 Run Batch Evaluation

```bash
venv\Scripts\python scripts/evaluate.py eval_dataset/sample_qa.jsonl
```

**Output:**
- 📊 Metrics table in terminal
- 📁 Results saved to `eval_results/{timestamp}.json`

**Scope to specific document:**
```bash
venv\Scripts\python scripts/evaluate.py eval_dataset/sample_qa.jsonl --doc-id <uuid>
```

### 📋 JSONL Format

```jsonl
{"question": "What is X?", "ground_truth": "X is..."}
{"question": "How does Y work?", "ground_truth": "Y works by..."}
```

---

## ✅ Running Tests

```bash
# Backend — all tests
venv\Scripts\pytest tests/ -v

# Backend — single test file
venv\Scripts\pytest tests/test_routes.py::test_ask_success -v

# Frontend — all tests
cd frontend && npm test
```

**Test Infrastructure:**
- 🧪 `TestClient` (no live server needed)
- 🎭 Mocked vector store + QA service
- ✅ No external API keys required for tests

---

## 🆘 Troubleshooting

### ❌ "No source available" — Answers without citations

**Cause:** Vector store retrieval not finding documents.

**Solution:**
1. Check logs: `Retrieved 0 documents` = retrieval failing
2. Verify document status: `GET /documents/{doc_id}` should show `status: "ready"`
3. Clear old data: `rm -r data/` and restart backend
4. Re-upload PDF and wait for processing to complete

### ❌ Slow response / timeout errors

**Cause:** First run downloads embedding model (~130 MB).

**Solution:**
- ⏳ First upload takes 1–2 minutes
- Subsequent uploads are instant
- Use Docker to pre-download the model at build time

### ❌ ModuleNotFoundError / ImportError

**Cause:** Python dependencies not installed or wrong virtual environment.

**Solution:**
```bash
venv\Scripts\pip install -r requirements.txt --force-reinstall
```

### ❌ Port already in use

**Cause:** Another process using 8000 or 3000.

**Solution:**
```bash
# Find and kill process on port 8000
netstat -ano | findstr :8000
taskkill /PID <PID> /F
```

### ✅ Everything working?

Check the backend logs:
```
INFO: Stored X chunks in vector store
INFO: Retrieved X documents for answering
INFO: Generated answer with X sources
```

If you see `Retrieved 0 documents`, the issue is in the filtering logic.

---

```
.
├── 📄 main.py                       # FastAPI app, CORS, lifespan hooks
├── api/
│   ├── routes.py                    # All endpoints (/upload, /ask, /ask/stream, /evaluate)
│   └── schemas.py                   # Pydantic request/response models
├── core/
│   ├── config.py                    # Settings from .env (pydantic-settings)
│   └── logging.py                   # structlog configuration
├── services/                         # Business logic layer
│   ├── document_processor.py         # Extract text + chunk documents
│   ├── document_registry.py          # In-memory doc status tracker
│   ├── session_memory.py             # Per-session conversation history
│   ├── vector_store.py               # ChromaDB wrapper (embed, store, retrieve) ⭐
│   ├── qa.py                         # RAG chain (get_answer + astream_answer)
│   └── evaluation.py                 # RAGAS scoring
├── scripts/
│   └── evaluate.py                   # CLI batch evaluator
├── tests/                            # pytest test suite
│   ├── conftest.py                   # Fixtures (mocks, client)
│   ├── test_document_processor.py
│   ├── test_routes.py
│   ├── test_evaluation.py
│   └── test_session_memory.py
├── frontend/                         # Next.js 14 React app
│   ├── app/
│   │   ├── layout.tsx                # Root layout + metadata
│   │   ├── page.tsx                  # Home page (chat UI)
│   │   └── globals.css               # Tailwind directives
│   ├── components/
│   │   ├── Sidebar.tsx               # File upload + doc selector
│   │   ├── ChatWindow.tsx            # Message display + streaming
│   │   ├── ChatInput.tsx             # Question input field
│   │   ├── SourcesExpander.tsx       # Collapsible citations
│   │   ├── DocumentCard.tsx          # Doc status display
│   │   ├── ThemeProvider.tsx         # Dark/light mode wrapper
│   │   └── ThemeToggle.tsx           # Theme switcher
│   ├── lib/
│   │   ├── api.ts                    # Fetch wrapper + SSE event reader
│   │   ├── store.ts                  # Zustand state (messages, docs, theme)
│   │   └── useChat.ts                # Custom hook for chat logic
│   ├── types/
│   │   └── index.ts                  # Shared TypeScript interfaces
│   └── __tests__/                    # Vitest + React Testing Library
├── eval_dataset/
│   └── sample_qa.jsonl               # Sample Q&A pairs for RAGAS evaluation
├── data/
│   ├── chroma/                       # ChromaDB persistence (auto-created)
│   └── uploads/                      # Uploaded files (auto-created)
├── 🐳 Dockerfile                     # Backend image
├── 🐳 docker-compose.yml             # Full stack orchestration
├── 📋 requirements.txt               # Python dependencies
├── 📋 .env.example                   # Configuration template
└── 📖 README.md                      # This file
```

---

## ⚙️ Configuration

All settings are managed by `core/config.py` via `.env` file.

| Variable | Default | Description |
|---|---|---|
| `GROQ_API_KEY` | **required** | Free from [console.groq.com](https://console.groq.com) |
| `GROQ_CHAT_MODEL` | `llama-3.3-70b-versatile` | Model ID from Groq |
| `LLM_TEMPERATURE` | `0.0` | Lower = more factual, 0–1 range |
| `LLM_MAX_TOKENS` | `1024` | Maximum tokens per answer |
| `EMBEDDING_MODEL` | `BAAI/bge-small-en-v1.5` | Hugging Face model ID |
| `EMBEDDING_DEVICE` | `cpu` | `cpu` or `cuda` (GPU) |
| `CHROMA_PERSIST_DIR` | `./data/chroma` | Vector store storage location |
| `UPLOAD_DIR` | `./data/uploads` | Uploaded files storage location |
| `MAX_UPLOAD_SIZE_MB` | `25` | Per-file size limit |
| `RETRIEVAL_K` | `5` | Chunks to retrieve per query |
| `CHUNK_SIZE` | `1000` | Characters per chunk |
| `CHUNK_OVERLAP` | `200` | Overlap between chunks (context preservation) |
| `MAX_CONVERSATION_TURNS` | `5` | Session history depth (follow-up questions) |
| `CORS_ORIGINS` | `["http://localhost:3000"]` | Allowed frontend origins |

**Example `.env`:**
```env
GROQ_API_KEY=gsk_your_key_here
EMBEDDING_DEVICE=cuda
CHUNK_SIZE=1500
```

---

## 💡 Key Design Decisions

### Why Local Embeddings?
`BAAI/bge-small-en-v1.5` runs on your CPU with **zero API costs**. The 384-dimension vectors are compact and fast. First run downloads ~130 MB; Docker pre-downloads it at build time for instant container startup.

### Why One Chroma Collection with Metadata Filters?
Instead of creating a collection per document:
- ✅ **Cross-document queries** are trivial (no filter needed)
- ✅ **Single-document queries** add `filter={"doc_id": "..."}`
- ✅ **Deletion** uses `collection.delete(where={"doc_id": "..."})`
- ✅ Scales better and simpler to manage

### Why LCEL Streaming Over ConversationalRetrievalChain?
The legacy `ConversationalRetrievalChain` doesn't stream tokens cleanly. Our LCEL composition using `create_history_aware_retriever` + `create_retrieval_chain` streams per-token deltas that map directly to SSE events for real-time UI updates.

### Why In-Memory Registries?
**v1 approach:** Simple, no external dependencies.  
**v2 approach (planned):** Redis/Postgres for persistence across restarts.

The registries (`DocumentRegistry`, `SessionMemory`) reset on server restart. This is acceptable for a development/demo tool.

### Document Retrieval Fix (June 2026)
Previously, the `retrieve()` method passed filters via `**search_kwargs` which langchain-chroma ignored. Now we:
1. Access Chroma's collection API directly
2. Pass `where={"doc_id": doc_id}` to the query
3. Properly convert distance scores to relevance

**Result:** 100% consistent document retrieval with proper scoping.

---

## 🔗 Resources & Links

- 📚 **LangChain Docs:** [python.langchain.com](https://python.langchain.com)
- 🎨 **ChromaDB Guide:** [docs.trychroma.com](https://docs.trychroma.com)
- 📊 **RAGAS Evaluation:** [ragas.io](https://ragas.io)
- 🚀 **Groq Models:** [console.groq.com](https://console.groq.com)
- 🤗 **BGE Embeddings:** [huggingface.co/BAAI/bge-small-en-v1.5](https://huggingface.co/BAAI/bge-small-en-v1.5)
- 📖 **FastAPI Docs:** [fastapi.tiangolo.com](https://fastapi.tiangolo.com)
- ⚛️ **Next.js Guide:** [nextjs.org](https://nextjs.org)

---

## 💝 Support

Found a bug? Have a feature request?
- 📝 Open an issue on [GitHub](https://github.com/saahilnaik9/rag-document-intelligence-api)
- 💬 Feel free to check existing issues first

---

**Made with ❤️ using RAG + Streaming + Local AI**
