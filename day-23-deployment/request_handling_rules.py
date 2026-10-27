"""
request_handling_rules.py

The HTTP rules in one place: which service status maps to which HTTP
code, how large a request body is allowed to be, and which methods each
path accepts. This mapping is a CONTRACT with clients: once published,
changing what status code a given outcome returns breaks every client
that already wrote code around the old behavior. Defining it once, here,
means api_server.py cannot drift from it by accident.
"""

MAX_BODY_SIZE_BYTES = 10_000  # requests larger than this get a 413, no exceptions

ALLOWED_METHODS = {
    "/query": {"POST"},
    "/health": {"GET"},
    "/metrics": {"GET"},
}

# Day 22's RagResponse.status values, mapped to the HTTP code a client
# should see for each one:
#   "ok"         -> 200, a normal successful answer
#   "rejected"   -> 400, the CLIENT sent something invalid (bad input)
#   "no_results" -> 200, the request was valid, the service just found
#                   nothing relevant; this is a successful, honest answer,
#                   not a client or server error
#   "error"      -> 500, something broke on the SERVER side
STATUS_TO_HTTP_CODE = {
    "ok": 200,
    "rejected": 400,
    "no_results": 200,
    "error": 500,
}


def http_code_for_status(service_status):
    """
    Returns the HTTP status code a client should receive for a given
    RagResponse.status value. An unrecognized status is treated as a
    server error rather than silently defaulting to 200, since claiming
    success for an outcome nobody planned for would be a worse failure
    than an honest 500.
    """
    return STATUS_TO_HTTP_CODE.get(service_status, 500)


def main():
    print("=== Request Handling Rules ===\n")

    print(f"Max body size: {MAX_BODY_SIZE_BYTES} bytes\n")

    print("Allowed methods per path:")
    for path, methods in ALLOWED_METHODS.items():
        print(f"  {path:<12} {sorted(methods)}")

    print("\nService status -> HTTP code mapping:")
    print(f"{'service status':<14}{'http code':<10}{'meaning'}")
    meanings = {
        "ok": "a normal, successful answer",
        "rejected": "the client sent invalid input",
        "no_results": "valid request, nothing relevant found",
        "error": "something broke on the server",
    }
    for status, code in STATUS_TO_HTTP_CODE.items():
        print(f"{status:<14}{code:<10}{meanings[status]}")

    print("\n--- http_code_for_status() in action ---")
    for status in ["ok", "rejected", "no_results", "error", "totally_unknown_status"]:
        print(f"  {status:<24} -> {http_code_for_status(status)}")

    print(
        "\nWhy this mapping is a contract with clients: once a client is "
        "written to expect 'rejected' input to come back as a 400, "
        "changing that to a 422 later silently breaks every client that "
        "already checks for 400 specifically. Defining the mapping once, "
        "in one file that both the server and any test import, is what "
        "keeps that contract honest and in one place instead of scattered "
        "across handler code."
    )


if __name__ == "__main__":
    main()
