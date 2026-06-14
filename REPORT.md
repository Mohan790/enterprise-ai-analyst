# Enterprise AI Data Analyst — Architecture Report

## 1. System Architecture
┌─────────────────────────┐
                │   User Question (API)   │
                └────────────┬────────────┘
                             ▼
                ┌─────────────────────────┐
                │   LangGraph ReAct Agent  │
                │   (Llama 3.1 via Groq)   │
                └──────┬──────────┬────────┘
                       ▼          ▼
          ┌─────────────────┐  ┌──────────────────────┐
          │  execute_sql      │  │  search_vector_db     │
          │  (SQLite)         │  │  (Qdrant + MiniLM)    │
          │  revenue, income, │  │  9 companies, 632     │
          │  EPS per company  │  │  semantic chunks      │
          └─────────────────┘  └──────────────────────┘
                       │          │
                       ▼          ▼
                ┌─────────────────────────┐
                │  Final Answer + Latency  │
                │  Logging (FastAPI)       │
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
- System prompt explicitly routes numerical questions to `execute_sql` and qualitative questions to `search_vector_db`
- `execute_sql`: queries SQLite `financials` table (company, year, revenue_billion, net_income_billion, eps), with try/except error-recovery returning `SQL_ERROR` messages back to the agent for retry
- `search_vector_db`: embeds the query with MiniLM and performs cosine similarity search against Qdrant

### Cloud Deployment (Phase 3)
- FastAPI wraps the agent with a `/ask` POST endpoint
- Dockerized (Python 3.11-slim base image)
- Response time logged per request for FinOps tracking
- Tested via Docker container with `host.docker.internal` networking to reach Qdrant

## 2. RAGAS Evaluation (5/5 test queries — all successful)

| # | Query | Answer | Tool Used | Faithfulness | Relevance |
|---|-------|--------|-----------|--------------|-----------|
| 1 | Apple total revenue 2023 | $383.3B | SQL | 1.0 | 1.0 |
| 2 | Nvidia GPU business | GPU market leadership, AI/data science expansion | Vector | 0.9 | 1.0 |
| 3 | Tesla revenue & net income 2023 | $96.8B revenue, $15B net income | SQL | 1.0 | 1.0 |
| 4 | Meta AI investments | AI startup investments, Nvidia partnership | Vector | 0.9 | 1.0 |
| 5 | Microsoft vs Google revenue 2023 | $211.9B vs $307.4B, $95.5B difference computed | SQL | 1.0 | 1.0 |

**Average Faithfulness: 0.96** — all numerical answers matched ground-truth SQLite data exactly; vector-search answers grounded in retrieved document chunks with no major hallucinations.

**Average Relevance: 1.0** — all 5 answers directly addressed the question, including correct tool selection (SQL vs vector) and an emergent calculation (revenue difference) on query 5.

## 3. Cost Analysis

| Metric | Value |
|--------|-------|
| LLM provider | Groq (Llama 3.1 8B Instant) — free tier |
| Avg response time | ~0.83s per query |
| Cost per query | $0 (Groq free tier) |
| Cost per 100 queries | $0 |
| Embedding model | Local (all-MiniLM-L6-v2), no API cost |
| Vector DB | Self-hosted Qdrant (Docker), no cloud cost |

**Note:** Gemini was the originally intended LLM. Free-tier quota was exhausted (`limit: 0` on `gemini-2.0-flash` and `gemini-2.0-flash-lite`) across multiple Google accounts before deployment could be completed. Groq's Llama 3.1 8B was substituted — the LangGraph architecture is LLM-agnostic; switching back to Gemini requires only changing the model initialization in `agent/graph.py`.

## 4. Known Limitations & Future Work
- Cloud Run deployment pending — system demonstrated via local Docker container with full agent/database networking (see demo video)
- Tesla SEC filing required manual re-download due to SEC anti-bot blocking; Wikipedia used as fallback source for 4 of 9 companies
- Could add GraphRAG (Neo4j) or semantic caching (Redis) for the "Extra Mile" requirement given more time
