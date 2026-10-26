"""
plan_executor.py

Runs a validated Plan step by step, in dependency order (a topological
sort of the depends_on graph), feeding each finished step's real output
into any later step's arguments that reference it. Every step is
recorded as "done", "failed", or "skipped", and a failed step causes
every step that depends on it, directly or indirectly, to be skipped
rather than run on top of a result that never actually happened.
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "day-16-custom-tools"))
from support_tools import check_refund_eligibility, create_ticket, lookup_order  # Day 16

from fake_planner import fake_plan
from plan_structure import validate_plan

AVAILABLE_TOOLS = {
    "lookup_order": lookup_order,
    "check_refund_eligibility": check_refund_eligibility,
    "create_ticket": create_ticket,
}


def topological_order(steps):
    """
    Orders steps so that every step comes after everything in its
    depends_on list, using a simple repeated-pass approach: keep
    picking any step whose dependencies have already been placed, until
    every step has been placed. plan_structure.validate_plan() is
    assumed to have already ruled out cycles and unknown dependency ids
    before this runs.
    """
    steps_by_id = {step.step_id: step for step in steps}
    ordered = []
    placed = set()

    while len(ordered) < len(steps):
        progress = False
        for step in steps:
            if step.step_id in placed:
                continue
            if all(dep_id in placed for dep_id in step.depends_on):
                ordered.append(step)
                placed.add(step.step_id)
                progress = True
        if not progress:
            raise RuntimeError("Could not order remaining steps, this should not happen on a validated, acyclic plan.")

    return ordered


def resolve_arguments(arguments, results_by_step_id):
    """
    Resolves any argument value written as {"from_step": "s1", "field": "status"}
    into the actual value from that earlier step's recorded output,
    passing real data forward instead of re-deriving it. Plain values
    pass through unchanged.
    """
    resolved = {}
    for key, value in arguments.items():
        if isinstance(value, dict) and "from_step" in value:
            source_result = results_by_step_id[value["from_step"]]["output"]
            resolved[key] = source_result.get(value["field"])
        else:
            resolved[key] = value
    return resolved


def execute_plan(plan, known_tools=AVAILABLE_TOOLS):
    """
    Executes every step in dependency order. Returns a dict of
    step_id -> {"status": "done"|"failed"|"skipped", "output": ...}.
    A step is skipped if any of its dependencies did not finish with
    "done", since running it on top of a dependency that failed or was
    itself skipped would mean acting on data that was never actually
    produced.
    """
    results = {}
    ordered_steps = topological_order(plan.steps)

    print(f"Goal: {plan.goal}\n")
    print(f"Execution order: {[step.step_id for step in ordered_steps]}\n")

    for step in ordered_steps:
        unmet_dependencies = [dep_id for dep_id in step.depends_on if results.get(dep_id, {}).get("status") != "done"]

        if unmet_dependencies:
            results[step.step_id] = {"status": "skipped", "output": None}
            print(f"[{step.step_id}] SKIPPED: unmet dependency on {unmet_dependencies}")
            continue

        arguments = resolve_arguments(step.arguments, results)
        tool = known_tools[step.tool_name]
        output = tool(**arguments)

        if isinstance(output, dict) and output.get("ok") is False:
            results[step.step_id] = {"status": "failed", "output": output}
            print(f"[{step.step_id}] FAILED: {step.tool_name}({arguments}) -> {output}")
        else:
            results[step.step_id] = {"status": "done", "output": output}
            print(f"[{step.step_id}] DONE: {step.tool_name}({arguments}) -> {output}")

    return results


def demonstrate_output_passing():
    """
    A small plan showing arguments.resolve_arguments actually feeding
    one step's real output into a later step's arguments, the "order
    status feeds the refund check" idea from the spec: s2's issue text
    is built from s1's REAL looked-up item name, not a value typed in
    ahead of time.
    """
    from plan_structure import Plan, Step

    plan = Plan(
        goal="Look up an order and log its real item name in a ticket",
        steps=[
            Step("s1", "Look up the order", "lookup_order", {"order_id": "ORD-1001"}),
            Step(
                "s2",
                "Create a ticket mentioning the actual item from the lookup",
                "create_ticket",
                {"issue": {"from_step": "s1", "field": "item"}, "priority": "low"},
                depends_on=["s1"],
            ),
        ],
    )

    print("--- Passing one step's real output into a later step's arguments ---\n")
    results = execute_plan(plan)
    print(f"\ns1's real 'item' value flowed directly into s2's 'issue' argument: {results['s2']['output'].get('issue')!r}")


def main():
    print("=== Executing a Plan ===\n")

    plan = fake_plan("handle damaged order 1001")
    is_valid, error = validate_plan(plan, set(AVAILABLE_TOOLS))
    print(f"Plan valid: {is_valid}" + (f", {error}" if error else "") + "\n")

    results = execute_plan(plan)

    print("\n--- Final status per step ---")
    for step_id, result in results.items():
        print(f"  {step_id}: {result['status']}")

    print("\n" + "=" * 60 + "\n")
    demonstrate_output_passing()


if __name__ == "__main__":
    main()
