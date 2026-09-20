"""Standard-library load harness for a running local stack.

Usage: python tests/load/search_load.py TOKEN [BASE_URL]
"""

import json
import statistics
import sys
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor

TOKEN = sys.argv[1]
BASE_URL = sys.argv[2] if len(sys.argv) > 2 else "http://localhost:8000"
REQUESTS = 100


def search(_: int) -> tuple[float, int]:
    request = urllib.request.Request(
        f"{BASE_URL}/search",
        data=json.dumps({"query": "What are the primary risks?", "limit": 8}).encode(),
        headers={"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json"},
    )
    started = time.perf_counter()
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            return (time.perf_counter() - started) * 1000, response.status
    except Exception:
        return (time.perf_counter() - started) * 1000, 0


with ThreadPoolExecutor(max_workers=100) as executor:
    results = list(executor.map(search, range(REQUESTS)))

latencies = [latency for latency, _ in results]
successes = sum(status == 200 for _, status in results)
print(
    json.dumps(
        {
            "requests": REQUESTS,
            "successes": successes,
            "failure_rate": 1 - successes / REQUESTS,
            "mean_ms": round(statistics.mean(latencies), 2),
            "p95_ms": round(sorted(latencies)[int(REQUESTS * 0.95) - 1], 2),
        },
        indent=2,
    )
)
