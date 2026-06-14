import requests, time, json

API = "http://localhost:8080/ask"

test_queries = [
    "What was Apple's total revenue in 2023?",
    "What does Nvidia say about their GPU business?",
    "What was Tesla's revenue and net income in 2023?",
    "What does Meta's report say about their AI investments?",
    "Compare Microsoft and Google revenue in 2023",
]

results = []
total_cost = 0
for q in test_queries:
    try:
        r = requests.post(API, json={"question": q}, timeout=60)
        data = r.json()
        answer = data.get('answer', 'ERROR')
        elapsed = data.get('time_seconds', 0)
        usage = data.get('token_usage', {})
        total_cost += usage.get('estimated_cost_usd', 0)
    except Exception as e:
        answer = f"ERROR: {e}"
        elapsed = 0
        usage = {}

    print(f"\nQ: {q}")
    print(f"A: {answer}")
    print(f"Time: {elapsed}s | Tokens: {usage.get('total_tokens', 0)} | Cost: ${usage.get('estimated_cost_usd', 0)}")
    results.append({"question": q, "answer": answer, "time": elapsed, "token_usage": usage})
    time.sleep(5)

print(f"\n\nTotal cost for 5 queries: ${total_cost:.8f}")
print(f"Projected cost per 100 queries: ${(total_cost/5)*100:.6f}")

with open("eval/results.json", "w") as f:
    json.dump({"results": results, "total_cost_5_queries": total_cost, "cost_per_100_queries": (total_cost/5)*100}, f, indent=2)

print("\nAll results saved to eval/results.json")
