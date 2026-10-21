"""
tool_safety.py

A tool is code that an agent decides to run on its own, without a
human reviewing each call -- which makes it a real attack surface, not
just a convenience function. This file shows four concrete safety
practices: validating inputs before doing anything, never running
arbitrary code, requiring confirmation for risky actions, and logging
every call.
"""

import datetime

CALL_LOG = []


def log_tool_call(tool_name, args, result):
    """LOG EVERY TOOL CALL: records what was called, with what arguments, and what came back -- without this, a bad outcome is undebuggable after the fact."""
    CALL_LOG.append({
        "timestamp": datetime.datetime(2026, 10, 21, 12, 0, 0).isoformat(),
        "tool": tool_name,
        "args": args,
        "result": result,
    })


def validate_before_acting(amount, max_allowed):
    """VALIDATE ALL INPUTS BEFORE DOING ANYTHING: reject bad input before any side effect happens, not after."""
    if not isinstance(amount, (int, float)):
        return False, "amount must be a number."
    if amount < 0:
        return False, "amount cannot be negative."
    if amount > max_allowed:
        return False, f"amount ${amount} exceeds the maximum allowed (${max_allowed})."
    return True, None


def never_run_arbitrary_code(expression):
    """
    NEVER LET A TOOL RUN ARBITRARY CODE OR SHELL COMMANDS: this is
    deliberately a REFUSAL, not an implementation -- a 'calculate'
    tool should use a restricted parser (as in Day 15's tool_examples.py)
    or a safe library, never pass agent-controlled text to eval(),
    exec(), or a shell. Demonstrating the refusal itself is the lesson.
    """
    return {"ok": False, "error": "Refused: tools must never execute arbitrary code or shell commands, regardless of who or what provided the input."}


REFUND_CONFIRMATION_THRESHOLD = 100.00


def process_refund(order_id, amount, confirmed=False):
    """REQUIRE CONFIRMATION FOR RISKY ACTIONS: a refund above the threshold needs an explicit confirmed=True, so a single bad agent decision can't move a large amount of money unsupervised."""
    is_valid, error = validate_before_acting(amount, max_allowed=10000)
    if not is_valid:
        result = {"ok": False, "error": error}
        log_tool_call("process_refund", {"order_id": order_id, "amount": amount}, result)
        return result

    if amount > REFUND_CONFIRMATION_THRESHOLD and not confirmed:
        result = {
            "ok": False,
            "error": f"Refund of ${amount} exceeds ${REFUND_CONFIRMATION_THRESHOLD} and requires confirmed=True.",
            "requires_confirmation": True,
        }
        log_tool_call("process_refund", {"order_id": order_id, "amount": amount}, result)
        return result

    result = {"ok": True, "order_id": order_id, "refunded": amount}
    log_tool_call("process_refund", {"order_id": order_id, "amount": amount}, result)
    return result


def main():
    print("=== Tool Safety ===\n")

    print("--- Validate inputs before acting ---")
    print(validate_before_acting(50, max_allowed=100))
    print(validate_before_acting(-10, max_allowed=100))
    print(validate_before_acting("fifty", max_allowed=100))

    print("\n--- Never run arbitrary code ---")
    print(never_run_arbitrary_code("import os; os.system('rm -rf /')"))

    print("\n--- Require confirmation for risky actions ---")
    print("Small refund (no confirmation needed):", process_refund("ORD-1001", 40.00))
    print("Large refund without confirmation (blocked):", process_refund("ORD-1002", 500.00))
    print("Large refund WITH confirmation (allowed):", process_refund("ORD-1002", 500.00, confirmed=True))

    print(f"\n--- Call log ({len(CALL_LOG)} entries) ---")
    for entry in CALL_LOG:
        print(f"  {entry}")

    print(
        "\nLeast-privilege design: a tool should be granted exactly the "
        "access it needs to do its one job -- a refund tool shouldn't also "
        "be able to delete accounts, and a search tool shouldn't be able to "
        "write to a database. The smaller each tool's capability, the "
        "smaller the damage any single bad agent decision can do."
    )


if __name__ == "__main__":
    main()
