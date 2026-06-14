import os, sqlite3
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.tools import tool
from langgraph.prebuilt import create_react_agent
from langchain_huggingface import HuggingFaceEmbeddings
from qdrant_client import QdrantClient

load_dotenv()

llm = ChatGroq(
    model="llama-3.1-8b-instant",
    api_key=os.getenv("GROQ_API_KEY")
)
embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
qdrant = QdrantClient(host=os.getenv("QDRANT_HOST", "localhost"), port=6333)

@tool
def search_vector_db(query: str) -> str:
    """Search financial documents for relevant information about companies."""
    vector = embeddings.embed_query(query)
    results = qdrant.query_points("financial_docs", query=vector, limit=3).points
    if not results:
        return "No results found."
    return "\n\n".join([
        f"Company: {r.payload['company_name']} ({r.payload['document_year']})\n{r.payload['text'][:300]}"
        for r in results
    ])


@tool
def execute_sql(query: str) -> str:
    """Execute SQL on financial database. 
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

agent = create_react_agent(llm, [search_vector_db, execute_sql])

if __name__ == "__main__":
    print("Testing agent...\n")
    result = agent.invoke({
        "messages": [("user", "What was Nvidia revenue in 2023 and what are they known for?")]
    })
    print("\nFinal Answer:", result["messages"][-1].content)
