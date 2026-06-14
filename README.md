# Enterprise AI Data Analyst

A Multi-Modal Enterprise Agent that answers business questions by combining structured SQL data with semantic search over financial documents.

## Architecture

1. **Vector ETL Pipeline** — Ingests 10-K/financial documents, cleans text, splits into semantic chunks using `SemanticChunker`, embeds with `all-MiniLM-L6-v2`, and stores in Qdrant with metadata (`company_name`, `document_year`).
2. **LangGraph ReAct Agent** — Two tools:
   - `execute_sql`: queries a SQLite database of financial metrics (revenue, net income, EPS) with error-recovery.
   - `search_vector_db`: semantic search over Qdrant for qualitative information from reports.
3. **FastAPI + Docker** — Wraps the agent as a REST API (`/ask`), containerized, with response time logging for FinOps tracking.

## Companies covered
Apple, Microsoft, Google, Amazon, Tesla, Meta, Nvidia, Samsung, Netflix (2023 data)

## How to run

### 1. Start Qdrant (vector database)
```bash
docker compose up -d
```

### 2. Set up environment
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Create a `.env` file:
### 3. Run the ETL pipeline (one-time)
```bash
python etl/pipeline.py
```

### 4. Run the API
```bash
uvicorn api.main:app --reload --port 8080
```

### 5. Or run with Docker
```bash
docker build -t ai-analyst .
docker run -p 8080:8080 -e QDRANT_HOST=host.docker.internal --add-host=host.docker.internal:host-gateway ai-analyst
```

### 6. Test
```bash
curl -X POST http://localhost:8080/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "What was Tesla revenue in 2023?"}'
```

## Tech Stack
- LangGraph (ReAct agent)
- Groq (Llama 3.1 8B) — chosen for free, reliable inference after Gemini quota exhaustion
- Qdrant (vector database)
- HuggingFace `all-MiniLM-L6-v2` (embeddings)
- SQLite (structured financial data)
- FastAPI + Docker

## Team
Mohan Balaji Rajaram and Ezekiel

## Vedio 
https://1drv.ms/v/c/5cc8b40456e8a390/IQCUEtgjMdfmS61Gy7fM-WUSAdOxw9qHAAGxMAInAmqqNyQ?e=iQHkZq
