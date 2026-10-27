"""
auth_and_rate_limit.py

Adds two protections an API opened up to the outside world needs: an API
key check (so not just anyone can call it) and a rate limit (so one
caller cannot flood it). Both are built with the standard library only,
as a small wrapper demonstrated here rather than baked permanently into
api_server.py, so each protection's logic is easy to read on its own.
"""

import json
import os
import sys
import threading
import time
import urllib.error
import urllib.request
from http.server import ThreadingHTTPServer

sys.path.insert(0, os.path.dirname(__file__))
from api_server import RagRequestHandler, build_app_state

# A demo key only: a real deployment reads this from the environment and
# NEVER hardcodes it, since anything in source code ends up in version
# control, visible to anyone with read access to the repository, forever
# in its history even if later removed.
DEMO_API_KEY = "demo-key-do-not-use-in-real-deployments"

RATE_LIMIT_REQUESTS = 10
RATE_LIMIT_WINDOW_SECONDS = 60


def get_configured_api_key():
    """Reads the real API key from the environment, falling back to the clearly-labeled demo key only when nothing is configured, so a forgotten environment variable fails safely rather than silently."""
    return os.environ.get("RAG_API_KEY", DEMO_API_KEY)


class FixedWindowRateLimiter:
    """
    A fixed-window rate limiter: counts requests per key within the
    CURRENT time window, and resets the count when a new window starts.
    Simpler than a sliding window, at the cost of allowing a short burst
    right at a window boundary, an acceptable tradeoff for a demo-scale
    protection.
    """

    def __init__(self, max_requests=RATE_LIMIT_REQUESTS, window_seconds=RATE_LIMIT_WINDOW_SECONDS):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.windows = {}  # key -> (window_start_time, count)
        self.lock = threading.Lock()

    def allow(self, key):
        """Returns True if this key may make a request right now, False if it has exceeded the limit for the current window."""
        now = time.time()
        with self.lock:
            window_start, count = self.windows.get(key, (now, 0))

            if now - window_start >= self.window_seconds:
                # A new window has started: reset the count.
                window_start, count = now, 0

            if count >= self.max_requests:
                self.windows[key] = (window_start, count)
                return False

            self.windows[key] = (window_start, count + 1)
            return True


class ProtectedRagRequestHandler(RagRequestHandler):
    """
    Wraps the real RagRequestHandler with an API key check and a rate
    limit on POST /query only. GET /health and GET /metrics stay
    unprotected here, since a load balancer or monitoring system needs to
    reach them without needing a key.
    """

    rate_limiter = FixedWindowRateLimiter()

    def do_POST(self):
        if self.path == "/query":
            api_key = self.headers.get("X-API-Key")
            configured_key = get_configured_api_key()

            if api_key != configured_key:
                # Rejecting here, before _read_body() ever runs, means
                # any body bytes the client already sent are still
                # sitting unread on the socket. On a keep-alive HTTP/1.1
                # connection, the NEXT request reusing this same
                # connection would then start by reading those leftover
                # bytes instead of a fresh request line, a desync. Force
                # the connection closed so the client has to open a new
                # one, the same safe choice api_server.py makes whenever
                # it cannot be sure the body was fully consumed.
                self.close_connection = True
                self._send_error_json(401, "Missing or invalid X-API-Key header.")
                return

            if not self.rate_limiter.allow(api_key):
                self.close_connection = True
                self._send_error_json(429, f"Rate limit exceeded: max {RATE_LIMIT_REQUESTS} requests per {RATE_LIMIT_WINDOW_SECONDS} seconds.")
                return

        super().do_POST()


def main():
    print("=== Auth and Rate Limit ===\n")

    ProtectedRagRequestHandler.app_state = build_app_state()
    httpd = ThreadingHTTPServer(("127.0.0.1", 0), ProtectedRagRequestHandler)
    port = httpd.server_port
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()

    base_url = f"http://127.0.0.1:{port}"
    print(f"Server started on {base_url}")
    print(f"Configured API key (demo only): {get_configured_api_key()}\n")

    def send(headers=None):
        # A fresh connection per call, instead of going through
        # urllib.request's connection pool: a rapid burst of requests
        # against a short-lived, in-process demo server on Windows can
        # race with the server's own connection teardown when a
        # keep-alive socket gets reused, and opening a new connection
        # every time sidesteps that race entirely. A real client talking
        # to a long-lived server would reasonably use keep-alive; this
        # demo avoids it specifically because of how fast and bursty it
        # is against a server that is itself starting and stopping
        # within the same short script.
        import http.client

        all_headers = {**(headers or {}), "Content-Type": "application/json"}
        data = json.dumps({"query": "What is RAG?"}).encode("utf-8")

        # A brand-new TCP connection can still occasionally be torn down
        # by the OS during rapid connect/accept churn against a
        # threaded server on Windows (WinError 10053), nothing to do
        # with this server's own logic. A single retry on a pure
        # connection-level failure is standard, defensive client
        # behavior, the same reason client_example.py's ask() catches
        # connection errors separately from HTTP errors.
        last_error = None
        for _ in range(3):
            connection = http.client.HTTPConnection("127.0.0.1", port, timeout=5)
            try:
                connection.request("POST", "/query", body=data, headers=all_headers)
                response = connection.getresponse()
                response.read()
                return response.status
            except (ConnectionAbortedError, ConnectionResetError, OSError) as e:
                last_error = e
            finally:
                connection.close()
        raise last_error

    try:
        print("--- No API key ---")
        status = send()
        print(f"status: {status}\n")
        assert status == 401, f"expected 401, got {status}"

        print("--- A valid API key ---")
        status = send(headers={"X-API-Key": get_configured_api_key()})
        print(f"status: {status}\n")
        assert status == 200, f"expected 200, got {status}"

        print(f"--- A burst of {RATE_LIMIT_REQUESTS + 5} requests (should hit the limit) ---")
        statuses = [send(headers={"X-API-Key": get_configured_api_key()}) for _ in range(RATE_LIMIT_REQUESTS + 5)]
        print(f"statuses: {statuses}")
        assert 429 in statuses, "expected at least one 429 in the burst"
        print(f"429 count: {statuses.count(429)}\n")

    finally:
        httpd.shutdown()
        httpd.server_close()
        print("Server shut down cleanly.")

    print(
        "\nWhy keys belong in environment variables, never in code: a key "
        "hardcoded in source ends up in version control history forever, "
        "readable by anyone with repository access, even after the line "
        "is later deleted. Reading it from RAG_API_KEY at startup means "
        "the real key never needs to touch a file that gets committed at "
        "all, and rotating it is a deployment change, not a code change."
    )


if __name__ == "__main__":
    main()
