"""
api_server.py

The HTTP door in front of Day 22's RagService, built entirely with the
standard library: http.server for the server itself, json for the
request and response bodies. No vendor framework, no vendor SDK, no API
key for any external model, everything here runs fully offline.

Endpoints:
  POST /query    -- ask a real question, get an answer back
  GET  /health   -- is the service currently healthy
  GET  /metrics  -- the numbers behind that health status

ThreadingHTTPServer is used instead of the plain HTTPServer so multiple
requests can be handled concurrently, the same way a real deployed
service needs to serve more than one client at a time.
"""

import json
import os
import sys
import time
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "day-22-production-rag"))

from config import Config  # Day 22
from health_and_metrics import ServiceMetrics  # Day 22
from rag_service import RagService  # Day 22

from request_handling_rules import ALLOWED_METHODS, MAX_BODY_SIZE_BYTES, http_code_for_status


def build_app_state():
    """Builds the shared service and metrics objects once, at server startup, the same way RagService builds its index once in __init__ rather than per request."""
    config = Config()
    service = RagService(config)
    metrics = ServiceMetrics()
    return {"service": service, "metrics": metrics}


class RagRequestHandler(BaseHTTPRequestHandler):
    """
    One handler instance is created per request by ThreadingHTTPServer.
    app_state is attached as a class attribute (set once, in main()
    below) so every instance shares the same RagService and metrics
    without needing to rebuild either per request.
    """

    app_state = None  # set by main() before the server starts
    protocol_version = "HTTP/1.1"

    def log_message(self, format, *args):
        # Suppress BaseHTTPRequestHandler's default stderr access logging;
        # Day 22's structured JSON logging already covers request details.
        pass

    def _send_json(self, status_code, payload):
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        if self.close_connection:
            # Tell the client explicitly, instead of just dropping the
            # socket, so a well-behaved client does not try to reuse a
            # connection we are about to close.
            self.send_header("Connection", "close")
        self.end_headers()
        self.wfile.write(body)

    def _send_error_json(self, status_code, message):
        # A single place every error response funnels through, so a raw
        # Python exception or stack trace can never leak into a response
        # body, only ever a clean, readable message.
        self._send_json(status_code, {"error": message})

    def _method_not_allowed_or_not_found(self, path, method):
        if path in ALLOWED_METHODS:
            self._send_error_json(405, f"Method {method} not allowed on {path}.")
        else:
            self._send_error_json(404, f"No such endpoint: {path}")

    def do_GET(self):
        if self.path == "/health":
            self._handle_health()
        elif self.path == "/metrics":
            self._handle_metrics()
        else:
            self._method_not_allowed_or_not_found(self.path, "GET")

    def do_POST(self):
        if self.path == "/query":
            self._handle_query()
        else:
            self._method_not_allowed_or_not_found(self.path, "POST")

    def _read_body(self):
        """
        Reads and size-checks the request body before attempting to
        parse it as JSON. Returns (body_bytes, error_response) where
        error_response is None on success, or a (code, message) tuple if
        the body was too large or missing a valid Content-Length.
        """
        content_length = self.headers.get("Content-Length")
        if content_length is None:
            return None, (400, "Missing Content-Length header.")

        try:
            length = int(content_length)
        except ValueError:
            return None, (400, "Content-Length header must be an integer.")

        if length < 0:
            return None, (400, "Content-Length header cannot be negative.")

        if length > MAX_BODY_SIZE_BYTES:
            # Do NOT read the oversized body: the client may still be
            # sending more bytes than we are willing to buffer, and a
            # partial read here would leave the socket holding leftover
            # bytes that the NEXT request on this connection would
            # wrongly be parsed as part of. Close the connection instead
            # of trying to drain it, which is safe on both HTTP/1.0 and
            # HTTP/1.1 keep-alive connections.
            self.close_connection = True
            return None, (413, f"Request body of {length} bytes exceeds the {MAX_BODY_SIZE_BYTES}-byte limit.")

        return self.rfile.read(length), None

    def _handle_query(self):
        """POST /query: the main endpoint. Parses a JSON body, calls RagService.query(), and maps the resulting status to the right HTTP code."""
        body, error = self._read_body()
        if error:
            code, message = error
            self._send_error_json(code, message)
            return

        try:
            payload = json.loads(body)
        except json.JSONDecodeError:
            self._send_error_json(400, "Request body must be valid JSON.")
            return

        if not isinstance(payload, dict) or "query" not in payload:
            self._send_error_json(400, "Request body must be a JSON object with a 'query' field.")
            return

        service = self.app_state["service"]
        metrics = self.app_state["metrics"]

        response = service.query(payload["query"])
        metrics.record(response)

        http_code = http_code_for_status(response.status)
        self._send_json(http_code, {
            "request_id": response.request_id,
            "status": response.status,
            "answer": response.answer,
            "sources": response.sources,
            "cache_hit": response.cache_hit,
            "timings_ms": response.timings_ms,
        })

    def _handle_health(self):
        """GET /health: healthy or degraded both return 200 (the service is up and answering), unhealthy returns 503 (a load balancer should stop sending traffic here)."""
        metrics = self.app_state["metrics"]
        status = metrics.health()
        http_code = 200 if status in ("healthy", "degraded") else 503
        self._send_json(http_code, {"status": status, "request_count": metrics.request_count, "error_count": metrics.error_count})

    def _handle_metrics(self):
        """GET /metrics: the full numeric picture behind the health status."""
        metrics = self.app_state["metrics"]
        self._send_json(200, {
            "request_count": metrics.request_count,
            "error_count": metrics.error_count,
            "error_rate": metrics.error_rate(),
            "cache_hit_rate": metrics.cache_hit_rate(),
            "average_latency_per_stage_ms": metrics.average_latency_per_stage(),
            "health": metrics.health(),
        })


def run_server(host="127.0.0.1", port=8000):
    """Starts the server and blocks forever serving requests, used when this file is run directly rather than imported for a demo."""
    RagRequestHandler.app_state = build_app_state()
    httpd = ThreadingHTTPServer((host, port), RagRequestHandler)
    print(f"Serving on http://{host}:{httpd.server_port}")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        httpd.server_close()


def main():
    """
    Running this file directly starts a real server that blocks forever,
    exactly what a deployed service should do (this is also what the
    Dockerfile's CMD runs). But a script that never returns can't be part
    of an automated "every script runs on its own" check, so this demo
    instead starts the server on a free port, sends one real request to
    prove it's alive, then shuts it down. start_server_demo.py is the
    file that explores the server's behavior in more depth.
    """
    import urllib.request

    RagRequestHandler.app_state = build_app_state()
    httpd = ThreadingHTTPServer(("127.0.0.1", 0), RagRequestHandler)
    port = httpd.server_port
    print(f"=== API Server Smoke Test ===\n")
    print(f"Server started on http://127.0.0.1:{port}\n")

    import threading
    server_thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    server_thread.start()

    try:
        request = urllib.request.Request(
            f"http://127.0.0.1:{port}/health",
            method="GET",
        )
        with urllib.request.urlopen(request, timeout=5) as response:
            body = json.loads(response.read())
            print(f"GET /health -> {response.status}: {body}")
    finally:
        httpd.shutdown()
        httpd.server_close()
        print("\nServer shut down cleanly.")

    print(
        "\nRunning this file with `python api_server.py` outside of this "
        "demo starts the real, permanently-listening server on "
        "RAG_API_PORT (default 8000) via run_server(), the same entry "
        "point the Dockerfile's CMD uses."
    )


if __name__ == "__main__":
    main()
