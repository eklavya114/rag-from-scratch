"""
cost_and_step_budget.py

A plan's cost is bounded by how many steps it has and roughly how much
work each one does. This file estimates a simple per-step cost, caps a
plan at a max_steps budget, and stops execution once the budget runs
out, reporting exactly what was left undone rather than quietly running
past the limit.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from plan_executor import AVAILABLE_TOOLS, resolve_arguments, topological_order
from plan_structure import Plan, Step

# A simple estimate: each tool call costs 1 "unit" of budget, standing
# in for a real system's estimate of tokens spent or API calls made.
ESTIMATED_COST_PER_STEP = 1


def execute_plan_with_budget(plan, max_budget, known_tools=AVAILABLE_TOOLS):
    """
    Same execution logic as plan_executor.execute_plan, except it stops
    as soon as running the next step would exceed max_budget, instead
    of running every step regardless of cost. Steps not reached due to
    the budget are recorded as "skipped" with the reason "budget", so
    the final report can tell a budget cutoff apart from a dependency
    failure.
    """
    results = {}
    ordered_steps = topological_order(plan.steps)
    spent = 0

    print(f"Goal: {plan.goal}")
    print(f"Budget: {max_budget} units, estimated cost per step: {ESTIMATED_COST_PER_STEP}\n")

    for step in ordered_steps:
        unmet_dependencies = [dep_id for dep_id in step.depends_on if results.get(dep_id, {}).get("status") != "done"]
        if unmet_dependencies:
            results[step.step_id] = {"status": "skipped", "reason": "unmet_dependency"}
            print(f"[{step.step_id}] SKIPPED (unmet dependency): {unmet_dependencies}")
            continue

        if spent + ESTIMATED_COST_PER_STEP > max_budget:
            results[step.step_id] = {"status": "skipped", "reason": "budget"}
            print(f"[{step.step_id}] SKIPPED (budget exhausted): would cost {ESTIMATED_COST_PER_STEP}, only {max_budget - spent} remaining")
            continue

        arguments = resolve_arguments(step.arguments, results)
        output = known_tools[step.tool_name](**arguments)
        spent += ESTIMATED_COST_PER_STEP
        results[step.step_id] = {"status": "done", "output": output}
        print(f"[{step.step_id}] DONE ({spent}/{max_budget} spent): {step.tool_name}({arguments}) -> {output}")

    return results, spent


def main():
    print("=== Cost and Step Budgets ===\n")

    plan = Plan(
        goal="Handle damaged order ORD-1001",
        steps=[
            Step("s1", "Look up the order", "lookup_order", {"order_id": "ORD-1001"}),
            Step("s2", "Check refund eligibility", "check_refund_eligibility", {"order_id": "ORD-1001"}, depends_on=["s1"]),
            Step("s3", "Create a ticket", "create_ticket", {"issue": "Damaged item", "priority": "high"}, depends_on=["s2"]),
        ],
    )

    print("--- A plan that fits the budget ---\n")
    results, spent = execute_plan_with_budget(plan, max_budget=5)
    completed = [sid for sid, r in results.items() if r["status"] == "done"]
    print(f"\nCompleted {len(completed)} of {len(plan.steps)} steps, spent {spent} of 5 units.\n")

    print("=" * 60 + "\n")

    print("--- A plan that gets cut short ---\n")
    results, spent = execute_plan_with_budget(plan, max_budget=2)
    completed = [sid for sid, r in results.items() if r["status"] == "done"]
    left_undone = [sid for sid, r in results.items() if r["status"] == "skipped" and r["reason"] == "budget"]
    print(f"\nCompleted {len(completed)} of {len(plan.steps)} steps, spent {spent} of 2 units.")
    print(f"Left undone due to budget: {left_undone}")

    print(
        "\nWhy budgets matter: without a cap, a plan with more steps than "
        "intended, or one that keeps replanning, can keep spending real "
        "tool calls (and with a real model, real tokens and real money) "
        "indefinitely. A budget turns 'ran until it happened to finish or "
        "fail' into a known, predictable upper bound, and reporting exactly "
        "which steps were cut, and why, keeps a budget cutoff honest "
        "instead of silently leaving a task half done with no explanation."
    )


if __name__ == "__main__":
    main()
