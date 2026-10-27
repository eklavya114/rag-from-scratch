"""
load_test_http.py

Measures the server from the OUTSIDE: real HTTP requests over a real
socket, timed with perf_counter the same way Day 22's load_test.py timed
in-process calls. Comparing the two numbers side by side shows exactly
what the network layer costs on top of the service's own work, since
every other part of the pipeline (retrieval, ranking, generation,
caching) is identical between the two runs.
"""

import json
import os
import random
import sys
import threading
import time
import urllib.request
from http.server import ThreadingHTTPServer

sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "day-22-production-rag"))

from api_server import RagRequestHandler, build_app_state
from config import Config  # Day 22
from rag_service import RagService  # Day 22

import load_test as day22_load_test  # Day 22, reused directly for the in-process comparison

NUM_REQUESTS = 100

QUERY_POOL = [
    "What is RAG?",
    "What is RAG?",
    "What is RAG?",
    "What is a vector database?",
    "What is a vector database?",
    "What programming language is easy to read?",
]


def percentile(sorted_values, pct):
    if not sorted_values:
        return 0.0
    index = min(len(sorted_values) - 1, int(len(sorted_values) * pct / 100))
    return sorted_values[index]


def run_http_load_test(base_url, num_requests=NUM_REQUESTS, seed=42):
    """Sends num_requests real HTTP requests to a running server and times each one end to end, including the network round trip, not just the service's internal work."""
    rng = random.Random(seed)
    latencies_ms = []
    status_counts = {}

    for _ in range(num_requests):
        query_text = rng.choice(QUERY_POOL)
        data = json.dumps({"query": query_text}).encode("utf-8")
        request = urllib.request.Request(f"{base_url}/query", data=data, method="POST")

        start = time.perf_counter()
        try:
            with urllib.request.urlopen(request, timeout=5) as response:
                status_code = response.status
                response.read()
        except Exception as e:
            status_code = getattr(e, "code", "connection_error")
        elapsed_ms = (time.perf_counter() - start) * 1000

        latencies_ms.append(elapsed_ms)
        status_counts[status_code] = status_counts.get(status_code, 0) + 1

    latencies_ms.sort()
    return {
        "p50_ms": percentile(latencies_ms, 50),
        "p95_ms": percentile(latencies_ms, 95),
        "status_counts": status_counts,
    }


def main():
    print("=== HTTP Load Test ===\n")

    RagRequestHandler.app_state = build_app_state()
    httpd = ThreadingHTTPServer(("127.0.0.1", 0), RagRequestHandler)
    port = httpd.server_port
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()

    base_url = f"http://127.0.0.1:{port}"
    print(f"Server started on {base_url}")
    print(f"Running {NUM_REQUESTS} requests over real HTTP.\n")

    try:
        http_results = run_http_load_test(base_url)
    finally:
        httpd.shutdown()
        httpd.server_close()

    print(f"p50 latency:    {http_results['p50_ms']:.4f} ms")
    print(f"p95 latency:    {http_results['p95_ms']:.4f} ms")
    print(f"Status counts:  {http_results['status_counts']}")

    print("\n--- Comparing with Day 22's in-process load test ---\n")
    service = RagService(Config())
    in_process_results = day22_load_test.run_load_test(service, num_requests=NUM_REQUESTS)
    print(f"In-process p50: {in_process_results['p50_ms']:.4f} ms")
    print(f"In-process p95: {in_process_results['p95_ms']:.4f} ms")

    print("\n=== Side by side ===")
    print(f"{'metric':<14}{'HTTP':<14}{'in-process':<14}")
    print(f"{'p50_ms':<14}{http_results['p50_ms']:<14.4f}{in_process_results['p50_ms']:<14.4f}")
    print(f"{'p95_ms':<14}{http_results['p95_ms']:<14.4f}{in_process_results['p95_ms']:<14.4f}")

    print(
        "\nWhy HTTP is slower: every HTTP request pays for a real TCP "
        "round trip, socket setup, and the http.server request parsing "
        "loop, on top of the exact same RagService work the in-process "
        "test measures directly. None of that network cost exists when "
        "the service is called as a plain Python method, which is why "
        "the HTTP numbers above should always be higher, even though both "
        "runs do the same underlying retrieval, ranking, and generation."
    )


if __name__ == "__main__":
    main()
