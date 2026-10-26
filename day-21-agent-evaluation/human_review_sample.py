"""
human_review_sample.py

Automatic graders are fast and consistent, but they only check what they
were explicitly written to check. They cannot judge tone, cannot tell if
an action was technically allowed but a bad idea anyway, and cannot spot
a new kind of problem nobody thought to grade for yet. This file samples
a fixed number of runs for a human to look at, weighted toward failures
and borderline passes, since those are the runs most likely to teach you
something the automatic graders missed.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from eval_tasks import TEST_SET
from graders import grade_run
from scripted_agents import AGENTS

SAMPLE_SIZE = 4


def is_borderline(grade):
    """A run counts as borderline if it technically passed but only barely: a lot of steps, or a nonzero tool error rate, even though nothing counted as an outright failure."""
    return grade.task_success and not grade.forbidden_call_made and (grade.efficiency < 0.8 or grade.tool_error_rate > 0)


def is_outright_failure(grade):
    return not grade.task_success or grade.forbidden_call_made


def collect_all_runs():
    """Collects every (agent_name, task, run, grade) combination across all agents and tasks, the full pool to sample from."""
    all_runs = []
    for agent_name, agent_fn in AGENTS.items():
        for task in TEST_SET:
            run = agent_fn(task)
            grade = grade_run(run, task, agent_name)
            all_runs.append((agent_name, task, run, grade))
    return all_runs


def sample_for_review(all_runs, sample_size=SAMPLE_SIZE):
    """
    Builds a review sample weighted toward problems: every outright
    failure is included first, then borderline passes fill in the rest
    of the sample, and only if there is still room left does a plain,
    clean pass get added. This puts a human's limited attention where it
    is most likely to catch something the graders missed.
    """
    failures = [r for r in all_runs if is_outright_failure(r[3])]
    borderline = [r for r in all_runs if is_borderline(r[3])]
    clean = [r for r in all_runs if not is_outright_failure(r[3]) and not is_borderline(r[3])]

    sample = []
    sample.extend(failures[:sample_size])
    remaining = sample_size - len(sample)
    sample.extend(borderline[:remaining])
    remaining = sample_size - len(sample)
    sample.extend(clean[:remaining])

    return sample[:sample_size]


def print_review_sheet(sample):
    for agent_name, task, run, grade in sample:
        print(f"Task: {task.task_id} | Agent: {agent_name}")
        print(f"  Goal: {task.goal}")
        trace_summary = ", ".join(f"{c['tool_name']}(ok={c['ok']})" for c in run["tool_calls"]) or "(no tool calls)"
        print(f"  Trace: {trace_summary}")
        print(f"  Final answer: {run['final_answer']}")
        print(f"  Automatic grades: success={grade.task_success}, tools_correct={grade.tools_correct}, "
              f"forbidden_call_made={grade.forbidden_call_made}, efficiency={grade.efficiency:.2f}, "
              f"tool_error_rate={grade.tool_error_rate:.2f}")
        print("  Human score: ______ (1-5, with notes)")
        print()


def main():
    print("=== Human Review Sample ===\n")

    all_runs = collect_all_runs()
    sample = sample_for_review(all_runs)

    print(f"Sampled {len(sample)} of {len(all_runs)} total runs for human review.\n")
    print_review_sheet(sample)

    print(
        "Why automatic graders miss some things: the graders here can "
        "check whether a keyword showed up, whether a tool was called, "
        "and whether a forbidden tool was touched. They cannot tell if the "
        "agent's tone was rude, if an allowed action was still a bad call "
        "in context, or if the final answer is technically correct but "
        "confusing to an actual customer. That is the gap human review "
        "fills in, and weighting the sample toward failures and borderline "
        "passes is what makes limited human attention worth spending."
    )


if __name__ == "__main__":
    main()
