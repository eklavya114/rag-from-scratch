"""
safe_logging_v2.py

Wraps Day 22's service_logging.py, WITHOUT editing that file, so every
log line goes through pii_redaction.py first. Logs are one of the most
common places data actually leaks: a log aggregator often has far looser
access controls than the production database it is supposedly less
sensitive than, and a log line, once written, tends to sit around for a
long time, copied into backups, shipped to a third-party log service,
grepped by anyone debugging an unrelated issue. Day 22 already avoided
logging full raw query text. This file adds a second layer: redact
whatever DOES get logged, and never log a secret at all, regardless of
where it appears.
"""

import json
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "day-22-production-rag"))

from service_logging import QUERY_PREVIEW_LENGTH, logger  # Day 22, reusing the same configured logger

from pii_redaction import redact_text

SENSITIVE_HEADER_NAMES = {"authorization", "x-api-key"}


def safe_preview(text):
    """A short preview, redacted first, so personal data never even makes it INTO the preview, let alone the full log line."""
    redacted, _ = redact_text(text)
    if len(redacted) <= QUERY_PREVIEW_LENGTH:
        return redacted
    return redacted[:QUERY_PREVIEW_LENGTH] + "..."


def safe_headers_summary(headers):
    """
    Returns a dict of header names only, NEVER their values, for any
    header considered sensitive (Authorization, X-API-Key). Logging
    header names is useful for debugging (did the client even send a
    key). Logging header VALUES, even accidentally, is the single most
    common way secrets leak through logs.
    """
    summary = {}
    for name, value in headers.items():
        if name.lower() in SENSITIVE_HEADER_NAMES:
            summary[name] = "[REDACTED]"
        else:
            summary[name] = value
    return summary


def log_request_safely(request_id, cleaned_query, cache_hit, num_retrieved, top_doc_id, stage_timings_ms, status, headers=None):
    """
    The safe replacement for Day 22's log_request(): redacts the query
    preview through pii_redaction.py, and redacts any sensitive header
    VALUES before including header names in the log line at all.
    """
    log_line = {
        "request_id": request_id,
        "query_preview": safe_preview(cleaned_query) if cleaned_query else None,
        "headers": safe_headers_summary(headers) if headers else {},
        "cache_hit": cache_hit,
        "num_retrieved": num_retrieved,
        "top_doc_id": top_doc_id,
        "stage_timings_ms": stage_timings_ms,
        "status": status,
    }
    logger.info(json.dumps(log_line))


def main():
    print("=== Safe Logging v2 ===\n")

    print("--- A request carrying a fake API key and an email in the query ---\n")
    fake_headers = {
        "Authorization": "Bearer sk-fake-secret-abc123",
        "X-API-Key": "demo-key-do-not-use-in-real-deployments",
        "Content-Type": "application/json",
    }
    query_with_pii = "My email is jane.doe@example.com, please help."

    log_request_safely(
        request_id="req-100",
        cleaned_query=query_with_pii,
        cache_hit=False,
        num_retrieved=2,
        top_doc_id=2,
        stage_timings_ms={"validate": 0.01, "retrieve": 0.4},
        status="ok",
        headers=fake_headers,
    )

    print(
        "\nWhat happened above: the raw Authorization and X-API-Key "
        "header VALUES never appear anywhere in that log line, only the "
        "fact that those headers were present. The email address in the "
        "query never appears either, redact_text() replaced it with "
        "[EMAIL] before the preview was even built. Compare this to Day "
        "22's plain log_request(): logging the full header dict or the "
        "full raw query there would have written both the fake secret "
        "and a real person's email straight into the log file."
    )


if __name__ == "__main__":
    main()
