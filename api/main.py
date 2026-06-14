import os, sys, time
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI
from pydantic import BaseModel
from agent.graph import agent, calculate_token_cost

app = FastAPI(title="Enterprise AI Analyst")

class Query(BaseModel):
    question: str

@app.get("/")
def root():
    return {"status": "ok", "message": "Enterprise AI Analyst is running!"}

@app.post("/ask")
def ask(query: Query):
    start = time.time()
    result = agent.invoke({
        "messages": [("user", query.question)]
    })
    elapsed = round(time.time() - start, 2)
    answer = result["messages"][-1].content
    usage = calculate_token_cost(result["messages"])

    print(f"[LOG] Q: {query.question}")
    print(f"[LOG] A: {answer[:100]}")
    print(f"[LOG] Time: {elapsed}s")
    print(f"[LOG] Tokens: input={usage['input_tokens']} output={usage['output_tokens']} total={usage['total_tokens']}")
    print(f"[LOG] Estimated cost: ${usage['estimated_cost_usd']}")

    return {
        "question": query.question,
        "answer": answer,
        "time_seconds": elapsed,
        "token_usage": usage
    }
