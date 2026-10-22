"""
loop_guards.py

A ReAct loop can fail to converge: an LLM can keep calling the same
tool with the same input forever, call a tool that doesn't exist, or
simply never produce a Final Answer within a reasonable number of
steps. This file shows three concrete guards against those failure
modes, each returning a clear message instead of hanging or crashing.
"""


class LoopGuardTriggered(Exception):
    """Raised when a guard detects the loop should stop -- carries a clear, specific reason."""


def guard_max_steps(step_number, max_steps):
    """MAX STEPS: the simplest guard -- bound the total number of reasoning steps regardless of what's happening, so a confused loop can't run forever."""
    if step_number > max_steps:
        raise LoopGuardTriggered(f"Reached the {max_steps}-step limit without a Final Answer.")


def guard_repeated_action(history, action, action_input):
    """
    DETECT REPEATED IDENTICAL ACTIONS: if the agent calls the SAME
    tool with the SAME input twice in a row, it's very likely stuck --
    a working agent reacts to the observation it just got, so calling
    the identical action again means that observation didn't change
    anything about its plan.
    """
    if not history:
        return
    last = history[-1]
    if last["action"] == action and last["action_input"] == action_input:
        raise LoopGuardTriggered(f"Action '{action}' was called with the same input ('{action_input}') twice in a row -- the agent appears stuck.")


def guard_unknown_tool(action, available_tools):
    """DETECT CALLS TO A TOOL THAT DOESN'T EXIST: an LLM can hallucinate a tool name that was never registered -- catch that before trying to call it."""
    if action not in available_tools:
        raise LoopGuardTriggered(f"Action '{action}' is not a registered tool. Available tools: {sorted(available_tools)}.")


def run_guarded_step(step_number, max_steps, history, action, action_input, available_tools):
    """Runs all three guards for one step, in order, before the action would actually be executed."""
    guard_max_steps(step_number, max_steps)
    guard_unknown_tool(action, available_tools)
    guard_repeated_action(history, action, action_input)


def main():
    print("=== Loop Guards ===\n")

    available_tools = {"lookup_order", "check_refund_eligibility"}

    print("--- Guard 1: max steps ---")
    try:
        run_guarded_step(step_number=11, max_steps=10, history=[], action="lookup_order", action_input="ORD-1001", available_tools=available_tools)
        print("No guard triggered (unexpected).")
    except LoopGuardTriggered as exc:
        print(f"Guard triggered: {exc}")

    print("\n--- Guard 2: repeated identical action ---")
    history = [{"action": "lookup_order", "action_input": "ORD-1001", "observation": {"status": "shipped"}}]
    try:
        run_guarded_step(step_number=2, max_steps=10, history=history, action="lookup_order", action_input="ORD-1001", available_tools=available_tools)
        print("No guard triggered (unexpected).")
    except LoopGuardTriggered as exc:
        print(f"Guard triggered: {exc}")

    print("\n--- Guard 3: unknown tool ---")
    try:
        run_guarded_step(step_number=1, max_steps=10, history=[], action="delete_everything", action_input="all", available_tools=available_tools)
        print("No guard triggered (unexpected).")
    except LoopGuardTriggered as exc:
        print(f"Guard triggered: {exc}")

    print("\n--- A step that passes all guards ---")
    try:
        run_guarded_step(step_number=1, max_steps=10, history=[], action="lookup_order", action_input="ORD-1001", available_tools=available_tools)
        print("All guards passed -- step is safe to execute.")
    except LoopGuardTriggered as exc:
        print(f"Guard triggered (unexpected): {exc}")

    print(
        "\nWhy loops need guards: an agent loop runs unattended, and none "
        "of these failure modes are rare in practice -- a model can get "
        "stuck in a pattern, hallucinate a tool name, or simply never "
        "converge on an answer. Each guard here turns an infinite or "
        "crashing loop into a clear, immediate, debuggable stop instead."
    )


if __name__ == "__main__":
    main()
