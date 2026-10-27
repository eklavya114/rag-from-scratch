"""
client_example.py

A small, copyable client for anyone who wants to call this API from
plain Python, no special library required. ask() handles the two kinds
of failure a client has to plan for separately: the server responding
with an error (HTTP errors), and the server never responding at all
(connection errors, including a timeout). Both get turned into a
readable message instead of an unhandled exception.
"""

import json
import os
import sys
import urllib.error
import urllib.request

sys.path.insert(0, os.path.dirname(__file__))

DEFAULT_TIMEOUT_SECONDS = 5


def ask(question, base_url, timeout=DEFAULT_TIMEOUT_SECONDS):
    """
    Sends one question to POST /query and returns the parsed JSON
    response. A real client should ALWAYS set a timeout: without one, a
    server that hangs (network trouble, an overloaded backend) would
    block this call forever instead of failing in a bounded amount of
    time. Returns a dict either way: either the real response, or a
    small {"error": "..."} dict describing what went wrong, so callers
    never need to wrap every call in their own try/except.
    """
    data = json.dumps({"query": question}).encode("utf-8")
    request = urllib.request.Request(
        f"{base_url}/query",
        data=data,
        method="POST",
        headers={"Content-Type": "application/json"},
    )

    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return json.loads(response.read())
    except urllib.error.HTTPError as e:
        # The server responded, but with an error status (4xx or 5xx).
        # Its body is still readable JSON describing what went wrong.
        try:
            return json.loads(e.read())
        except json.JSONDecodeError:
            return {"error": f"Server returned HTTP {e.code} with an unreadable body."}
    except urllib.error.URLError as e:
        # The request never reached a server at all: connection refused,
        # DNS failure, or (wrapped inside e.reason) a timeout.
        return {"error": f"Could not reach the server: {e.reason}"}


def main():
    import threading

    from api_server import RagRequestHandler, build_app_state
    from http.server import ThreadingHTTPServer

    print("=== Client Example ===\n")

    RagRequestHandler.app_state = build_app_state()
    httpd = ThreadingHTTPServer(("127.0.0.1", 0), RagRequestHandler)
    port = httpd.server_port
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()

    base_url = f"http://127.0.0.1:{port}"
    print(f"Server started on {base_url}\n")

    try:
        questions = [
            "What is RAG?",
            "What is a vector database?",
            "What programming language is easy to read?",
        ]

        for question in questions:
            result = ask(question, base_url)
            print(f"Question: {question}")
            if "error" in result:
                print(f"  Error: {result['error']}\n")
                continue
            print(f"  Status: {result['status']}")
            print(f"  Answer: {result['answer'][:150]}...")
            print(f"  Sources: {result['sources']}\n")

        print("--- A connection error (a server that isn't actually running) ---")
        result = ask("Does anyone answer here?", "http://127.0.0.1:1", timeout=1)
        print(f"  {result}\n")

    finally:
        httpd.shutdown()
        httpd.server_close()
        print("Server shut down cleanly.")

    print(
        "\nWhy client-side error handling and timeouts matter: a server "
        "can fail in two very different ways, by responding with an "
        "error, or by never responding at all. Without an explicit "
        "timeout, the second case would hang this client indefinitely "
        "instead of returning a clear, readable error, exactly the "
        "difference shown by the HTTPError and URLError branches above."
    )


if __name__ == "__main__":
    main()
