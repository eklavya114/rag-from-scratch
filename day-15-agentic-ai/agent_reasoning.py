"""
agent_reasoning.py

simple_agent.py's loop made a decision every step, but that decision
was a single opaque function call. This file breaks that same process
into its four distinct parts -- think, decide, observe, reflect -- and
prints each one explicitly, so the reasoning that's normally hidden
inside an LLM call is visible step by step.
"""

import json
import os


def think(task, context):
    """
    THINK: given the task and what's happened so far, what does the
    situation call for right now? A real LLM would generate this as
    free text; here we derive it from simple rules so it's
    deterministic and runs without an API key.
    """
    if not context:
        thought = f"I need to start working on: '{task}'. The first thing to do is gather information."
    elif context[-1]["tool"] == "search" and "calculate" not in [c["tool"] for c in context]:
        thought = "I found some information. Now I should check if any math is needed."
    else:
        thought = "I have what I need. The task looks complete."
    return thought


def decide(thought, context):
    """ACTION SELECTION: turn the thought into a concrete tool choice -- the step where reasoning becomes something executable."""
    if "gather information" in thought:
        return {"tool": "search", "args": ["population of France"]}
    if "check if any math" in thought:
        return {"tool": "calculate", "args": ["67000000", "/", "1000000"]}
    return {"tool": "done", "args": []}


def act(decision, tools):
    """ACT: execute the chosen tool. Any exception becomes a clearly labeled failed observation instead of crashing the loop."""
    tool_name = decision["tool"]
    if tool_name == "done":
        return None
    try:
        return tools[tool_name](*decision["args"])
    except Exception as exc:
        return f"ERROR: {exc}"


def observe(decision, result):
    """OBSERVATION COLLECTION: record exactly what happened -- the tool called, the arguments, and the real result -- so reflection has something concrete to work from."""
    return {"tool": decision["tool"], "args": decision["args"], "result": result}


def reflect(observation_history):
    """
    REFLECTION: look back over what happened and draw a conclusion --
    did the actions taken actually make progress? This is what lets an
    agent notice it's stuck or that a result didn't help, rather than
    blindly repeating the same plan.
    """
    if not observation_history:
        return "No actions taken yet."
    tool_names = [obs["tool"] for obs in observation_history]
    if "ERROR" in str(observation_history[-1]["result"]):
        return f"The last action ({tool_names[-1]}) failed -- a different approach may be needed."
    return f"Made progress using: {', '.join(tool_names)}. Results looked usable."


def fake_search(query):
    return "France has a population of about 67,000,000."


def fake_calculate(a, op, b):
    a, b = float(a), float(b)
    return a / b if op == "/" else None


TOOLS = {"search": fake_search, "calculate": fake_calculate}


def main():
    print("=== Agent Reasoning: Think, Decide, Act, Observe, Reflect ===\n")

    task = "How many millions of people live in France?"
    context = []

    for step in range(1, 4):
        print(f"--- Step {step} ---")

        thought = think(task, context)
        print(f"THINK:   {thought}")

        decision = decide(thought, context)
        print(f"DECIDE:  use tool '{decision['tool']}' with args {decision['args']}")

        if decision["tool"] == "done":
            print("ACT:     (no tool call needed, task is complete)")
            break

        result = act(decision, TOOLS)
        print(f"ACT:     executed {decision['tool']} -> {result}")

        observation = observe(decision, result)
        context.append(observation)
        print(f"OBSERVE: recorded {observation}")

        reflection = reflect(context)
        print(f"REFLECT: {reflection}\n")

    print("=== Final reflection ===")
    print(reflect(context))

    # Persist the reasoning trace so it could be inspected or replayed later --
    # agents that can't show their work are much harder to debug.
    trace_path = os.path.join(os.path.dirname(__file__), "reasoning_trace.json")
    with open(trace_path, "w", encoding="utf-8") as f:
        json.dump(context, f, indent=2)
    print(f"\nReasoning trace saved to {trace_path}")


if __name__ == "__main__":
    main()
