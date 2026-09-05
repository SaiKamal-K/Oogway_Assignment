# Product Requirements Document (PRD)
## Project: The Lenny Growth Assistant
**Status:** Approved | **Author:** Forward Deployed Engineer | **Target Audience:** Product Managers, Growth Leaders, Engineering Evaluators

---

## 1. Executive Summary & Forward Deployment Brief

### 1.1 Persona & The Problem
- **Primary Persona:** Growth Product Managers, Heads of Growth, and Product Leaders at high-growth startups and enterprises.
- **The Problem:** Lenny Rachitsky's podcast represents over 200+ hours of gold-standard operational wisdom from the world’s top product practitioners (e.g., Adam Fishman, Elena Verna, Shreyas Doshi, Brian Chesky, Gustaf Alströmer). However, this tactical knowledge is locked in lengthy audio files and unindexed transcripts. Growth leaders need instantaneous, rigorously verified answers to specific operational dilemmas (e.g., onboarding drop-off, PLG vs. sales-led motions, retention curves) without spending hours skimming transcripts or risking generic AI hallucinations.
- **Job To Be Done (JTBD):** *"When facing a critical growth or product strategy decision, I want to query Lenny's podcast archive for battle-tested tactics from proven leaders, so that I can draft high-impact strategies, executive memos, and frameworks grounded in real-world benchmarks."*

### 1.2 Core Value Propositions
1. **Zero-Hallucination Grounded Answers:** All outputs are strictly linked to episode transcripts with explicit speaker and timestamp citations (`[Episode: Guest, Timestamp]`). If information does not exist in the archive, the system explicitly declines to speculate.
2. **Ship 30 for 30 Content Engine:** Automatically converts raw tactical answers into high-retention, ~1,250-word essays formatted with clear narrative hooks, skimmable headings, bold anchor points, and actionable checklists.
3. **Claude-Style Side-by-Side Artifacts:** Provides an interactive dual-pane experience where generated Markdown briefs or interactive HTML/CSS frameworks render in a secure, isolated sandbox beside the conversation.
4. **Dual Model Layer (Local & Cloud):** Operates completely offline with zero data leakage via local Ollama models (`llama3.1:8b`), while allowing instant switching to cloud models (Claude 3.5 Sonnet / GPT-4o) via the UI without code redeployment.

---

## 2. Success Metrics

| Metric Category | Target | Measurement Methodology |
| :--- | :--- | :--- |
| **Retrieval Grounding Accuracy** | $\ge 90\%$ | Proportion of claims directly supported by retrieved chunks without fabrication. |
| **Local Time-to-First-Token (TTFT)** | $< 4.0\text{s}$ | Latency between user prompt submission and initial streaming token via Ollama `llama3.1:8b`. |
| **Artifact Security & Isolation** | $0$ XSS / zero parent leaks | Sandboxed iframe evaluation (`sandbox="allow-scripts"`, strictly omitting `allow-same-origin`) verified against malicious script execution. |
| **Out-of-Domain Rejection Rate** | $100\%$ | Strict threshold gating rejecting queries unaddressed by transcripts (e.g., general world trivia). |
| **Single-Command Startup Time** | $< 3\text{ minutes}$ | `docker-compose up` to fully initialized database, backend, and frontend. |

---

## 3. Assumptions & Constraints

1. **Host Environment:** Evaluation environment provides at least 16GB RAM and a modern multi-core CPU/GPU capable of running 8B parameter models on Ollama.
2. **Data Sourcing:** Transcripts are sourced from the open-source [ChatPRD/lennys-podcast-transcripts](https://github.com/ChatPRD/lennys-podcast-transcripts) repository. Transcripts include YAML metadata (guest, title, date, keywords) and timestamped speaker lines.
3. **Network Autonomy:** The system must function completely offline when configured with local Ollama embeddings and local LLMs, requiring internet connectivity only if cloud LLMs (Anthropic/OpenAI) are explicitly toggled.

---

## 4. Scope & Strategic Choices

### In Scope (MVP)
- **Knowledge Ingestion:** Ingestion pipeline parsing markdown transcripts, chunking (500-800 tokens, 100 overlap), generating dense vector embeddings (`all-MiniLM-L6-v2`), and indexing in PostgreSQL using `pgvector` HNSW.
- **RAG & Strict Grounding:** Semantic similarity search with similarity threshold gating ($\ge 0.50$ cosine threshold), returning formatted citations and source drawer metadata.
- **Ship 30 for 30 Generator:** Structured prompting engine producing ~1,250 words, short paragraphs (1-3 sentences), hook, bold anchors, and implementation checklists.
- **Artifact Sandbox:** Two-column split UI with tabbed Preview/Code viewer, supporting live Markdown rendering and DOMPurified HTML/CSS rendering inside a secure iframe.
- **Model Router:** Instant switching between Ollama (`llama3.1:8b`), Anthropic Claude, and OpenAI via UI header.
- **Persistence:** PostgreSQL storage for sessions, message history, retrieved sources, and generated artifacts.

### Intentionally Deferred (Post-MVP)
- **Audio Playback Synchronization:** Directly scrubbing podcast audio to timestamp markers (deferred to conserve bandwidth and simplify evaluation).
- **Multi-Tenant User Authentication:** Enterprise SSO/OAuth2 (deferred in favor of session-based UUID isolation for straightforward evaluation).

---

## 5. User Flows & Acceptance Criteria

### Flow 1: Grounded Growth Question
1. User enters: *"What is Adam Fishman's view on onboarding and why is it a 100% lever?"*
2. System displays status: *"Searching Lenny's Podcast archive..."*
3. Chunks are retrieved from Adam Fishman's episode.
4. Assistant streams answer with citation tags: `[Adam Fishman, 00:00:00]`.
5. Sources drawer displays the exact episode title, YouTube link, timestamp, and transcript excerpt.

### Flow 2: Ship 30 for 30 Essay Generation
1. User toggles **Ship 30 for 30 Mode** and asks: *"Write an essay on building high-retention onboarding flows based on Lenny's guests."*
2. Assistant streams an essay structured with:
   - Compelling hook highlighting common onboarding fallacies.
   - 1 to 3 sentence paragraph blocks.
   - Bold anchor words for each tactical point.
   - Specific quotes/ideas attributed to guests.
   - An operational checklist conclusion.
3. The right-hand **Artifact Viewer** automatically slides open, rendering the formatted essay live with options to copy or download.

### Flow 3: Out-of-Domain Guardrail
1. User asks: *"Who won the 2022 World Cup?"*
2. Cosine similarity score fails the threshold ($< 0.50$).
3. Assistant returns: *"I do not have sufficient information in Lenny's podcast archive to answer this question. Please ask a product, growth, or leadership question covered in the podcast."*

---

## 6. Risks & Mitigation Matrix

| Risk | Impact | Likelihood | Mitigation Strategy |
| :--- | :--- | :--- | :--- |
| **Local Model Hallucination** | High | Medium | Strict system prompt instructing the model to rely *only* on context and cite sources; hard similarity threshold gating. |
| **Ollama Connectivity / Latency** | Medium | Low | Healthcheck endpoint diagnosing Ollama status; timeout handling with user-friendly error banners in UI. |
| **Malicious HTML in Artifacts** | High | Low | Dual-layer defense: `DOMPurify` sanitization in JavaScript + `sandbox="allow-scripts"` (strictly excluding `allow-same-origin`) on iframe. |
| **Database Connection Failures** | High | Low | Resilient connection pool in SQLAlchemy with health retry loops and graceful startup diagnostics. |
