"""
agent_with_planning.py

The whole pipeline, end to end: plan a goal with fake_planner.py,
validate the plan with plan_structure.py, execute it with
plan_executor.py, replan if a step fails using replanning.py's logic,
and print a final honest report of what was done, what failed, and what
was skipped.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from fake_planner import fake_plan
from plan_executor import AVAILABLE_TOOLS, execute_plan
from plan_structure import validate_plan
from replanning import MAX_REPLANS, any_step_failed


def handle_goal(goal, revised_goal_for_failure=None, max_replans=MAX_REPLANS):
    """
    Runs the full pipeline for one goal:
      1. PLAN: ask fake_planner.py for a Plan.
      2. VALIDATE: check it against plan_structure.validate_plan() before running anything.
      3. EXECUTE: run it with plan_executor.py.
      4. REPLAN IF NEEDED: on any failed step, ask for a revised plan and try again, up to max_replans times.
      5. REPORT: print exactly what finished, what failed, and what was skipped, honestly.
    """
    print(f"=== Handling goal: '{goal}' ===\n")

    current_goal = goal
    attempt = 0

    while True:
        attempt += 1
        print(f"--- Attempt {attempt} ---\n")

        # STEP 1: PLAN.
        plan = fake_plan(current_goal)

        # STEP 2: VALIDATE, before a single tool call happens.
        is_valid, error = validate_plan(plan, set(AVAILABLE_TOOLS))
        if not is_valid:
            print(f"Plan is invalid, stopping: {error}\n")
            return {"outcome": "invalid_plan", "error": error}

        # STEP 3: EXECUTE.
        results = execute_plan(plan)
        print()

        if not any_step_failed(results):
            print(f"Attempt {attempt} finished with no failed steps.\n")
            return {"outcome": "success", "results": results, "attempts": attempt}

        # STEP 4: REPLAN IF NEEDED.
        if attempt > max_replans or revised_goal_for_failure is None:
            print(f"Stopping after {attempt} attempt(s): replan budget exhausted or no revised plan available.\n")
            return {"outcome": "gave_up", "results": results, "attempts": attempt}

        print(f"A step failed. Replanning (attempt {attempt} of {max_replans} replans allowed)...\n")
        current_goal = revised_goal_for_failure


def print_final_report(outcome):
    print("=== Final Report ===\n")
    print(f"Outcome: {outcome['outcome']}")

    if outcome["outcome"] == "invalid_plan":
        print(f"The plan itself was invalid: {outcome['error']}")
        return

    results = outcome["results"]
    done = [sid for sid, r in results.items() if r["status"] == "done"]
    failed = [sid for sid, r in results.items() if r["status"] == "failed"]
    skipped = [sid for sid, r in results.items() if r["status"] == "skipped"]

    print(f"Attempts made: {outcome['attempts']}")
    print(f"Done: {done}")
    print(f"Failed: {failed}")
    print(f"Skipped: {skipped}")


def main():
    print("=== Agent With Planning, End to End ===\n")

    outcome = handle_goal(
        goal="handle damaged order 1001",
    )
    print_final_report(outcome)

    print("\n" + "=" * 60 + "\n")

    outcome = handle_goal(
        goal="handle damaged order 9999",
        revised_goal_for_failure="handle damaged order 9999 (revised after failure)",
    )
    print_final_report(outcome)

    print(
        "\nHow this connects: fake_planner.py decides WHAT to do, "
        "plan_structure.py's validate_plan() checks that the WHAT is "
        "actually sound before committing to it, plan_executor.py's "
        "execute_plan() does the WHAT in the right order, and "
        "replanning.py's failure-handling logic decides what to do when "
        "the WHAT turns out not to work. Each piece does exactly one job, "
        "and the full pipeline is just those four jobs run in sequence, "
        "same as every other day in this project where a clean separation "
        "between pieces made the whole system easier to reason about."
    )


if __name__ == "__main__":
    main()
