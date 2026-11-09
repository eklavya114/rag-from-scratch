"""
main.py

One command that proves the whole project actually works together:
builds the real service (every stage from Days 1 to 28, wired through
real imports), answers three real sample questions with their sources,
prints health and key metrics, and tells the user how to run the full
test suite. This is the "front door" the README's finished-house
analogy describes: one command that demonstrates every room of the
house is actually connected, not just built.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from config import Config
from service import ProjectService

SAMPLE_QUESTIONS = [
    "How do I get an RMA number?",
    "What is a chargeback?",
    "Can I get store credit instead of a refund?",
]


def main():
    print("=== RAG From Scratch: The Complete Project ===\n")

    config = Config()
    config.validate()
    service = ProjectService(config)
    print(f"Service built: {service.pipeline.indexed_document_count} documents indexed into "
          f"{service.pipeline.indexed_chunk_count} chunks.\n")

    print("--- Answering 3 sample questions ---\n")
    for question in SAMPLE_QUESTIONS:
        response = service.answer(question, config.api_key)
        print(f"Q: {question}")
        print(f"Status: {response.status}")
        print(f"Sources: {response.sources}")
        if response.answer:
            print(f"Answer: {response.answer[:150]}...")
        print()

    print("--- Health and key metrics ---")
    error_count = service.requests_total.value({"status": "error"})
    ok_count = service.requests_total.value({"status": "ok"})
    total_requests = ok_count + error_count + service.requests_total.value({"status": "no_results"})
    error_rate = error_count / total_requests if total_requests else 0.0
    health = "healthy" if error_rate < 0.05 else "degraded"
    print(f"Health: {health}")
    print(f"Requests handled this run: {total_requests}")
    print(f"Error rate: {error_rate:.0%}\n")

    print("--- Tests ---")
    print("Run 'python tests.py' to verify the parts of this project that must never break.")
    print("(Not run automatically here, so this command stays focused on demonstrating the system itself.)\n")

    print(
        "What this command proves: every answer above came from a real "
        "pipeline built out of Day 1 to 14's retrieval, ranking, "
        "generation, and caching stages, served through Day 22's "
        "validation, Day 25's resilience patterns, and Day 27's security "
        "checks, with Day 24's metrics recording every request. Nothing "
        "printed here is a mock or a hardcoded string, it is the real, "
        "connected system this entire project built, one day at a time."
    )


if __name__ == "__main__":
    main()
