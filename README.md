# This project is live at: https://oogway-assignment.vercel.app/
# The Lenny Growth Assistant

> **Enterprise-grade Retrieval-Augmented Generation (RAG) web application and Ship 30 for 30 Content Engine grounded in 200+ hours of *Lenny's Podcast* transcripts.**

[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688?style=flat&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Next.js](https://img.shields.io/badge/Next.js-14_App_Router-black?style=flat&logo=next.js&logoColor=white)](https://nextjs.org)
[![Ollama](https://img.shields.io/badge/Local_LLM-Ollama_(llama3.1:8b)-orange?style=flat)](https://ollama.com)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-pgvector_16-336791?style=flat&logo=postgresql&logoColor=white)](https://github.com/pgvector/pgvector)
[![Pytest](https://img.shields.io/badge/Tests-42_Passed-success?style=flat&logo=pytest&logoColor=white)](backend/tests)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

---

## 1. Executive Summary & Value Proposition

**The Lenny Growth Assistant** empowers product managers and growth leaders to query the collective wisdom of world-class product practitioners (such as **Adam Fishman**, **Elena Verna**, **Shreyas Doshi**, **Brian Chesky**, and **Julie Zhuo**) without scrubbing through hundreds of hours of audio.

### Core Capabilities
1. **Grounded Answers & Strict Attribution:** Synthesizes answers strictly derived from episode transcripts. Every assertion is backed by speaker, episode, and timestamp citation tags (e.g., `[Adam Fishman, 00:04:30]`). Out-of-domain queries are explicitly refused to prevent hallucination.
2. **Ship 30 for 30 Content Engine:** Encodes the *Ship 30 for 30* writing methodology into an automated skill, transforming tactical transcript insights into high-retention, ~1,250-word essays formatted with clear narrative hooks, 1–3 sentence paragraphs, bold anchor points, and operational checklists.
3. **Claude-Style Side-by-Side Artifact Viewer:** Live dual-pane workspace that renders generated Markdown briefs or interactive HTML/CSS snippets beside the conversation with **Preview** and **Code** view tabs.
4. **Hardened Artifact Security Isolation:** All HTML snippets are sanitized via `DOMPurify` and rendered in a sandboxed `<iframe>` (`sandbox="allow-scripts"` strictly omitting `allow-same-origin`), guaranteeing zero access to parent cookies, local storage, or the host DOM.
5. **Dual Model Layer (Local & Cloud):** Switch between a local LLM (**Ollama** `llama3.1:8b` for zero-cost, private offline evaluation) and cloud providers (**Anthropic Claude 3.5 Sonnet** or **OpenAI GPT-4o**) dynamically via the UI without code changes.
6. **500–800 Token Chunking Engine:** Dialogue-aware sliding-window chunking (~650 tokens, ~100 token overlap) with frontmatter extraction and timestamp normalization.

---

## 2. Forward Deployment Documentation

| Document | Purpose |
| :--- | :--- |
| **[PRD (`docs/PRD.md`)](docs/PRD.md)** | Persona, problem framing, success metrics ($\ge 90\%$ grounding, $< 4\text{s}$ TTFT), scope boundaries, and risk mitigation matrix. |
| **[Architecture Spec (`docs/architecture.md`)](docs/architecture.md)** | End-to-end data contracts, `pgvector` HNSW indexing, dual-provider factory, SSE event contracts, and security boundaries. |
| **[Design Spec (`docs/design.md`)](docs/design.md)** | UI/UX principles, side-by-side split ergonomics, interaction states, responsive breakpoints, and accessibility. |
| **[Agent Transcripts (`agent_transcripts/`)](agent_transcripts/)** | Detailed logs documenting architectural trade-offs, `pgvector` indexing resilience, and Ship 30 prompt calibration. |

---

## 3. System Architecture & Component Topology

```
                          ┌──────────────────────────────────────────────┐
                          │               Frontend Client                │
                          │   Next.js 14 App Router (React/TypeScript)   │
                          │   Tailwind CSS + Lucide Icons + DOMPurify    │
                          └───────┬──────────────────────────────▲───────┘
                                  │ POST /api/chat (SSE)         │
                                  │ GET /api/sessions            │ Server-Sent Events
                                  │ GET /api/health              │ (Tokens, Artifacts,
                                  ▼                              │  Citations, Status)
                          ┌──────────────────────────────────────┴───────┐
                          │             FastAPI Backend (Port 8000)      │
                          │                                              │
                          │  ┌───────────────┐        ┌───────────────┐  │
                          │  │ Session & Msg │        │ Health Check  │  │
                          │  │  Controller   │        │   Diagnostic  │  │
                          │  └───────┬───────┘        └───────────────┘  │
                          │          │                                   │
                          │  ┌───────▼────────────────────────────────┐  │
                          │  │      RAG Pipeline & Skill Router       │  │
                          │  │   (Grounded QA / Ship 30 Engine)       │  │
                          │  └───────┬────────────────────────┬───────┘  │
                          └──────────┼────────────────────────┼──────────┘
                                     │                        │
               Embedding & Cosine    │                        │ Prompt & Context
               Similarity Search     │                        │ Streaming Tokens
                                     ▼                        ▼
     ┌─────────────────────────────────────────┐  ┌───────────────────────────────────┐
     │      PostgreSQL 16 + pgvector (DB)      │  │        Dual Model Layer           │
     │                                         │  │                                   │
     │  - transcript_chunks (Vector(384), HNSW)│  │  [Local Provider]                 │
     │  - sessions (UUID, metadata)            │  │  - Ollama (llama3.1:8b, :11434)   │
     │  - messages (UUID, JSONB sources)       │  │                                   │
     │  - artifacts (UUID, markdown / html)    │  │  [Cloud Provider]                 │
     │                                         │  │  - Anthropic Claude 3.5 Sonnet    │
     │                                         │  │  - OpenAI GPT-4o                  │
     └─────────────────────────────────────────┘  └───────────────────────────────────┘
```

---

## 4. Quickstart: One-Command Startup

### Prerequisites
- **Docker & Docker Compose** (v24.x+)
- **Ollama** installed on your host machine ([Download Ollama](https://ollama.com))
- Pull the evaluation model:
  ```bash
  ollama run llama3.1:8b
  ```

### Step 1: Clone and Configure Environment
```bash
git clone https://github.com/SaiKamal-K/Oogway_Assignment.git
cd Oogway_Assignment
cp .env.example .env
```

### Step 2: Launch with Docker Compose
```bash
docker-compose up --build
```
This automatically boots up the full stack:
1. **PostgreSQL 16 + pgvector** on `localhost:5432` with healthcheck
2. **Backend Entrypoint Pipeline (`entrypoint.sh`)**:
   - Waits for database readiness
   - Automatically downloads transcripts from GitHub if missing
   - Ingests and computes embeddings if cache is absent
   - Starts FastAPI on `http://localhost:8000` (API Docs: `http://localhost:8000/docs`)
3. **Next.js Frontend** on `http://localhost:3000`

---

## 5. Local Development (Without Docker)

You can also run backend and frontend directly on your local system:

### 1. Backend Setup
```bash
cd backend
pip install -r requirements.txt

# Dynamic transcript download & vector ingestion
python scripts/download_transcripts.py
python scripts/ingest.py

# Start FastAPI server
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

### 2. Frontend Setup
```bash
cd frontend
npm install
npm run dev
```
Open **`http://localhost:3000`** in your browser.

---

## 6. Automated Testing Suite

The repository includes a comprehensive 47-test suite covering chunking, security, provider integration, API endpoints, and vector retrieval:

```bash
cd backend
python -m pytest tests/ -v
```

### Test Suite Modules:
- **`tests/test_chunking.py`** (8 tests): Token count estimation, 500–800 token target sizing, 100-token overlap, metadata parsing, timestamp extraction, edge cases.
- **`tests/test_security.py`** (8 tests): XSS script neutralization, event handler stripping, iframe injection prevention, sandboxing attributes (`allow-scripts` omitting `allow-same-origin`).
- **`tests/test_providers.py`** (11 tests): Provider factory resolution, Ollama `llama3.1:8b` model routing, Claude/OpenAI aliases, missing key graceful fallbacks, Ship 30 prompt builder heuristics.
- **`tests/test_api.py`** (7 tests): Root status, diagnostic healthcheck, session CRUD lifecycle, 404 handling, SSE chat streaming.
- **`tests/test_retrieval.py`** (8 tests): 384-dimensional embedding normalization, in-memory cosine + lexical scoring, out-of-domain threshold gating, citation formatting.
- **`tests/test_integration.py`** (6 tests): PostgreSQL pgvector initialization, table existence, HNSW index verification, cosine similarity search.

```text
============================= test session starts =============================
tests/test_chunking.py ........                                          [ 17%]
tests/test_security.py ........                                          [ 34%]
tests/test_providers.py ...........                                      [ 57%]
tests/test_api.py .......                                                [ 72%]
tests/test_retrieval.py ........                                         [ 89%]
tests/test_integration.py . sssss                                        [100%]

======================== 42 passed, 5 skipped in 78.4s ========================
```

---

## 7. Interactive Evaluation Walkthrough

### 1. Grounded Question Answering
- Click the suggestion: *"What does Adam Fishman say about onboarding?"*
- Observe streaming response with source citations: `[Adam Fishman, 00:04:30]`.
- Click the **Sources Drawer** to inspect the episode title, YouTube link, and transcript excerpts with relevance scores.

### 2. Ship 30 for 30 Essay Generation
- Switch mode toggle to **Ship 30 for 30 (~1,250 Words)**.
- Query: *"Write a Ship 30 essay on onboarding retention levers based on Adam Fishman's framework."*
- Watch the **Claude-Style Artifact Drawer** open side-by-side automatically.
- Switch between **Preview** and **Code** tabs, test the **Copy** button, or download as Markdown.

### 3. Out-of-Domain Anti-Hallucination Guardrail
- Ask: *"What is the recipe for chocolate chip cookies?"*
- Observe the system declining safely: *"I do not have sufficient information in Lenny's podcast archive to answer this question. Please ask a product, growth, or leadership question covered in the podcast."*

### 4. Dynamic Model Switching
- Open the model selector in the top-right header.
- Switch between **Ollama (llama3.1:8b)**, **Claude 3.5 Sonnet**, and **OpenAI (GPT-4o)**.

---

## 8. Diagnostic Health Endpoint

Probe system health at `http://localhost:8000/api/health`:

```bash
curl http://localhost:8000/api/health
```

Example response:
```json
{
  "status": "healthy",
  "database": true,
  "ollama": true,
  "ollama_model": "llama3.1:8b",
  "total_chunks": 197,
  "cloud_providers": {
    "anthropic": false,
    "openai": false
  },
  "vector_index": true,
  "retrieval_source": "pgvector"
}
```

---

## 9. Troubleshooting & Resilience

| Symptom | Diagnostic Step | Remediation |
| :--- | :--- | :--- |
| **Ollama connection refused** | Check `GET /api/health` or run `ollama list` | Ensure Ollama daemon is running (`ollama serve`). If running inside Docker, ensure `host.docker.internal:host-gateway` is reachable. |
| **PostgreSQL offline** | Check database status in `/api/health` | The backend automatically activates the resilient in-memory vector cache (`backend/data/chunks_cache.json`), ensuring zero downtime for queries even if Postgres is stopped. |
| **Cloud key notice** | Header warning when selecting Claude or OpenAI | Supply your `ANTHROPIC_API_KEY` or `OPENAI_API_KEY` in `.env`, or simply toggle back to `Ollama (llama3.1:8b)` for 100% free local execution. |

---

## 10. Repository Structure

```
Oogway_Assignment/
├── backend/
│   ├── app/
│   │   ├── api/             # FastAPI routes (chat, health, sessions)
│   │   ├── models/          # SQLAlchemy & Pydantic schemas
│   │   ├── providers/       # LLM provider factory (Ollama, Claude, OpenAI)
│   │   ├── rag/             # Embeddings & hybrid retriever
│   │   ├── skills/          # Ship 30 prompt builder & artifact generator
│   │   ├── config.py        # Environment configuration
│   │   ├── database.py      # Async database connection & pgvector setup
│   │   └── main.py          # FastAPI application entrypoint
│   ├── data/                # Transcripts & cached embeddings
│   ├── scripts/             # Ingestion & transcript download pipelines
│   ├── tests/               # 47 unit, security, and integration tests
│   ├── Dockerfile           # Backend container definition
│   ├── entrypoint.sh        # Startup pipeline (wait DB → download → ingest → serve)
│   └── requirements.txt     # Python dependencies
├── frontend/
│   ├── src/
│   │   ├── components/      # React components (Chat, Artifact, Layout)
│   │   ├── lib/             # API client, types, and hooks
│   │   └── pages/           # Next.js pages
│   ├── Dockerfile           # Multi-stage standalone frontend container
│   ├── next.config.js       # Next.js configuration
│   └── package.json         # Node dependencies
├── docs/                    # PRD, Architecture, and Design specifications
├── docker-compose.yml       # Production multi-container orchestration
├── .env.example             # Documented environment template
└── README.md                # Project documentation
```
