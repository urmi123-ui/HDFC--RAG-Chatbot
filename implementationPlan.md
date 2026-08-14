# Implementation Plan: Mutual Fund FAQ Assistant

This document outlines the phase-wise implementation plan for the Facts-Only RAG Mutual Fund FAQ Assistant, derived from the `architecture.md` and `problemStatement.md` requirements.

## Phase 1: Project Setup & Environment Configuration
**Objective**: Establish the foundation of the project, including directory structure, dependencies, and configuration.

1. **Initialize Project Directory**:
   - Create directories: `data/raw/`, `data/processed/`, `data/index/`, `ingestion/`, `app/`, `ui/`, `config/`, `scheduler/`.
2. **Setup Dependencies (`requirements.txt`)**:
   - Install `fastapi`, `uvicorn`, `beautifulsoup4`, `chromadb`, `sentence-transformers`, `openai` (or equivalent LLM SDK), `apscheduler`, `pyyaml`.
3. **Configuration & Environment**:
   - Create a `.env` file for API keys (e.g., `OPENAI_API_KEY`).
   - Create `config/corpus.yaml` containing the 12 active HDFC Mutual Fund scheme URLs (Groww links) and basic metadata (scheme name, slug, category).

---

## Phase 2: Offline Ingestion Pipeline
**Objective**: Build the scripts to fetch, parse, chunk, and embed the mutual fund scheme pages into the vector database.

1. **`ingestion/fetch.py`**:
   - Create a scraper to perform HTTP GET requests for each URL defined in `corpus.yaml`.
   - Save raw HTML files to `data/raw/` with a timestamp.
2. **`ingestion/parse.py`**:
   - Clean the HTML (remove navigation, footers).
   - Extract content into logical sections (e.g., `expense_ratio`, `exit_load`, `fund_management`).
3. **`ingestion/chunk.py`**:
   - Implement **Section-Aware Semantic Chunking**.
   - Treat small sections as single chunks (pass-through).
   - Split larger sections into 200-300 token chunks with ~50 tokens overlap, ensuring no overlap across different sections.
   - Attach rich metadata to each chunk (`slug`, `section`, `last_updated`, `source_url`).
4. **`ingestion/index.py`**:
   - Use `sentence-transformers` with the **`BAAI/bge-small-en-v1.5`** model to generate embeddings.
   - Upsert embeddings and the attached metadata into **ChromaDB** located at `data/index/`.
5. **`ingestion/run.py`**:
   - Create the main entrypoint that orchestrates fetching, parsing, chunking, and indexing sequentially.

---

## Phase 3: Core Retrieval & Validation Logic
**Objective**: Implement the backend logic for classifying user intent, retrieving grounded information, and enforcing facts-only compliance.

1. **`app/classifier.py`**:
   - Implement logic (rule-based or lightweight LLM prompt) to route queries:
     - *Factual* (Proceed to RAG; e.g., expense ratios, exit loads, fund management/manager details)
     - *Advisory* / *Comparison* (Route to refusal handler)
     - *Performance* (Link-only fallback)
2. **`app/retriever.py`**:
   - Implement **Two-Stage Scheme-Resolved Hybrid Retrieval**:
     - **Stage 1 (Scheme & Section Intent Resolution)**: Parse query using fuzzy substring matching against `corpus.yaml` scheme slugs and names to identify the target scheme. Detect keyword-based section intent (e.g., 'manager' -> `fund_management`).
     - **Stage 2 (Metadata-Filtered Query)**: Query ChromaDB with BGE-small-en-v1.5. If a scheme is resolved, query with a metadata filter (`where={"slug": resolved_slug}`). Boost or prioritize chunks matching the resolved section intent. If no scheme is resolved, run a global vector search (top-k=5) or ask for clarification.
3. **`app/validator.py`**:
   - Post-generation checks to ensure the LLM output is ≤ 3 sentences and contains no advisory language.
4. **`app/formatter.py`**:
   - Structure the API JSON response with the final answer, citation URL, `last_updated` date (from chunk metadata), and disclaimer snippet.

---

## Phase 4: Generation Layer & API Gateway
**Objective**: Integrate the LLM and expose the system via a REST API.

1. **`app/generator.py`**:
   - Define the strict System Prompt enforcing facts-only answers and limiting to retrieved context.
   - Integrate the **Groq SDK** to generate answers based on retrieved top-k chunks using the **`llama-3.3-70b-versatile`** model.
   - Implement the `Refusal Handler` template for advisory/comparison queries, providing relevant AMFI/SEBI links instead of generated text.
2. **`app/main.py`**:
   - Setup a FastAPI server.
   - Create the `POST /api/chat` endpoint taking a simple JSON payload `{ "message": "query" }`.
   - Wire together the classifier, retriever, generator, and formatter to process the request and return the structured response.

---

## Phase 5: Minimal User Interface
**Objective**: Create a clean, front-end presentation layer for user interaction.

1. **`ui/index.html`**:
   - Develop a single-page HTML/JS/CSS app.
   - Display a welcome message and the required disclaimer: *"Facts-only. No investment advice."*
   - Add clickable example questions:
     - *What is the expense ratio of HDFC Mid Cap Fund Direct Growth?*
     - *What is the exit load on HDFC Defence Fund Direct Growth?*
     - *Who manages HDFC Gold ETF Fund of Fund Direct Plan Growth?*
   - Implement a chat window that hits the `POST /api/chat` endpoint and renders the assistant's reply along with the single citation link and last-updated footer.

---

## Phase 6: Daily Scheduler & Final Testing
**Objective**: Automate data freshness and perform end-to-end verification.

1. **`scheduler/daily.py`**:
   - Implement `APScheduler` to trigger `ingestion/run.py` daily at 10:00 AM IST (Asia/Kolkata timezone) to update ChromaDB automatically.
2. **Testing & Verification**:
   - Run unit tests for `classifier.py` and `validator.py`.
   - Perform manual UI testing against edge cases (e.g., asking for stock advice, comparing two schemes).
   - Verify that the system refuses correctly and only provides data backed by the 12 specific HDFC Groww URLs.
