"""
tool_examples.py

A broader set of example tools, each demonstrating a different kind of
thing an agent might need to do: look things up, compute something,
communicate, take an action with a side effect, or read from storage.
All simulated (no real network/email/filesystem calls) so this file is
safe to run anywhere, but each one is written the way a real tool
would be structured.
"""


def search_tool(query):
    """SEARCH: finds information. A real version would hit a search API; here a small fixed knowledge base stands in for it."""
    knowledge_base = {
        "rag": "RAG combines retrieval with generation to answer questions grounded in real documents.",
        "agent": "An agent is a system that thinks, decides, and acts, usually in a loop.",
    }
    key = query.lower().strip()
    return knowledge_base.get(key, f"No information found for '{query}'.")


def calculate_tool(expression):
    """
    CALCULATE: does math safely. Deliberately avoids eval() on
    arbitrary text -- this is a security-relevant choice, since an
    agent's "math expression" argument could otherwise be used to run
    arbitrary code. Only a restricted 'number operator number' form is
    supported.
    """
    parts = expression.split()
    if len(parts) != 3:
        return "Error: expected 'number operator number', e.g. '3 * 4'."
    left_str, op, right_str = parts
    try:
        left, right = float(left_str), float(right_str)
    except ValueError:
        return "Error: operands must be numbers."
    operations = {
        "+": lambda a, b: a + b,
        "-": lambda a, b: a - b,
        "*": lambda a, b: a * b,
        "/": lambda a, b: a / b if b != 0 else "Error: division by zero.",
    }
    if op not in operations:
        return f"Error: unsupported operator '{op}'."
    return operations[op](left, right)


def send_email_tool(to, subject, body=""):
    """SEND EMAIL: communicates with someone. Simulated -- prints what WOULD be sent instead of using a real mail server, so this file has no external side effects."""
    print(f"[simulated email] To: {to} | Subject: {subject} | Body: {body}")
    return f"Email queued for {to}."


def create_ticket_tool(title, priority="normal"):
    """CREATE TICKET: takes an action with a lasting side effect -- a real version would call a ticketing system's API and return a real ticket ID."""
    ticket_id = f"TICKET-{abs(hash(title)) % 10000:04d}"
    return f"Created {priority}-priority ticket {ticket_id}: '{title}'."


def web_search_tool(query):
    """WEB SEARCH: simulated external lookup, standing in for a real web search API call that isn't available in this offline exercise."""
    return f"[simulated web search] Top result for '{query}': 'Understanding {query} - a complete guide'."


DATABASE = {
    "user_42": {"name": "Jordan Lee", "plan": "pro", "signup_year": 2024},
    "user_7": {"name": "Alex Kim", "plan": "free", "signup_year": 2023},
}


def database_query_tool(user_id):
    """DATABASE QUERY: reads from storage. A small in-memory dict stands in for a real database connection, keeping this tool dependency-free."""
    record = DATABASE.get(user_id)
    if record is None:
        return f"No record found for '{user_id}'."
    return record


def main():
    print("=== Example Tools ===\n")

    print("--- search_tool ---")
    print(search_tool("rag"))

    print("\n--- calculate_tool ---")
    print(f"3 * 4 = {calculate_tool('3 * 4')}")
    print(f"invalid input: {calculate_tool('3 ** 4')}")

    print("\n--- send_email_tool ---")
    print(send_email_tool("customer@example.com", "Your ticket update", "We're looking into it."))

    print("\n--- create_ticket_tool ---")
    print(create_ticket_tool("Login page returns a 500 error", priority="high"))

    print("\n--- web_search_tool ---")
    print(web_search_tool("vector databases"))

    print("\n--- database_query_tool ---")
    print(f"user_42 -> {database_query_tool('user_42')}")
    print(f"user_99 -> {database_query_tool('user_99')}")

    print(
        "\nTool design notes: each tool here does exactly ONE thing, takes "
        "plain arguments (not a whole conversation), and returns either a "
        "usable result or a clearly labeled error string -- never raises an "
        "uncaught exception for an expected failure mode. That predictability "
        "is what lets an agent loop treat every tool call the same way."
    )


if __name__ == "__main__":
    main()
