"""
agent_evaluation.py

"The agent seems to work" isn't a metric. This file scores agent runs
on a small test set using concrete numbers: did it finish the task,
how many steps did it take, and how often did its tool calls fail --
the same measure-before-trusting discipline used for retrieval quality
back on Day 8.
"""


def run_agent_on_task(task):
    """
    Simulates running an agent on a task and recording what happened.
    Each task dict describes a scripted outcome (steps taken, whether
    it finished, how many tool errors occurred) standing in for a real
    agent trace -- the scoring logic below is what matters here, not
    how the trace was produced.
    """
    return {
        "task_id": task["task_id"],
        "completed": task["completed"],
        "steps_taken": task["steps_taken"],
        "tool_errors": task["tool_errors"],
    }


TEST_SET = [
    {"task_id": "lookup_capital", "completed": True, "steps_taken": 2, "tool_errors": 0},
    {"task_id": "book_flight", "completed": True, "steps_taken": 5, "tool_errors": 1},
    {"task_id": "cancel_subscription", "completed": False, "steps_taken": 10, "tool_errors": 3},
    {"task_id": "summarize_document", "completed": True, "steps_taken": 3, "tool_errors": 0},
    {"task_id": "compare_prices", "completed": True, "steps_taken": 4, "tool_errors": 1},
]


def task_completion_rate(results):
    """COMPLETION RATE: the most basic question -- out of everything the agent attempted, how much did it actually finish?"""
    return sum(1 for r in results if r["completed"]) / len(results)


def average_steps(results):
    """EFFICIENCY: fewer steps for the same outcome is better -- an agent that takes 10 steps to do what another does in 3 is burning more time and (with a real LLM) more money."""
    return sum(r["steps_taken"] for r in results) / len(results)


def tool_error_rate(results):
    """Average number of tool failures per task -- a proxy for how often the agent chose bad arguments or hit flaky tools."""
    return sum(r["tool_errors"] for r in results) / len(results)


def efficiency_score(result):
    """A simple per-task score: completed tasks are rewarded, and each step/error taken chips away at the score -- cruder than a real cost model, but enough to RANK tasks by how cleanly they went."""
    if not result["completed"]:
        return 0.0
    return max(0.0, 1.0 - 0.05 * result["steps_taken"] - 0.1 * result["tool_errors"])


def evaluate(results):
    completion = task_completion_rate(results)
    steps = average_steps(results)
    errors = tool_error_rate(results)
    scores = {r["task_id"]: efficiency_score(r) for r in results}
    return {
        "completion_rate": completion,
        "average_steps": steps,
        "tool_error_rate": errors,
        "per_task_scores": scores,
    }


def main():
    print("=== Agent Evaluation ===\n")

    results = [run_agent_on_task(task) for task in TEST_SET]

    print("--- Per-task results ---")
    for r in results:
        status = "DONE" if r["completed"] else "FAILED"
        print(f"  {r['task_id']:<22} {status:<7} steps={r['steps_taken']:<3} tool_errors={r['tool_errors']}")

    report = evaluate(results)

    print("\n--- Aggregate metrics ---")
    print(f"Task completion rate: {report['completion_rate']:.0%}")
    print(f"Average steps per task: {report['average_steps']:.1f}")
    print(f"Average tool errors per task: {report['tool_error_rate']:.1f}")

    print("\n--- Per-task efficiency scores (0-1, higher is better) ---")
    for task_id, score in sorted(report["per_task_scores"].items(), key=lambda pair: pair[1], reverse=True):
        print(f"  {task_id:<22} {score:.2f}")

    worst_task = min(report["per_task_scores"], key=report["per_task_scores"].get)
    print(
        f"\nLowest-scoring task: '{worst_task}' -- worth investigating first, "
        f"since it represents either a failed task or one that succeeded only "
        f"after an unusually high number of steps/errors."
    )


if __name__ == "__main__":
    main()
