"""
error_handling.py

Every agent in this folder so far assumed tools behave. Real tools
fail: bad arguments, flaky APIs, unexpected shapes of data, and agents
that keep picking the same unhelpful action over and over. This file
shows each failure mode concretely and how to recover from it instead
of crashing the whole run.
"""


def flaky_divide(a, b):
    """A tool that can fail on bad input -- the kind of failure real tools raise all the time."""
    return a / b


def unpredictable_lookup(key):
    """A tool that sometimes returns something the caller doesn't expect (None instead of a string)."""
    data = {"rag": "Retrieval-Augmented Generation"}
    return data.get(key)  # returns None for anything not in the dict -- an easy thing to mishandle


def call_tool_safely(tool_fn, *args, **kwargs):
    """
    GRACEFUL DEGRADATION: wraps a tool call so an exception becomes a
    labeled failure result instead of crashing the agent loop. This is
    the single most important piece of agent error handling -- one bad
    tool call should never take down the whole run.
    """
    try:
        result = tool_fn(*args, **kwargs)
        return {"ok": True, "result": result}
    except Exception as exc:
        return {"ok": False, "error": f"{type(exc).__name__}: {exc}"}


def demonstrate_invalid_parameters():
    print("--- Tool call fails: invalid parameters ---\n")
    outcome = call_tool_safely(flaky_divide, 10, 0)
    print(f"divide(10, 0) -> {outcome}")
    outcome = call_tool_safely(flaky_divide, 10, "not a number")
    print(f"divide(10, 'not a number') -> {outcome}\n")


def demonstrate_unexpected_result():
    """TOOL RETURNS UNEXPECTED RESULT: a tool can succeed (no exception) but still return something the caller isn't prepared for, like None instead of text."""
    print("--- Tool returns unexpected result ---\n")
    result = unpredictable_lookup("rag")
    print(f"lookup('rag') -> {result!r} (as expected)")

    result = unpredictable_lookup("unknown_key")
    if result is None:
        print(f"lookup('unknown_key') -> {result!r} -- caught the None case instead of treating it as a usable answer")
    else:
        print(f"lookup('unknown_key') -> {result!r}")
    print()


def demonstrate_stuck_loop():
    """
    AGENT GETS STUCK IN LOOPS: a buggy decision function can keep
    picking the same unhelpful action forever. A max-steps guard is
    the simplest reliable fix -- it bounds the damage even when the
    underlying decision logic is wrong.
    """
    print("--- Agent gets stuck in a loop (max steps guard) ---\n")

    def always_same_decision(_context):
        return {"tool": "search", "args": ["same query every time"]}

    max_steps = 5
    steps_taken = 0
    context = []
    for step in range(1, max_steps + 1):
        decision = always_same_decision(context)
        context.append(decision)
        steps_taken += 1
        if steps_taken >= max_steps:
            print(f"Step {step}: still repeating '{decision['tool']}' -- stopping at the {max_steps}-step limit instead of looping forever.")
            break
        print(f"Step {step}: called {decision['tool']} again (no progress).")
    print()


def demonstrate_fallback_mechanism():
    """
    FALLBACK MECHANISMS: when the primary approach fails, fall back to
    a simpler, more reliable path rather than giving up entirely.
    """
    print("--- Fallback mechanism ---\n")

    def primary_tool(query):
        raise ConnectionError("primary search service is unreachable")

    def fallback_tool(query):
        return f"[fallback] cached result for '{query}'"

    primary_outcome = call_tool_safely(primary_tool, "latest news")
    if primary_outcome["ok"]:
        print(f"Primary tool succeeded: {primary_outcome['result']}")
    else:
        print(f"Primary tool failed ({primary_outcome['error']}), falling back...")
        fallback_outcome = call_tool_safely(fallback_tool, "latest news")
        print(f"Fallback result: {fallback_outcome['result']}")


def main():
    print("=== Agent Error Handling ===\n")
    demonstrate_invalid_parameters()
    demonstrate_unexpected_result()
    demonstrate_stuck_loop()
    demonstrate_fallback_mechanism()

    print(
        "\nWhy this matters: an agent that crashes on the first bad tool "
        "call, misreads a None as a real answer, loops forever on a bad "
        "decision, or has no fallback when its primary tool is down, is "
        "unusable in production no matter how good its reasoning is the "
        "rest of the time. Error handling isn't an afterthought for agents "
        "the way it sometimes is for simple scripts -- it's load-bearing, "
        "because agents run unattended and make their own decisions about "
        "what to try next."
    )


if __name__ == "__main__":
    main()
