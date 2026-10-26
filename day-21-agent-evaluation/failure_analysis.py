"""
failure_analysis.py

Grading tells you THAT something failed. This file digs into WHY, by
grouping failures by reason: a missing expected tool call, a wrong final
answer, a forbidden tool call, or too many steps. Grouped failures are
what turn "something is wrong" into an actual list of bugs worth fixing,
and each one is also a candidate for a new entry in eval_tasks.py so it
gets caught automatically next time.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from eval_tasks import TEST_SET
from graders import grade_run
from scripted_agents import AGENTS

MAX_REASONABLE_STEPS = 4


def classify_failure(grade):
    """
    Returns the single most important reason a run failed, checked in
    order of severity: a forbidden call is always reported first since
    it is a hard fail regardless of anything else, followed by a missing
    tool, a wrong answer, and finally taking too many steps.
    """
    if grade.forbidden_call_made:
        return "forbidden_tool"
    if not grade.tools_correct:
        return "missing_tool"
    if not grade.task_success:
        return "wrong_answer"
    if grade.steps_taken > MAX_REASONABLE_STEPS:
        return "too_many_steps"
    return None  # not a failure


def collect_failures(agent_fn, agent_name, tasks=TEST_SET):
    """Runs an agent on every task and returns (task, run, grade, reason) for every run that failed on at least one criterion."""
    failures = []
    for task in tasks:
        run = agent_fn(task)
        grade = grade_run(run, task, agent_name)
        reason = classify_failure(grade)
        if reason is not None:
            failures.append((task, run, grade, reason))
    return failures


def group_by_reason(failures):
    groups = {}
    for task, run, grade, reason in failures:
        groups.setdefault(reason, []).append(task.task_id)
    return groups


def print_full_trace(task, run, grade, reason):
    print(f"Task: {task.task_id}")
    print(f"Goal: {task.goal}")
    print(f"Failure reason: {reason}\n")
    print("Trace:")
    for i, call in enumerate(run["tool_calls"], start=1):
        status = "ok" if call["ok"] else "FAILED"
        print(f"  Step {i}: {call['tool_name']}({call['args']}) -> {status}: {call['result']}")
    print(f"Final answer: {run['final_answer']}\n")

    print("What went wrong:")
    if reason == "forbidden_tool":
        forbidden = [c["tool_name"] for c in run["tool_calls"] if c["tool_name"] in task.forbidden_tools]
        print(f"  Called a forbidden tool: {forbidden}. This tool should never be called for this task, regardless of the outcome.")
    elif reason == "missing_tool":
        called = {c["tool_name"] for c in run["tool_calls"]}
        missing = [t for t in task.expected_tools if t not in called]
        print(f"  Never called required tool(s): {missing}. The final answer may still look fine without the actual check being made.")
    elif reason == "wrong_answer":
        print(f"  Final answer is missing expected keywords: {task.expected_answer_keywords}.")
    elif reason == "too_many_steps":
        print(f"  Took {grade.steps_taken} steps, more than the {MAX_REASONABLE_STEPS}-step threshold used here.")


def main():
    print("=== Failure Analysis ===\n")

    all_failures = []
    for agent_name, agent_fn in AGENTS.items():
        failures = collect_failures(agent_fn, agent_name)
        all_failures.extend(failures)

    groups = group_by_reason(all_failures)

    print("--- Failures grouped by reason (across all three agents) ---")
    for reason, task_ids in sorted(groups.items(), key=lambda pair: len(pair[1]), reverse=True):
        print(f"  {reason:<16} count={len(task_ids):<3} tasks={task_ids}")

    if not all_failures:
        print("  No failures found.")
        return

    print("\n--- Most common failure reason ---")
    most_common_reason = max(groups, key=lambda r: len(groups[r]))
    print(f"  '{most_common_reason}' with {len(groups[most_common_reason])} occurrence(s)")

    print("\n--- One full failing trace ---\n")
    print_full_trace(*all_failures[0])

    print(
        "Why this matters: a failure reason that keeps showing up across "
        "multiple agents, like a specific task tending to confuse every "
        "agent the same way, points at a problem with the TASK itself, or "
        "at a genuinely hard case worth adding a second, related task for, "
        "so the exact same failure gets caught automatically the next time "
        "this test set runs."
    )


if __name__ == "__main__":
    main()
