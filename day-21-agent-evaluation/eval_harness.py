"""
eval_harness.py

Runs the ENTIRE fixed test set against one agent, grades every run, and
aggregates the results into a summary. Then runs all three scripted
agents through the same harness and prints their summaries side by side,
which is the actual point: comparing agents only means something if they
were run on exactly the same tasks.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from eval_tasks import TEST_SET
from graders import grade_run
from scripted_agents import AGENTS


def run_harness(agent_fn, agent_name, tasks=TEST_SET):
    """Runs one agent on every task in the test set and returns a list of GradeResult objects, one per task."""
    grades = []
    for task in tasks:
        run = agent_fn(task)
        grade = grade_run(run, task, agent_name)
        grades.append(grade)
    return grades


def summarize(grades):
    """
    Aggregates a list of per-task GradeResults into a few headline
    numbers. These are the metrics you would track release over release:
    success rate, how many hard fails happened, average steps, and tool
    error rate.
    """
    total = len(grades)
    task_success_rate = sum(1 for g in grades if g.task_success) / total
    forbidden_call_count = sum(1 for g in grades if g.forbidden_call_made)
    average_steps = sum(g.steps_taken for g in grades) / total
    average_tool_error_rate = sum(g.tool_error_rate for g in grades) / total
    average_efficiency = sum(g.efficiency for g in grades) / total

    return {
        "task_success_rate": task_success_rate,
        "forbidden_call_count": forbidden_call_count,
        "average_steps": average_steps,
        "average_tool_error_rate": average_tool_error_rate,
        "average_efficiency": average_efficiency,
    }


def print_task_table(grades):
    print(f"{'task_id':<28}{'success':<9}{'tools_ok':<10}{'forbidden':<11}{'steps':<7}{'efficiency':<11}")
    for g in grades:
        print(f"{g.task_id:<28}{str(g.task_success):<9}{str(g.tools_correct):<10}{str(g.forbidden_call_made):<11}{g.steps_taken:<7}{g.efficiency:<11.2f}")


def main():
    print("=== Agent Evaluation Harness ===\n")
    print(f"Running {len(TEST_SET)} fixed tasks against every agent. Same tasks, every time.\n")

    all_summaries = {}

    for agent_name, agent_fn in AGENTS.items():
        print(f"--- {agent_name} agent, per-task results ---")
        grades = run_harness(agent_fn, agent_name)
        print_task_table(grades)
        summary = summarize(grades)
        all_summaries[agent_name] = summary
        print()

    print("=== Side-by-side summary ===\n")
    print(f"{'metric':<26}" + "".join(f"{name:<12}" for name in AGENTS))
    print(f"{'task_success_rate':<26}" + "".join(f"{all_summaries[n]['task_success_rate']:<12.0%}" for n in AGENTS))
    print(f"{'forbidden_call_count':<26}" + "".join(f"{all_summaries[n]['forbidden_call_count']:<12}" for n in AGENTS))
    print(f"{'average_steps':<26}" + "".join(f"{all_summaries[n]['average_steps']:<12.2f}" for n in AGENTS))
    print(f"{'average_tool_error_rate':<26}" + "".join(f"{all_summaries[n]['average_tool_error_rate']:<12.2f}" for n in AGENTS))
    print(f"{'average_efficiency':<26}" + "".join(f"{all_summaries[n]['average_efficiency']:<12.2f}" for n in AGENTS))

    print(
        "\nWhy run the same tests every time: careful and sloppy both reach "
        "a perfect task success rate here, so success rate alone cannot "
        "tell them apart. Only running the identical test set and looking "
        "at average_steps and average_efficiency reveals that sloppy is "
        "doing more work for the same result. And only forbidden_call_count "
        "reveals that risky is not actually safe to ship, even though its "
        "task success rate is close to the others."
    )


if __name__ == "__main__":
    main()
