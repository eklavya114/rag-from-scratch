"""
secure_api_check.py

A security checklist run against the REAL Day 23 API, started on a real
localhost port. Not a one-off manual check: a short, repeatable table of
PASS/FAIL results, the same discipline Day 25's failure_matrix.py
applied to failure modes, applied here to security properties instead.
Running this on every release is what catches a regression (an endpoint
that used to require a key and no longer does) before it reaches real
users, instead of relying on someone remembering to check by hand.
"""

import io
import json
import os
import sys
import threading
import urllib.error
import urllib.request
from http.server import ThreadingHTTPServer

if hasattr(sys.stdout, "buffer"):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "day-23-deployment"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "day-22-production-rag"))

from api_server import build_app_state  # Day 23
from auth_and_rate_limit import ProtectedRagRequestHandler, get_configured_api_key  # Day 23

READER_KEY = "reader-demo-key"
ADMIN_KEY = get_configured_api_key()  # the valid key ProtectedRagRequestHandler already checks against


class RoleAwareRequestHandler(ProtectedRagRequestHandler):
    """Adds a minimal admin-only route on top of Day 23's key check, so this checklist has a real role-gated endpoint to test, not just the plain key check."""

    def do_GET(self):
        if self.path == "/admin/metrics":
            api_key = self.headers.get("X-API-Key")
            if api_key != ADMIN_KEY:
                self._send_error_json(403, "This route requires the admin role.")
                return
            self._send_json(200, {"admin_metrics": "ok"})
        else:
            super().do_GET()


def send(method, path, base_url, headers=None, body=None):
    """Sends one real HTTP request and returns (status_code, body_text), catching HTTPError so a non-2xx response is still inspectable."""
    data = json.dumps(body).encode("utf-8") if body is not None else None
    request = urllib.request.Request(f"{base_url}{path}", data=data, method=method, headers=headers or {})
    try:
        with urllib.request.urlopen(request, timeout=5) as response:
            return response.status, response.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8", errors="replace")


def run_checks(base_url):
    """Runs every security check and returns a list of result rows, each with a name, expected outcome, actual outcome, and PASS/FAIL."""
    checks = []

    status, body = send("POST", "/query", base_url, body={"query": "What is RAG?"})
    checks.append(("Missing API key returns 401", 401, status, body))

    status, body = send("POST", "/query", base_url, headers={"X-API-Key": "totally-wrong-key"}, body={"query": "What is RAG?"})
    checks.append(("Wrong API key returns 401", 401, status, body))

    status, body = send("GET", "/admin/metrics", base_url, headers={"X-API-Key": READER_KEY})
    checks.append(("Admin route blocked for reader key", 403, status, body))

    status, body = send("GET", "/admin/metrics", base_url, headers={"X-API-Key": ADMIN_KEY})
    checks.append(("Admin route allowed for admin key", 200, status, body))

    oversized_body = json.dumps({"query": "x" * 20_000}).encode("utf-8")
    request = urllib.request.Request(f"{base_url}/query", data=oversized_body, method="POST", headers={"X-API-Key": ADMIN_KEY})
    try:
        with urllib.request.urlopen(request, timeout=5) as response:
            status, body = response.status, response.read().decode()
    except urllib.error.HTTPError as e:
        status, body = e.code, e.read().decode()
    checks.append(("Oversized body returns 413", 413, status, body))

    status, body = send("GET", "/does-not-exist", base_url)
    checks.append(("Unknown path returns 404", 404, status, body))

    status, body = send("POST", "/query", base_url, headers={"X-API-Key": ADMIN_KEY}, body={"query": ""})
    no_stack_trace = "Traceback" not in body and "File \"" not in body
    checks.append(("Error response has no stack trace", True, no_stack_trace, body))

    return checks


def main():
    print("=== Secure API Check ===\n")

    RoleAwareRequestHandler.app_state = build_app_state()
    httpd = ThreadingHTTPServer(("127.0.0.1", 0), RoleAwareRequestHandler)
    port = httpd.server_port
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    base_url = f"http://127.0.0.1:{port}"
    print(f"Server started on {base_url}\n")

    try:
        checks = run_checks(base_url)
    finally:
        httpd.shutdown()
        httpd.server_close()

    print(f"{'check':<42}{'expected':<12}{'actual':<12}{'result':<8}")
    print("-" * 74)
    passed_count = 0
    for name, expected, actual, body in checks:
        passed = expected == actual
        passed_count += passed
        print(f"{name:<42}{str(expected):<12}{str(actual):<12}{'PASS' if passed else 'FAIL':<8}")

    print(f"\n{passed_count} of {len(checks)} checks passed.")
    print("\nServer shut down cleanly.")

    print(
        "\nWhy a checklist runs on every release: any one of these "
        "checks could silently stop being true after an unrelated code "
        "change, a refactor that accidentally skips the key check on a "
        "new route, a new error path that forgets to catch an exception "
        "safely. Running the full table against the REAL running server, "
        "not just reading the code and assuming it still behaves "
        "correctly, is what catches that kind of regression automatically, "
        "the same guarantee a unit test suite gives for correctness, "
        "applied here to security properties specifically."
    )


if __name__ == "__main__":
    main()
