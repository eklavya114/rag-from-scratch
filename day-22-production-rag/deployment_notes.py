"""
deployment_notes.py

This file is for reading, nothing here needs to run. It explains, as
plain text, how RagService could be wrapped as an HTTP API, how
configuration and secrets would be handled in a real deployment, and
what to monitor once it is live. None of the code blocks below are
executed anywhere in this project. There is no API key or vendor SDK
anywhere in this project, including here: this is a description of how a
real deployment would look, not a runnable integration.
"""

WRAPPING_AS_AN_HTTP_API = """
WRAPPING RagService AS AN HTTP API (text only, not executed)

RagService already has the right shape for this: one object built once
at startup, one method that takes a string and returns a response. Both
FastAPI and the standard library's http.server can wrap it with very
little extra code.

Using FastAPI (illustrative only):

    from fastapi import FastAPI
    from rag_service import RagService
    from config import Config

    app = FastAPI()
    service = RagService(Config())

    @app.post("/query")
    def handle_query(payload: dict):
        response = service.query(payload.get("query", ""))
        return {
            "request_id": response.request_id,
            "status": response.status,
            "answer": response.answer,
            "sources": response.sources,
            "cache_hit": response.cache_hit,
        }

Using only the standard library's http.server (illustrative only):

    from http.server import BaseHTTPRequestHandler, HTTPServer
    import json
    from rag_service import RagService
    from config import Config

    service = RagService(Config())

    class Handler(BaseHTTPRequestHandler):
        def do_POST(self):
            length = int(self.headers["Content-Length"])
            body = json.loads(self.rfile.read(length))
            response = service.query(body.get("query", ""))
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({
                "status": response.status,
                "answer": response.answer,
            }).encode())

In both cases, RagService itself does not change. It was built with one
query() entry point specifically so wrapping it in a web framework is a
thin layer on top, not a rewrite.
"""

ENVIRONMENT_VARIABLES = """
ENVIRONMENT VARIABLES FOR CONFIG AND SECRETS

Config values that are safe to vary between environments (development,
staging, production) without being secret belong in environment
variables, read once at startup and used to build a Config object:

    RAG_TOP_K=3
    RAG_CACHE_SIZE=100
    RAG_MAX_QUERY_LENGTH=500

A real deployment that calls an actual LLM API would also need an API
key. That key never belongs in source code, never gets committed to
version control, and never gets logged. It would be read from an
environment variable or a secrets manager at startup, for example:

    ANTHROPIC_API_KEY=... (read at startup, never hardcoded, never logged)

This project intentionally has no API key anywhere, since every stage
here runs on the toy, offline components built across Days 1 to 21. This
section describes where a real key WOULD live in a real deployment, it
is not instructing this project to add one.
"""

WHAT_TO_MONITOR = """
WHAT TO MONITOR AFTER DEPLOYING

- Error rate, the same number health_and_metrics.py already tracks:
  alert immediately if it crosses into "unhealthy," investigate if it
  sits in "degraded" for more than a few minutes.
- p95 and p99 latency per stage, so a slowdown can be traced to the exact
  stage responsible (retrieval, ranking, generation) instead of a vague
  "the service feels slow" report.
- Cache hit rate, since a sudden drop usually means either traffic
  patterns changed or the cache itself is misbehaving.
- Request volume, since a sudden drop can mean upstream traffic stopped
  reaching the service at all, which an error rate metric alone would
  never catch, since zero requests also means zero errors.
- The evaluation_hook.py quality metrics, run on a schedule against a
  fixed labeled set, not just once at launch, so a quality regression
  introduced by a later change gets caught before many real users see it.
"""


def main():
    print("=== Deployment Notes (reading material, nothing here runs) ===\n")
    print(WRAPPING_AS_AN_HTTP_API)
    print(ENVIRONMENT_VARIABLES)
    print(WHAT_TO_MONITOR)


if __name__ == "__main__":
    main()
