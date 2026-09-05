# System Architecture Specification
## Project: The Lenny Growth Assistant

---

## 1. System Topology Overview

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

## 2. Database Schema (`PostgreSQL + pgvector`)

### 2.1 Schema Definition
The database schema is managed via async SQLAlchemy (`asyncpg`) and leverages the native `vector` extension:

```sql
-- Enable the vector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Sessions Table
CREATE TABLE sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title VARCHAR(255) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- Messages Table
CREATE TABLE messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
    role VARCHAR(50) NOT NULL, -- 'user' | 'assistant' | 'system'
    content TEXT NOT NULL,
    sources JSONB DEFAULT '[]'::jsonb,
    mode VARCHAR(50) DEFAULT 'default', -- 'default' | 'ship30'
    provider VARCHAR(50) DEFAULT 'ollama', -- 'ollama' | 'claude' | 'openai'
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- Artifacts Table
CREATE TABLE artifacts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    message_id UUID NOT NULL REFERENCES messages(id) ON DELETE CASCADE,
    session_id UUID NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
    artifact_type VARCHAR(50) NOT NULL, -- 'markdown' | 'html'
    title VARCHAR(255) NOT NULL,
    content TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- Transcript Chunks with pgvector
CREATE TABLE transcript_chunks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    episode_slug VARCHAR(120) NOT NULL,
    episode_title VARCHAR(255) NOT NULL,
    guest_name VARCHAR(120) NOT NULL,
    youtube_url VARCHAR(255),
    publish_date VARCHAR(50),
    timestamp_ref VARCHAR(50) NOT NULL,
    chunk_index INTEGER NOT NULL,
    chunk_text TEXT NOT NULL,
    token_count INTEGER NOT NULL,
    embedding vector(384) NOT NULL
);

-- Approximate Nearest Neighbor Index (HNSW) for Cosine Distance
CREATE INDEX IF NOT EXISTS idx_transcript_chunks_hnsw 
ON transcript_chunks 
USING hnsw (embedding vector_cosine_ops)
WITH (m = 16, ef_construction = 64);
```

---

## 3. Data Contracts & API Specification

### 3.1 REST Endpoints
- `GET /api/health`: Diagnostic probe returning status of Database, Ollama, Vector Index count, and Cloud Provider keys.
- `POST /api/sessions`: Create a new session. Returns `{ "session_id": "...", "title": "..." }`.
- `GET /api/sessions`: List all historical sessions sorted by `updated_at DESC`.
- `GET /api/sessions/{session_id}`: Retrieve message history and associated artifacts.
- `DELETE /api/sessions/{session_id}`: Delete a session and associated records.
- `POST /api/chat`: Server-Sent Events (SSE) streaming endpoint.

### 3.2 SSE Event Contract
```json
event: message
data: {"type": "status", "content": "Searching Lenny's Podcast archive..."}

event: message
data: {"type": "sources", "sources": [
  {
    "episode": "How to build a high-performing growth team",
    "guest": "Adam Fishman",
    "timestamp": "00:00:00",
    "youtube_url": "https://www.youtube.com/watch?v=wP8YyWH524A",
    "score": 0.82,
    "text": "Onboarding is the only part of your product experience that a hundred percent of people are ever going to touch..."
  }
]}

event: message
data: {"type": "token", "content": "According to Adam Fishman..."}

event: message
data: {"type": "artifact", "artifact": {
  "type": "markdown",
  "title": "The Onboarding Imperative: A 100% Leverage Point",
  "content": "# The Onboarding Imperative\n\n..."
}}

event: message
data: {"type": "done", "session_id": "...", "message_id": "..."}
```

---

## 4. Ingestion & Retrieval Pipeline

### 4.1 Ingestion Flow
1. **Source Sourcing:** Fetches raw transcripts from `ChatPRD/lennys-podcast-transcripts`.
2. **Parsing:** Extracts YAML frontmatter (`guest`, `title`, `youtube_url`, `publish_date`, `keywords`).
3. **Chunking:** Splits by speaker dialogue blocks while maintaining a recursive sliding window of 500–800 tokens with 100-token overlap.
4. **Dense Embedding:** Computes 384-dimensional dense vectors using `sentence-transformers/all-MiniLM-L6-v2`.
5. **Persistence & Indexing:** Batch inserts chunks into PostgreSQL and builds the HNSW cosine similarity index.

### 4.2 Retrieval Flow & Strict Grounding
1. User enters a query. Query embedding is calculated via `all-MiniLM-L6-v2`.
2. PostgreSQL executes:
   ```sql
   SELECT episode_title, guest_name, chunk_text, timestamp_ref, youtube_url,
          1 - (embedding <=> :query_vector::vector) AS similarity_score
   FROM transcript_chunks
   WHERE 1 - (embedding <=> :query_vector::vector) >= :threshold
   ORDER BY similarity_score DESC
   LIMIT :top_k;
   ```
3. **Strict Threshold Gating:** If the top chunk similarity score $< 0.50$, the retriever flags the query as out-of-domain. The assistant produces the standard rejection response without hallucinating.

---

## 5. Model Routing & Dual Provider Layer

```
                        ┌───────────────────────────────┐
                        │   Incoming Request Payload    │
                        │   (provider: 'ollama'|'claude')│
                        └───────────────┬───────────────┘
                                        │
                        ┌───────────────▼───────────────┐
                        │       Provider Factory        │
                        └───────┬───────────────┬───────┘
                                │               │
              if 'ollama'       │               │ if 'claude' / 'openai'
                                ▼               ▼
                    ┌──────────────────┐ ┌───────────────────┐
                    │  OllamaProvider  │ │   CloudProvider   │
                    │  (Local Daemon)  │ │ (Anthropic/OpenAI)│
                    │ :11434/api/chat  │ │   API Endpoints   │
                    └─────────┬────────┘ └─────────┬─────────┘
                              │                    │
                              └─────────┬──────────┘
                                        │
                                        ▼
                        ┌───────────────────────────────┐
                        │ Standardized Async Generator  │
                        │   async for token in stream   │
                        └───────────────────────────────┘
```

---

## 6. Security Boundaries & Sandboxed Artifact Isolation

Artifacts can contain arbitrary HTML and CSS. To protect user privacy and system security:
1. **Sanitization:** All HTML strings pass through `DOMPurify.sanitize(html, { WHOLE_DOCUMENT: true, ADD_TAGS: ['style', 'link', 'script'] })`.
2. **Iframe Sandboxing:** Rendered in an `<iframe>` configured strictly as:
   ```html
   <iframe sandbox="allow-scripts" srcdoc={cleanHtml} />
   ```
   **Security Guarantee:**
   - `allow-scripts`: Allows interactive client-side JavaScript within the artifact.
   - **Absence of `allow-same-origin`:** Ensures the iframe executes in a unique, opaque origin. It CANNOT access parent cookies, local storage, session storage, authentication headers, or parent DOM elements.
