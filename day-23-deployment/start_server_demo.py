"""
start_server_demo.py

Starts api_server.py in a background thread, on a port the OS picks
(port 0), and talks to it with real HTTP requests over urllib.request,
the exact same library any plain Python client would use. This is the
server being tested from the OUTSIDE, as a real client would see it,
not by calling its handler methods directly in-process.
"""

import json
import os
import sys
import threading
import urllib.error
import urllib.request
from http.server import ThreadingHTTPServer

sys.path.insert(0, os.path.dirname(__file__))
from api_server import RagRequestHandler, build_app_state


def start_background_server():
    """
    Starts the server on a free port (port 0 tells the OS to pick one)
    in a daemon thread, so it never blocks the rest of the script and
    gets cleaned up automatically if the process exits unexpectedly.
    Returns the running server and its actual bound port.
    """
    RagRequestHandler.app_state = build_app_state()
    httpd = ThreadingHTTPServer(("127.0.0.1", 0), RagRequestHandler)
    port = httpd.server_port

    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()

    return httpd, port


def send_request(method, url, body=None, headers=None):
    """
    Sends one real HTTP request over the wire using only the standard
    library, and returns (status_code, parsed_body_or_raw_text). On the
    wire: a request line (method, path, HTTP version), headers, and an
    optional body get written to a socket; the server reads that same
    socket, parses it back into a request, and writes a response in the
    same shape back.
    """
    data = json.dumps(body).encode("utf-8") if body is not None else None
    request = urllib.request.Request(url, data=data, method=method, headers=headers or {})

    try:
        with urllib.request.urlopen(request, timeout=5) as response:
            raw = response.read()
            try:
                return response.status, json.loads(raw)
            except json.JSONDecodeError:
                return response.status, raw.decode("utf-8", errors="replace")
    except urllib.error.HTTPError as e:
        # A non-2xx response still has a readable body; urllib raises it
        # as an exception instead of returning it, so we unwrap it here.
        raw = e.read()
        try:
            return e.code, json.loads(raw)
        except json.JSONDecodeError:
            return e.code, raw.decode("utf-8", errors="replace")


def preview(value, max_length=120):
    text = json.dumps(value) if not isinstance(value, str) else value
    return text if len(text) <= max_length else text[:max_length] + "..."


def main():
    print("=== Start Server Demo ===\n")

    httpd, port = start_background_server()
    base_url = f"http://127.0.0.1:{port}"
    print(f"Server started on {base_url}\n")

    try:
        print("--- A valid query ---")
        status, body = send_request("POST", f"{base_url}/query", body={"query": "What is RAG?"})
        print(f"status: {status}, body: {preview(body)}\n")

        print("--- An empty query (should be rejected) ---")
        status, body = send_request("POST", f"{base_url}/query", body={"query": ""})
        print(f"status: {status}, body: {preview(body)}\n")

        print("--- Bad JSON ---")
        data = b"{not valid json"
        request = urllib.request.Request(f"{base_url}/query", data=data, method="POST")
        try:
            with urllib.request.urlopen(request, timeout=5) as response:
                print(f"status: {response.status}")
        except urllib.error.HTTPError as e:
            raw = e.read()
            print(f"status: {e.code}, body: {preview(json.loads(raw))}\n")

        print("--- An unknown path ---")
        status, body = send_request("GET", f"{base_url}/does-not-exist")
        print(f"status: {status}, body: {preview(body)}\n")

        print("--- GET /health ---")
        status, body = send_request("GET", f"{base_url}/health")
        print(f"status: {status}, body: {preview(body)}\n")

    finally:
        httpd.shutdown()
        httpd.server_close()
        print("Server shut down cleanly.")

    print(
        "\nWhat happened on the wire: every request above opened a real "
        "TCP connection to 127.0.0.1, wrote an HTTP request line and "
        "headers, and read back a real HTTP response, exactly like a "
        "client in any language would. The only difference from a real "
        "deployment is that the server happens to be running on the same "
        "machine, on a port chosen by the OS instead of a fixed one."
    )


if __name__ == "__main__":
    main()
