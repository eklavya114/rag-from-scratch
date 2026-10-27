"""
metrics_endpoint.py

Adds GET /metrics/prometheus on top of Day 23's api_server.py, WITHOUT
editing that file: a subclass overrides do_GET(), handles the one new
path itself, and falls back to the parent class's do_GET() for every
other path (/health, /metrics, anything else), the same
wrap-without-editing pattern instrumented_service.py used for RagService
itself.
"""

import json
import os
import sys
import threading
import urllib.request
from http.server import ThreadingHTTPServer

sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "day-22-production-rag"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "day-23-deployment"))

from api_server import RagRequestHandler, build_app_state  # Day 23
from config import Config  # Day 22
from health_and_metrics import ServiceMetrics  # Day 22

from instrumented_service import InstrumentedRagService


def build_instrumented_app_state():
    """
    Builds app state around the INSTRUMENTED service instead of the
    plain RagService, so /query (inherited from RagRequestHandler) now
    also records Prometheus-style metrics on every call. A real Day 22
    ServiceMetrics object is still included too: RagRequestHandler's
    inherited /query, /health, and /metrics handlers all expect
    app_state["metrics"] to be a real ServiceMetrics, and this keeps
    those paths working unmodified rather than only fixing the one new
    path this file actually adds.
    """
    config = Config()
    instrumented = InstrumentedRagService(config)
    return {"service": instrumented, "metrics": ServiceMetrics()}


class MetricsRequestHandler(RagRequestHandler):
    """Adds GET /metrics/prometheus. Every other GET and all POST handling falls straight through to RagRequestHandler, unchanged."""

    def do_GET(self):
        if self.path == "/metrics/prometheus":
            self._handle_prometheus_metrics()
        else:
            super().do_GET()

    def _handle_prometheus_metrics(self):
        """
        Returns the Prometheus text exposition format, the standard
        content type a real scraper (Prometheus itself, or any
        compatible tool) expects. This is served as PLAIN TEXT, not
        JSON, since that is the actual wire format the Prometheus
        ecosystem is built around.
        """
        instrumented = self.app_state["service"]
        body = instrumented.registry.render_prometheus().encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/plain; version=0.0.4")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def main():
    print("=== Metrics Endpoint ===\n")

    MetricsRequestHandler.app_state = build_instrumented_app_state()
    httpd = ThreadingHTTPServer(("127.0.0.1", 0), MetricsRequestHandler)
    port = httpd.server_port
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()

    base_url = f"http://127.0.0.1:{port}"
    print(f"Server started on {base_url}\n")

    try:
        print("--- Sending a few real queries first, so there is something to scrape ---")
        instrumented = MetricsRequestHandler.app_state["service"]
        for query_text in ["What is RAG?", "What is RAG?", "What is a vector database?"]:
            instrumented.query(query_text)
        print("3 queries sent (1 should be a cache hit).\n")

        print("--- A curl-style GET request, made from Python with urllib ---\n")
        request = urllib.request.Request(f"{base_url}/metrics/prometheus", method="GET")
        with urllib.request.urlopen(request, timeout=5) as response:
            print(f"status: {response.status}")
            print(f"content-type: {response.headers.get('Content-Type')}\n")
            print(response.read().decode("utf-8"))

        print("--- Confirming /health still works, unmodified from Day 23 ---")
        request = urllib.request.Request(f"{base_url}/health", method="GET")
        with urllib.request.urlopen(request, timeout=5) as response:
            print(f"status: {response.status}, body: {json.loads(response.read())}\n")

    finally:
        httpd.shutdown()
        httpd.server_close()
        print("Server shut down cleanly.")

    print(
        "\nWhy the scraper PULLS metrics instead of the service pushing "
        "them: a scraper that pulls on its own schedule controls its own "
        "load, visiting as many services as it wants at a pace it "
        "chooses, and a service that goes down simply stops responding "
        "to the next pull rather than needing to remember to push "
        "anything. A service pushing its own metrics out would need to "
        "know where every interested consumer lives, and would have no "
        "way to signal 'I am currently down' the moment it actually goes "
        "down, exactly the case a pull-based scraper notices immediately "
        "as a failed scrape."
    )


if __name__ == "__main__":
    main()
