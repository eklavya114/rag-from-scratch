"""
regression_check.py

Catches quality drops between versions of an agent. Saves a baseline
summary to a temporary JSON file, runs a "new version" of the agent
against the same fixed test set, and compares the two summaries. A
regression check belongs in every release because a change meant to fix
one thing can easily break another, and the only way to notice is to
compare against a saved number from before the change, not against a
guess about what should have happened.
"""

import json
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(__file__))
from eval_harness import run_harness, summarize
from eval_tasks import TEST_SET
from scripted_agents import AGENTS


def save_baseline(summary, path):
    """Saves a summary as the baseline to compare future runs against."""
    with open(path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)


def load_baseline(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def compare_to_baseline(baseline, new_summary):
    """
    Compares a new summary against a saved baseline on the metrics that
    matter for a regression: did the pass rate drop, and did forbidden
    calls increase. Returns a list of problems found, empty if none.
    """
    problems = []

    if new_summary["task_success_rate"] < baseline["task_success_rate"]:
        problems.append(
            f"task_success_rate dropped from {baseline['task_success_rate']:.0%} "
            f"to {new_summary['task_success_rate']:.0%}"
        )

    if new_summary["forbidden_call_count"] > baseline["forbidden_call_count"]:
        problems.append(
            f"forbidden_call_count increased from {baseline['forbidden_call_count']} "
            f"to {new_summary['forbidden_call_count']}"
        )

    return problems


def main():
    print("=== Regression Check ===\n")

    baseline_path = os.path.join(tempfile.gettempdir(), "day21_baseline_summary.json")

    print("Step 1: Save a baseline from the careful agent's results.\n")
    baseline_grades = run_harness(AGENTS["careful"], "careful", TEST_SET)
    baseline_summary = summarize(baseline_grades)
    save_baseline(baseline_summary, baseline_path)
    print(f"Baseline saved: task_success_rate={baseline_summary['task_success_rate']:.0%}, "
          f"forbidden_call_count={baseline_summary['forbidden_call_count']}\n")

    print("Step 2: Run the 'new version' of the agent (the risky agent) against the same test set.\n")
    new_grades = run_harness(AGENTS["risky"], "risky", TEST_SET)
    new_summary = summarize(new_grades)
    print(f"New version:  task_success_rate={new_summary['task_success_rate']:.0%}, "
          f"forbidden_call_count={new_summary['forbidden_call_count']}\n")

    print("Step 3: Compare against the saved baseline.\n")
    loaded_baseline = load_baseline(baseline_path)
    problems = compare_to_baseline(loaded_baseline, new_summary)

    if problems:
        print("FAIL")
        for problem in problems:
            print(f"  - {problem}")
    else:
        print("PASS")

    os.remove(baseline_path)
    print(f"\nTemporary baseline file removed: {baseline_path}")

    print(
        "\nWhy this belongs in every release: a change can be intended to "
        "fix one task and still quietly make the agent worse somewhere "
        "else. Without a saved baseline and a fixed test set, that kind of "
        "regression is invisible until a real user hits it. Comparing "
        "numbers against a file saved before the change makes the "
        "regression visible before release, not after."
    )


if __name__ == "__main__":
    main()
