import os, sqlite3
from typing import Optional
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from groq import Groq
import instructor
from langchain_groq import ChatGroq
from langchain_core.tools import tool
from langgraph.prebuilt import create_react_agent
from langchain_huggingface import HuggingFaceEmbeddings
from qdrant_client import QdrantClient
from qdrant_client.models import Filter, FieldCondition, MatchValue

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

llm = ChatGroq(model="llama-3.1-8b-instant", api_key=GROQ_API_KEY)
embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
qdrant = QdrantClient(host=os.getenv("QDRANT_HOST", "localhost"), port=6333)

# --- Instructor client for structured metadata extraction ---
instructor_client = instructor.from_groq(Groq(api_key=GROQ_API_KEY), mode=instructor.Mode.JSON)

VALID_COMPANIES = ["Apple", "Microsoft", "Google", "Amazon", "Tesla", "Meta", "Nvidia", "Samsung", "Netflix"]

class VectorSearchFilter(BaseModel):
    """Structured filters extracted from a user's natural language question."""
    company_name: Optional[str] = Field(
        default=None,
        description=f"Company name if the question mentions one of: {VALID_COMPANIES}. Otherwise null."
    )
    document_year: Optional[int] = Field(
        default=None,
        description="The year of the report being asked about, if mentioned. Otherwise null."
    )
    semantic_query: str = Field(
        description="A cleaned-up version of the question, suitable for semantic search."
    )


@tool
def search_vector_db(query: str) -> str:
    """Use this tool for QUALITATIVE questions about a company's business, strategy, risks, products, or investments
    (e.g. 'what does X say about Y', 'what are the risks', 'describe their AI strategy').
    This tool uses an LLM to extract structured metadata filters (company_name, document_year)
    from your query before performing semantic search over financial report documents."""

    # Step 1: extract structured filters using Instructor + Pydantic
    try:
        filters = instructor_client.chat.completions.create(
            model="llama-3.1-8b-instant",
            response_model=VectorSearchFilter,
            messages=[{
                "role": "user",
                "content": f"Extract search filters from this question: '{query}'"
            }],
        )
    except Exception:
        filters = VectorSearchFilter(semantic_query=query)

    # Step 2: build Qdrant filter from extracted metadata
    conditions = []
    if filters.company_name and filters.company_name in VALID_COMPANIES:
        conditions.append(FieldCondition(key="company_name", match=MatchValue(value=filters.company_name)))
    if filters.document_year:
        conditions.append(FieldCondition(key="document_year", match=MatchValue(value=filters.document_year)))
    qdrant_filter = Filter(must=conditions) if conditions else None

    # Step 3: embed and search with filter applied
    vector = embeddings.embed_query(filters.semantic_query)
    results = qdrant.query_points(
        "financial_docs",
        query=vector,
        query_filter=qdrant_filter,
        limit=3
    ).points

    if not results:
        return f"No results found (filters applied: company={filters.company_name}, year={filters.document_year})."

    return "\n\n".join([
        f"Company: {r.payload['company_name']} ({r.payload['document_year']})\n{r.payload['text'][:400]}"
        for r in results
    ])


@tool
def execute_sql(query: str) -> str:
    """Use this tool for NUMERICAL questions about revenue, net income, or EPS
    (e.g. 'what was the revenue', 'compare net income').
    Table name: financials
    Columns: id, company, year, revenue_billion, net_income_billion, eps
    Example: SELECT company, revenue_billion FROM financials WHERE company='Nvidia' AND year=2023
    """
    conn = sqlite3.connect("data/financials.db")
    try:
        cursor = conn.execute(query)
        rows = cursor.fetchall()
        cols = [d[0] for d in cursor.description]
        return str([dict(zip(cols, row)) for row in rows])
    except Exception as e:
        return f"SQL_ERROR: {e} — please rewrite the query and try again."
    finally:
        conn.close()


SYSTEM_PROMPT = """You are a financial data analyst assistant. You have exactly two tools:
1. execute_sql - for numerical financial metrics (revenue, net income, EPS)
2. search_vector_db - for qualitative information from annual reports (strategy, risks, products, investments).
   This tool automatically extracts company/year filters from your query using structured extraction.

Only use these two tools. Never invent or call any other tool.
For qualitative questions (e.g. about AI investments, GPU business, supply chain risks), always use search_vector_db first.
Always give a clear, direct final answer in plain English."""

agent = create_react_agent(llm, [search_vector_db, execute_sql], prompt=SYSTEM_PROMPT)


# --- Token cost calculation (FinOps) ---
# Groq pricing for llama-3.1-8b-instant (per million tokens)
PRICE_PER_M_INPUT = 0.05
PRICE_PER_M_OUTPUT = 0.08

def calculate_token_cost(messages) -> dict:
    """Sum token usage across all AI messages in the agent's loop and estimate cost."""
    total_input = 0
    total_output = 0
    for m in messages:
        usage = getattr(m, "usage_metadata", None)
        if usage:
            total_input += usage.get("input_tokens", 0)
            total_output += usage.get("output_tokens", 0)
    cost = (total_input / 1_000_000 * PRICE_PER_M_INPUT) + (total_output / 1_000_000 * PRICE_PER_M_OUTPUT)
    return {
        "input_tokens": total_input,
        "output_tokens": total_output,
        "total_tokens": total_input + total_output,
        "estimated_cost_usd": round(cost, 8)
    }


if __name__ == "__main__":
    print("Testing agent...\n")
    result = agent.invoke({
        "messages": [("user", "What does Nvidia say about their GPU business?")]
    })
    print("\nFinal Answer:", result["messages"][-1].content)
    print("\nToken usage:", calculate_token_cost(result["messages"]))
