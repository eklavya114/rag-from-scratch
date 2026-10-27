"""
request_validation.py

Validates a request before any real work happens: no embedding, no
retrieval, no ranking, nothing, until the input itself is confirmed to be
reasonable. Failing early and cheaply matters because validation is
nearly free, while retrieval and generation are not. A bad request that
slips past validation wastes real work on something that was never going
to produce a usable answer anyway.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from config import Config


def validate_request(raw_query, config):
    """
    Checks a raw query against the rules every request must satisfy:
    it must be a string, it must not be empty or whitespace-only, and it
    must not exceed the configured maximum length. Returns a small result
    object instead of raising, so the caller can handle a bad request as
    data, not as an exception to catch.
    """
    if not isinstance(raw_query, str):
        return {"ok": False, "cleaned_query": None, "error": f"Query must be a string, got {type(raw_query).__name__}."}

    stripped = raw_query.strip()

    if not stripped:
        return {"ok": False, "cleaned_query": None, "error": "Query cannot be empty or whitespace-only."}

    if len(stripped) > config.max_query_length:
        return {
            "ok": False,
            "cleaned_query": None,
            "error": f"Query is {len(stripped)} characters, which exceeds the limit of {config.max_query_length}.",
        }

    return {"ok": True, "cleaned_query": stripped, "error": None}


def main():
    print("=== Request Validation ===\n")

    config = Config()
    config.validate()

    print("--- A valid request ---")
    result = validate_request("What is RAG?", config)
    print(result)

    print("\n--- Bad request: empty string ---")
    print(validate_request("", config))

    print("\n--- Bad request: whitespace only ---")
    print(validate_request("     ", config))

    print("\n--- Bad request: too long ---")
    too_long = "What is RAG? " * 50
    result = validate_request(too_long, config)
    print(f"Length: {len(too_long.strip())}, result: {result}")

    print("\n--- Bad request: non-string input ---")
    print(validate_request(12345, config))

    print(
        "\nWhy failing early and cheaply matters: every check above runs "
        "in microseconds and touches no index, no embedding function, and "
        "no generator. Catching a bad request here means retrieval, "
        "ranking, and generation never even start for input that was "
        "always going to fail, which keeps the expensive part of the "
        "pipeline reserved for requests that actually deserve it."
    )


if __name__ == "__main__":
    main()
