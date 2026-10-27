"""
service_logging.py

Structured, JSON-formatted logging for every request, using the standard
library's logging module. A real production service never prints
freeform text, it emits structured lines a log aggregator can parse,
filter, and alert on. What gets logged here is chosen carefully: enough
to debug a real problem, never the full raw text a user typed, since a
query preview is useful for context while the full text is both
unnecessary for debugging most issues and a privacy risk to store.
"""

import json
import logging
import sys

logger = logging.getLogger("rag_service")
logger.setLevel(logging.INFO)
logger.propagate = False

if not logger.handlers:
    _handler = logging.StreamHandler(sys.stdout)
    _handler.setFormatter(logging.Formatter("%(message)s"))
    logger.addHandler(_handler)

QUERY_PREVIEW_LENGTH = 40


def _preview(text):
    """Returns a short preview of a query, never the full text, so logs stay useful without becoming a record of exactly what every user asked."""
    if len(text) <= QUERY_PREVIEW_LENGTH:
        return text
    return text[:QUERY_PREVIEW_LENGTH] + "..."


def log_request(request_id, cleaned_query, cache_hit, num_retrieved, top_doc_id, stage_timings_ms, status):
    """
    Logs one request as a single JSON line. This is what gets logged and
    why:
      - request_id: lets this exact request be found again in logs
      - a QUERY PREVIEW, not the full query: enough context to recognize
        the request, without storing a full record of user text
      - cache_hit: whether any work was actually skipped
      - num_retrieved / top_doc_id: what the retrieval stage actually found
      - stage_timings_ms: where time was spent, per stage
      - status: the final outcome (ok, rejected, no_results, error)
    """
    log_line = {
        "request_id": request_id,
        "query_preview": _preview(cleaned_query) if cleaned_query else None,
        "cache_hit": cache_hit,
        "num_retrieved": num_retrieved,
        "top_doc_id": top_doc_id,
        "stage_timings_ms": stage_timings_ms,
        "status": status,
    }
    logger.info(json.dumps(log_line))


def main():
    print("=== Service Logging ===\n")

    print("--- A normal, successful request ---")
    log_request(
        request_id="req-001",
        cleaned_query="What is RAG and why does it matter for building real systems?",
        cache_hit=False,
        num_retrieved=3,
        top_doc_id=2,
        stage_timings_ms={"validate": 0.01, "preprocess": 0.05, "retrieve": 1.2, "rank": 0.3, "generate": 0.4},
        status="ok",
    )

    print("\n--- A cache hit (short query, no stage timings needed) ---")
    log_request(
        request_id="req-002",
        cleaned_query="What is RAG?",
        cache_hit=True,
        num_retrieved=3,
        top_doc_id=2,
        stage_timings_ms={"validate": 0.01, "cache_check": 0.02},
        status="ok",
    )

    print("\n--- A rejected request ---")
    log_request(
        request_id="req-003",
        cleaned_query=None,
        cache_hit=False,
        num_retrieved=0,
        top_doc_id=None,
        stage_timings_ms={"validate": 0.01},
        status="rejected",
    )

    print(
        "\nWhat is safe and useful to log: request_id, cache_hit, retrieval "
        "counts, timings, and status are all useful for debugging and "
        "contain nothing private. query_preview gives enough context to "
        "recognize what kind of question came in, truncated so the full "
        "text of what a user typed is never stored. The full raw query is "
        "deliberately left out of every log line above."
    )


if __name__ == "__main__":
    main()
