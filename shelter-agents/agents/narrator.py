import requests
import os
from datetime import datetime

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://ollama:11434")
API_URL = os.getenv("API_URL", "http://shelter-api:8000")

def fetch(path):
    r = requests.get(f"{API_URL}{path}")
    return r.json() if r.status_code == 200 else {}

def run_narrator():
    print("=== Narrator Agent ===")

    metrics = fetch("/metrics")
    by_shelter = fetch("/metrics/by-shelter")
    species = fetch("/metrics/species")
    animals = fetch("/animals")

    from agents.generator import DOG_BREEDS
    long_stay = [a for a in animals if a.get("status") == "available"]
    long_stay_count = sum(1 for a in long_stay if _days(a["intake_date"]) >= 30)
    most_urgent = sorted(
        [a for a in long_stay if _days(a["intake_date"]) >= 30],
        key=lambda a: _days(a["intake_date"]),
        reverse=True
    )
    urgent_name = most_urgent[0]["name"] if most_urgent else None
    urgent_days = _days(most_urgent[0]["intake_date"]) if most_urgent else 0

    near_capacity = [s for s in by_shelter if s["adoption_rate"] == max(s2["adoption_rate"] for s2 in by_shelter)]
    top_shelter = near_capacity[0]["shelter"] if near_capacity else "unknown"

    dogs_available = species.get("dog", {}).get("available", 0)
    cats_available = species.get("cat", {}).get("available", 0)

    context = f"""
You are a shelter network analyst writing a brief daily update for a public dashboard.
Keep it to 2-3 sentences. Be warm, factual, and encouraging. No bullet points.

Current data:
- Total animals: {metrics.get('total_animals', 0)}
- Available for adoption: {metrics.get('available', 0)} ({dogs_available} dogs, {cats_available} cats)
- Adopted total: {metrics.get('adopted', 0)}
- Network adoption rate: {metrics.get('adoption_rate', 0)}%
- Animals in shelter 30+ days: {long_stay_count}
- Most urgent case: {f"{urgent_name} has been waiting {urgent_days} days" if urgent_name else "none"}
- Best performing shelter: {top_shelter}

Write the daily summary now:
"""

    print("  Generating narrative via Ollama...")
    try:
        response = requests.post(
            f"{OLLAMA_URL}/api/chat",
            json={
                "model": "mistral",
                "messages": [
                    {"role": "user", "content": context}
                ],
                "stream": False
            },
            timeout=60
        )
        summary = response.json()["message"]["content"].strip()
        print(f"  Summary: {summary}")

        post = requests.post(f"{API_URL}/metrics/summary", json={"summary": summary})
        if post.status_code == 200:
            print("  Posted to API successfully.")
        else:
            print(f"  Failed to post: {post.text}")

    except Exception as e:
        print(f"  Error: {e}")

    print("=== Narrator complete ===")

def _days(iso):
    try:
        return (datetime.utcnow() - datetime.fromisoformat(iso.replace("Z", ""))).days
    except:
        return 0
