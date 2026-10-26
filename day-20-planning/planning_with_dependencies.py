"""
planning_with_dependencies.py

Not every step in a plan has to wait for the one before it, only for
the ones it actually depends on. This file groups a plan's steps into
levels: every step in a level has no unmet dependency once the
previous levels are done, so every step in that level could, in
principle, run at the same time.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from plan_structure import Plan, Step, validate_plan


def group_into_levels(steps):
    """
    Groups steps into levels: level 0 holds every step with no
    dependencies at all, level 1 holds every step whose dependencies
    are all satisfied once level 0 is done, and so on. Every step
    within one level is independent of every other step in that same
    level, which is what makes running them together safe.
    """
    steps_by_id = {step.step_id: step for step in steps}
    placed = set()
    levels = []

    while len(placed) < len(steps):
        current_level = [
            step for step in steps
            if step.step_id not in placed and all(dep_id in placed for dep_id in step.depends_on)
        ]
        if not current_level:
            raise RuntimeError("Could not place remaining steps into a level, check for a cycle.")
        levels.append(current_level)
        placed.update(step.step_id for step in current_level)

    return levels


def main():
    print("=== Planning With Dependencies ===\n")

    # s1 and s2 are two independent lookups: neither needs the other's result.
    # s3 needs BOTH to finish before it can run.
    plan = Plan(
        goal="Compare two orders and summarize them in one ticket",
        steps=[
            Step("s1", "Look up the first order", "lookup_order", {"order_id": "ORD-1001"}),
            Step("s2", "Look up the second order", "lookup_order", {"order_id": "ORD-1002"}),
            Step("s3", "Create a summary ticket", "create_ticket", {"issue": "Comparing ORD-1001 and ORD-1002", "priority": "low"}, depends_on=["s1", "s2"]),
        ],
    )

    known_tools = {"lookup_order", "check_refund_eligibility", "create_ticket"}
    is_valid, error = validate_plan(plan, known_tools)
    print(f"Plan valid: {is_valid}" + (f", {error}" if error else "") + "\n")

    levels = group_into_levels(plan.steps)

    for i, level in enumerate(levels):
        step_ids = [step.step_id for step in level]
        print(f"Level {i}: {step_ids}")
        for step in level:
            print(f"  [{step.step_id}] {step.description} (depends_on={step.depends_on})")
    print()

    print(
        f"Level 0 ({[s.step_id for s in levels[0]]}) can run together: "
        f"neither step in it depends on anything, including each other.\n"
    )
    print(
        f"Level {len(levels) - 1} ({[s.step_id for s in levels[-1]]}) waits "
        f"for every step listed in its depends_on, not just the first one "
        f"to finish, s3 needs BOTH s1 and s2 done before it can run, even "
        f"though they're both in level 0 together.\n"
    )

    print(
        "Why this matters for a dependency graph: grouping into levels is "
        "exactly what lets an executor decide which steps are SAFE to run "
        "concurrently instead of always running one at a time. Two "
        "independent lookups waiting on nothing can be dispatched together, "
        "the same idea Day 19's parallel_tool_calls.py showed for a single "
        "model turn requesting two independent tool calls at once, just "
        "applied here across an entire plan's dependency structure instead "
        "of one turn."
    )


if __name__ == "__main__":
    main()
