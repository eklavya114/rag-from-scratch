"""
plan_vs_react.py

Compares a full plan (write everything first, then execute) against
Day 17's ReAct style of deciding one step at a time, on the exact same
goal and tools. Counts tool calls for each, and shows where each
approach wastes effort or recovers differently when something
surprising happens.
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "day-16-custom-tools"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "day-17-react-pattern"))
from support_tools import check_refund_eligibility, lookup_order  # Day 16
from react_parser import parse_react_text  # Day 17

from fake_planner import fake_plan
from plan_executor import AVAILABLE_TOOLS, execute_plan
from plan_structure import validate_plan

GOAL = "handle damaged order 1001"


def run_react_version():
    """
    ReAct style: decide one step at a time, reading each observation
    before choosing the next action, the same shape as Day 17's
    react_loop.py. Scripted here with the same fixed task so it can be
    compared fairly against the planning version below.
    """
    print("--- ReAct version (one step at a time) ---\n")

    tool_calls_made = 0
    history = []

    def fake_llm_react_step(step_number):
        if step_number == 1:
            return "Thought: I need to look up the order first.\nAction: lookup_order\nAction Input: ORD-1001"
        if step_number == 2:
            return "Thought: The order was delivered, so I should check refund eligibility.\nAction: check_refund_eligibility\nAction Input: ORD-1001"
        return "Thought: I have what I need.\nFinal Answer: Order ORD-1001 was delivered but is outside the refund window."

    for step_number in range(1, 4):
        raw_text = fake_llm_react_step(step_number)
        parsed = parse_react_text(raw_text)
        print(f"Thought: {parsed.thought}")

        if parsed.final_answer:
            print(f"Final Answer: {parsed.final_answer}\n")
            break

        print(f"Action: {parsed.action}({parsed.action_input})")
        tool = {"lookup_order": lookup_order, "check_refund_eligibility": check_refund_eligibility}[parsed.action]
        result = tool(parsed.action_input)
        tool_calls_made += 1
        print(f"Observation: {result}\n")
        history.append(result)

    return tool_calls_made


def run_planning_version():
    """Planning style: the full plan is written out BEFORE any tool runs, then executed in order."""
    print("--- Planning version (write the plan first) ---\n")

    plan = fake_plan(GOAL)
    is_valid, error = validate_plan(plan, set(AVAILABLE_TOOLS))
    print(f"Plan has {len(plan.steps)} steps, valid: {is_valid}\n")

    for step in plan.steps:
        print(f"  planned: [{step.step_id}] {step.tool_name}({step.arguments})")
    print()

    results = execute_plan(plan)
    tool_calls_made = sum(1 for r in results.values() if r["status"] in ("done", "failed"))
    return tool_calls_made


def main():
    print(f"=== Planning vs. ReAct, Same Goal: '{GOAL}' ===\n")

    react_tool_calls = run_react_version()
    print("=" * 60 + "\n")
    planning_tool_calls = run_planning_version()

    print("\n=== Comparison ===\n")
    print(f"ReAct tool calls made: {react_tool_calls}")
    print(f"Planning tool calls made: {planning_tool_calls}")

    print(
        "\nThe tradeoff: planning let the whole path be inspected BEFORE "
        "any tool ran, here it was 3 steps committed to up front, validated "
        "for unknown tools and cycles before execution began. ReAct never "
        "commits to more than the next single step, which means it can "
        "change direction immediately if an early observation is "
        "surprising, without needing anything like replanning.py's revised "
        "plan lookup. Notice the actual tool call counts differ too: the "
        "ReAct version here was scripted to stop at 2 calls once it decided "
        "it had 'enough to answer,' while the planning version committed up "
        "front to a 3rd step (opening a ticket) that ReAct's script never "
        "got around to considering. That gap is not a coincidence, it is "
        "the same tradeoff: a plan written out in full is less likely to "
        "quietly stop one step short of the actual goal, while a one-step-"
        "at-a-time loop can always decide 'that's enough' earlier than it "
        "should. The real difference shows up most clearly when something "
        "goes wrong: ReAct adapts on the very next step, while planning has "
        "to detect the failure and explicitly go ask for a new plan."
    )


if __name__ == "__main__":
    main()
