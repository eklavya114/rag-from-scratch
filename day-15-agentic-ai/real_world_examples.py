"""
real_world_examples.py

Four realistic agent use cases, each built from the simulated tools in
tool_examples.py, run step by step so the full think->act->observe
trace is visible for each one.
"""

from tool_examples import (
    create_ticket_tool,
    database_query_tool,
    search_tool,
    send_email_tool,
    web_search_tool,
)


def support_agent(customer_message):
    """SUPPORT AGENT: tries to resolve a customer issue using the knowledge base; if it can't, escalates by creating a ticket -- the RAG-can-answer vs. action-is-needed decision point."""
    print(f"Customer says: \"{customer_message}\"\n")

    print("Step 1: search the knowledge base for a resolution.")
    answer = search_tool("rag" if "rag" in customer_message.lower() else "unrelated_topic")
    print(f"  -> {answer}")

    if answer.startswith("No information found"):
        print("Step 2: knowledge base didn't help -- escalating.")
        ticket_result = create_ticket_tool(customer_message, priority="normal")
        print(f"  -> {ticket_result}")
        send_email_tool("customer@example.com", "We've received your request", ticket_result)
        return ticket_result
    else:
        print("Step 2: knowledge base answered it -- replying directly, no ticket needed.")
        send_email_tool("customer@example.com", "Answer to your question", answer)
        return answer


def research_agent(topic):
    """RESEARCH AGENT: searches, then summarizes what it found -- a short multi-step chain toward one goal."""
    print(f"Researching: \"{topic}\"\n")

    print("Step 1: search the web for the topic.")
    result = web_search_tool(topic)
    print(f"  -> {result}")

    print("Step 2: summarize the finding.")
    summary = f"Summary: {topic} appears to be a well-documented subject based on available search results."
    print(f"  -> {summary}")
    return summary


CATALOG = {
    "laptop_a": {"name": "Laptop A", "price": 999},
    "laptop_b": {"name": "Laptop B", "price": 849},
    "laptop_c": {"name": "Laptop C", "price": 1099},
}


def shopping_agent(budget):
    """SHOPPING AGENT: compares options against a constraint (budget) and picks the best fit, rather than just listing everything."""
    print(f"Shopping with a budget of ${budget}\n")

    print("Step 1: check what's in the catalog.")
    affordable = [item for item in CATALOG.values() if item["price"] <= budget]
    print(f"  -> {len(affordable)} of {len(CATALOG)} items fit the budget: {[i['name'] for i in affordable]}")

    if not affordable:
        print("Step 2: nothing fits -- reporting back instead of guessing.")
        return None

    print("Step 2: pick the best (cheapest, since all else is equal here).")
    best = min(affordable, key=lambda item: item["price"])
    print(f"  -> Recommending {best['name']} at ${best['price']}")
    return best


def code_agent(snippet):
    """CODE AGENT: reads a snippet and explains what it does -- a simple rule-based 'explanation' standing in for a real code-understanding model."""
    print(f"Explaining snippet:\n{snippet}\n")

    print("Step 1: look for recognizable patterns.")
    if "def " in snippet and "return" in snippet:
        explanation = "This defines a function that computes and returns a value."
    elif "for " in snippet:
        explanation = "This iterates over a collection, performing an action on each item."
    else:
        explanation = "This is a general code snippet; no specific pattern was recognized."
    print(f"  -> {explanation}")
    return explanation


def main():
    print("=== Real-World Agent Examples ===\n")

    print("--- 1. Support Agent ---")
    support_agent("I have a question about RAG.")
    print()
    support_agent("My invoice looks wrong.")

    print("\n--- 2. Research Agent ---")
    research_agent("transformer architectures")

    print("\n--- 3. Shopping Agent ---")
    shopping_agent(budget=900)

    print("\n--- 4. Code Agent ---")
    code_agent("def square(x):\n    return x * x")

    print(
        "\nNotice the shared shape across all four: each agent takes a "
        "goal, picks a small sequence of tool calls suited to that goal, "
        "and produces either an answer or a real side effect (a ticket, an "
        "email, a recommendation) -- the same think/act/observe loop from "
        "simple_agent.py, just pointed at a different real-world problem "
        "each time."
    )


if __name__ == "__main__":
    main()
