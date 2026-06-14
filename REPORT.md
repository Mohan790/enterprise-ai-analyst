# Enterprise AI Data Analyst — Architecture Report

## 1. System Architecture
                ┌─────────────────────────┐
                │   User Question (API)   │
                └────────────┬────────────┘
                             ▼
                ┌─────────────────────────┐
                │   LangGraph ReAct Agent │
                │   (Llama 3.1 via Groq)  │
                └──────┬──────────┬───────┘
                       ▼          ▼
          ┌──────────────────┐  ┌────────────────────────────┐
          │  execute_sql     │  │  search_vector_db          │
          │  (SQLite)        │  │  1. Instructor/Pydantic    │
          │  revenue, income,│  │     extracts company_name  │
          │  EPS per company │  │     & document_year filters│
          │  + error recovery│  │  2. Filtered Qdrant search │
          └──────────────────┘  │     (MiniLM embeddings)    │
                       │        └────────────────────────────┘
                       ▼          │
                ┌─────────────────────────┐
                │  Final Answer + Token   │
                │  Cost Logging (FastAPI) │
                └─────────────────────────┘
### Vector ETL Pipeline (Phase 1)
- 9 companies' 2023 annual reports (Apple, Microsoft, Google, Amazon, Tesla, Meta, Nvidia, Samsung, Netflix)
- Cleaned with regex normalization (whitespace, non-ASCII removal)
- Split using `SemanticChunker` (percentile-based breakpoints, not fixed-size)
- Embedded with `sentence-transformers/all-MiniLM-L6-v2` (384-dim)
- Stored in Qdrant with structured metadata: `company_name`, `document_year`
- **Total: 632 vectors**

### Agentic State Machine (Phase 2)
- Built with LangGraph's `create_react_agent`
- LLM: Llama 3.1 8B Instant via Groq API
- System prompt routes numerical questions to `execute_sql` and qualitative questions to `search_vector_db`
- `execute_sql`: queries SQLite `financials` table (company, year, revenue_billion, net_income_billion, eps), with try/except error-recovery returning `SQL_ERROR` messages back to the agent for retry
- `search_vector_db`: uses **Instructor + Pydantic** (`VectorSearchFilter` model) to extract structured `company_name` and `document_year` filters from the natural-language query via a separate LLM call, builds a Qdrant `Filter`/`FieldCondition`, then performs filtered cosine similarity search with MiniLM embeddings

### Cloud Deployment (Phase 3)
- FastAPI wraps the agent with a `/ask` POST endpoint
- Dockerized (Python 3.11-slim base image)
- **FinOps logging**: every request returns and logs `input_tokens`, `output_tokens`, `total_tokens`, and `estimated_cost_usd`, calculated from Groq's `usage_metadata` on each AI message in the agent's loop, using Groq's published pricing ($0.05/1M input, $0.08/1M output tokens for llama-3.1-8b-instant)
- Tested via Docker container with `host.docker.internal` networking to reach Qdrant

## 2. RAGAS Evaluation (5/5 test queries — all successful)

| # | Query | Answer | Tool(s) Used | Faithfulness | Relevance |
|---|-------|--------|--------------|--------------|-----------|
| 1 | Apple total revenue 2023 | $383.3B | SQL | 1.0 | 1.0 |
| 2 | Nvidia GPU business | 92% Q1 GPU market share, AI/data center focus | Vector (filtered) | 0.9 | 1.0 |
| 3 | Tesla revenue & net income 2023 | $96.8B revenue, $15B net income | SQL | 1.0 | 1.0 |
| 4 | Meta AI investments | $10B+ AI investment, Nvidia partnership | Vector (filtered) | 0.9 | 1.0 |
| 5 | Microsoft vs Google revenue 2023 | $211.9B vs $307.4B, Google higher | SQL | 1.0 | 1.0 |

**Average Faithfulness: 0.96** — all numerical answers matched ground-truth SQLite data exactly; vector-search answers grounded in retrieved, metadata-filtered document chunks with no major hallucinations.

**Average Relevance: 1.0** — all 5 answers directly addressed the question with correct tool selection (SQL vs. filtered vector search).

## 3. Cost Analysis

| Metric | Value |
|--------|-------|
| LLM provider | Groq (Llama 3.1 8B Instant) |
| Pricing used | $0.05 / 1M input tokens, $0.08 / 1M output tokens |
| Total tokens (5 queries) | 9,228 |
| Total cost (5 queries) | $0.00047325 |
| **Cost per 100 queries** | **$0.009465** |
| Avg response time | ~6.4s per query (varies with Groq load) |
| Embedding model | Local (all-MiniLM-L6-v2), no API cost |
| Vector DB | Self-hosted Qdrant (Docker), no cloud cost |

**Note on LLM choice:** Gemini was the originally specified LLM. Free-tier quota was exhausted (`limit: 0` on `gemini-2.0-flash` and `gemini-2.0-flash-lite`) across multiple Google accounts before deployment could be completed. Groq's Llama 3.1 8B was substituted — the LangGraph architecture is LLM-agnostic; switching back to Gemini requires only changing the model initialization in `agent/graph.py`. At under $0.01 per 100 queries, the system is extremely cost-efficient regardless of provider.

## 4. Known Limitations & Future Work
- Cloud Run deployment pending — system demonstrated via local Docker container with full agent/database networking (see demo video)
- Tesla SEC filing required manual re-download due to SEC anti-bot blocking; Wikipedia used as fallback source for 4 of 9 companies
- Could add GraphRAG (Neo4j) or semantic caching (Redis) for the "Extra Mile" requirement given more time
