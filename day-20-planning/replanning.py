"""
replanning.py

When a step fails, the honest options are retry, replan, or stop and
report. This file shows replanning: asking the fake planner for a
revised plan once a step actually fails, running that revised plan
instead, and capping how many times this can happen so a planner that
keeps failing cannot loop forever.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from fake_planner import fake_plan
from plan_executor import AVAILABLE_TOOLS, execute_plan
from plan_structure import validate_plan

MAX_REPLANS = 2


def any_step_failed(results):
    return any(result["status"] == "failed" for result in results.values())


def run_with_replanning(goal, revised_goal_for_failure, max_replans=MAX_REPLANS):
    """
    Runs a plan for `goal`. If any step fails, asks the fake planner
    for a revised plan (looked up by `revised_goal_for_failure`, since
    this fake planner is scripted rather than a real reasoning model)
    and runs that instead, up to `max_replans` times. Returns the
    results of whichever attempt finished without a failed step, or the
    results of the last attempt if every attempt failed.
    """
    goal_to_try = goal
    attempts = 0

    while True:
        attempts += 1
        print(f"--- Attempt {attempts}: {goal_to_try} ---\n")

        plan = fake_plan(goal_to_try)
        is_valid, error = validate_plan(plan, set(AVAILABLE_TOOLS))
        if not is_valid:
            print(f"Plan is invalid, cannot execute: {error}")
            return None

        results = execute_plan(plan)
        print()

        if not any_step_failed(results):
            print(f"Attempt {attempts} succeeded, no replanning needed.\n")
            return results

        if attempts > max_replans:
            print(f"Giving up after {attempts - 1} replan(s): the {max_replans}-replan limit was reached.\n")
            return results

        print(f"A step failed. Asking the planner for a revised plan (replan {attempts} of {max_replans})...\n")
        goal_to_try = revised_goal_for_failure


def report_outcome(results):
    done = [step_id for step_id, r in results.items() if r["status"] == "done"]
    failed = [step_id for step_id, r in results.items() if r["status"] == "failed"]
    skipped = [step_id for step_id, r in results.items() if r["status"] == "skipped"]
    print(f"Done: {done}")
    print(f"Failed: {failed}")
    print(f"Skipped: {skipped}")


def main():
    print("=== Replanning After a Failure ===\n")

    print("### Scenario 1: the first attempt fails, the replanned attempt succeeds ###\n")
    results = run_with_replanning(
        goal="handle damaged order 9999",
        revised_goal_for_failure="handle damaged order 9999 (revised after failure)",
    )
    print("Final outcome:")
    report_outcome(results)

    print("\n" + "=" * 60 + "\n")

    print("### Scenario 2: replanning runs out of attempts ###\n")
    # The revised goal passed here is the SAME failing goal, so every
    # "replan" just reruns the identical broken plan, simulating a
    # planner that cannot actually fix the problem within its budget.
    results = run_with_replanning(
        goal="handle damaged order 9999",
        revised_goal_for_failure="handle damaged order 9999",
        max_replans=2,
    )
    print("Final outcome, reporting honestly what was actually finished:")
    report_outcome(results)

    print(
        "\nWhen replanning is worth it: replanning makes sense when the "
        "FAILURE itself suggests a different approach would work, like "
        "an order id that does not exist, where the fix is to stop asking "
        "about a nonexistent order and log the problem instead. Replanning "
        "does nothing useful against a failure that a different plan "
        "cannot actually route around, which is exactly why a replan cap "
        "exists: past that cap, the honest move is to stop and report what "
        "was actually accomplished, not to keep trying the same broken "
        "idea with slightly different wording."
    )


if __name__ == "__main__":
    main()
