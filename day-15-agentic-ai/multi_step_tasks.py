"""
multi_step_tasks.py

Every example so far had a short, fairly linear task. Real tasks often
need to be broken into a planned sequence of steps, and the agent must
adapt when one of those steps fails instead of just stopping. This
file shows both: decomposing a complex task into a plan, and recovering
when a step in that plan doesn't work the first time.
"""


def plan_task(goal):
    """
    TASK DECOMPOSITION: breaks one high-level goal into an ordered list
    of concrete steps. A real agent might ask an LLM to produce this
    plan; here it's scripted so the example is deterministic.
    """
    if goal == "onboard new customer":
        return [
            {"step": "create_account", "args": ["new_customer@example.com"]},
            {"step": "send_welcome_email", "args": ["new_customer@example.com"]},
            {"step": "provision_database_record", "args": ["new_customer@example.com"]},
            {"step": "notify_sales_team", "args": ["new_customer@example.com"]},
        ]
    return []


# Each of these functions simulates a step in the plan. provision_database_record
# is deliberately flaky -- it fails the first time to demonstrate recovery.
_provision_attempts = {}


def create_account(email):
    return f"Account created for {email}."


def send_welcome_email(email):
    return f"Welcome email sent to {email}."


def provision_database_record(email):
    attempts = _provision_attempts.get(email, 0) + 1
    _provision_attempts[email] = attempts
    if attempts == 1:
        raise ConnectionError("database temporarily unavailable")
    return f"Database record provisioned for {email} (succeeded on attempt {attempts})."


def notify_sales_team(email):
    return f"Sales team notified about new customer {email}."


STEP_FUNCTIONS = {
    "create_account": create_account,
    "send_welcome_email": send_welcome_email,
    "provision_database_record": provision_database_record,
    "notify_sales_team": notify_sales_team,
}


def execute_plan(plan, max_retries_per_step=2):
    """
    Executes a plan step by step. If a step fails, retries it up to
    max_retries_per_step times before giving up on the WHOLE plan --
    this is the "adapt if something goes wrong" behavior: a transient
    failure doesn't need to kill the plan, but a step that keeps
    failing should stop it rather than silently skip ahead.
    """
    results = []
    for item in plan:
        step_name = item["step"]
        step_fn = STEP_FUNCTIONS[step_name]
        succeeded = False

        for attempt in range(1, max_retries_per_step + 1):
            try:
                result = step_fn(*item["args"])
                print(f"  [{step_name}] attempt {attempt}: succeeded -> {result}")
                results.append({"step": step_name, "attempt": attempt, "ok": True, "result": result})
                succeeded = True
                break
            except Exception as exc:
                print(f"  [{step_name}] attempt {attempt}: failed -> {type(exc).__name__}: {exc}")

        if not succeeded:
            print(f"  [{step_name}] gave up after {max_retries_per_step} attempts -- stopping the plan.")
            results.append({"step": step_name, "attempt": max_retries_per_step, "ok": False, "result": None})
            break

    return results


def main():
    print("=== Multi-Step Task Planning ===\n")

    goal = "onboard new customer"
    plan = plan_task(goal)

    print(f"Goal: {goal}")
    print(f"Decomposed into {len(plan)} steps:")
    for i, item in enumerate(plan, start=1):
        print(f"  {i}. {item['step']}({', '.join(item['args'])})")

    print("\nExecuting plan (one step fails on its first attempt and recovers on retry):\n")
    results = execute_plan(plan)

    completed = sum(1 for r in results if r["ok"])
    print(f"\nCompleted {completed}/{len(plan)} planned steps.")
    if completed == len(plan):
        print("Task finished successfully, including recovery from a transient failure.")
    else:
        print("Task did not complete -- a step failed past its retry budget.")


if __name__ == "__main__":
    main()
