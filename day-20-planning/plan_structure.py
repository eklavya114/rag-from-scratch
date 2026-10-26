"""
plan_structure.py

Defines what a plan actually is: a Step (one tool call, with its
arguments and what it depends on) and a Plan (a goal plus an ordered
list of Steps). validate_plan() checks a plan before anything runs:
every tool it names actually exists, every dependency it names points
at a real step, and there is no circular dependency that would make
execution impossible.
"""

from dataclasses import dataclass, field


@dataclass
class Step:
    """One step in a plan: which tool to call, with what arguments, and which earlier steps (by id) must finish first."""
    step_id: str
    description: str
    tool_name: str
    arguments: dict
    depends_on: list = field(default_factory=list)


@dataclass
class Plan:
    """A goal and the ordered list of Steps meant to achieve it."""
    goal: str
    steps: list


def validate_plan(plan, known_tools):
    """
    Checks a plan for three concrete problems before it ever runs:
      1. every step's tool_name is one of known_tools,
      2. every id listed in depends_on refers to a step that actually exists in the plan,
      3. there is no cycle in the dependency graph (a step that depends on itself, directly or indirectly).
    Returns (True, None) if the plan is sound, or (False, error_message) describing the first problem found.
    """
    step_ids = {step.step_id for step in plan.steps}

    for step in plan.steps:
        if step.tool_name not in known_tools:
            return False, f"Step '{step.step_id}' uses unknown tool '{step.tool_name}'."

        for dep_id in step.depends_on:
            if dep_id not in step_ids:
                return False, f"Step '{step.step_id}' depends on '{dep_id}', which is not a step in this plan."

    cycle = find_cycle(plan.steps)
    if cycle:
        return False, f"Circular dependency detected: {' -> '.join(cycle)}."

    return True, None


def find_cycle(steps):
    """
    Depth-first search for a cycle in the dependency graph. Returns the
    cycle as a list of step ids if one exists, or None if the graph is
    acyclic. A plan with a cycle can never be executed in dependency
    order, since every step in the cycle is waiting on another step in
    the same cycle to finish first.
    """
    steps_by_id = {step.step_id: step for step in steps}
    visiting = set()
    visited = set()

    def visit(step_id, path):
        if step_id in visiting:
            return path[path.index(step_id):] + [step_id]
        if step_id in visited:
            return None

        visiting.add(step_id)
        for dep_id in steps_by_id[step_id].depends_on:
            if dep_id in steps_by_id:
                result = visit(dep_id, path + [step_id])
                if result:
                    return result
        visiting.discard(step_id)
        visited.add(step_id)
        return None

    for step in steps:
        result = visit(step.step_id, [])
        if result:
            return result
    return None


def main():
    print("=== Plan Structure and Validation ===\n")

    known_tools = {"lookup_order", "check_refund_eligibility", "create_ticket"}

    valid_plan = Plan(
        goal="Handle damaged order ORD-1001",
        steps=[
            Step("s1", "Look up the order", "lookup_order", {"order_id": "ORD-1001"}),
            Step("s2", "Check refund eligibility", "check_refund_eligibility", {"order_id": "ORD-1001"}, depends_on=["s1"]),
            Step("s3", "Create a ticket if needed", "create_ticket", {"issue": "Damaged item", "priority": "high"}, depends_on=["s2"]),
        ],
    )

    print("--- A valid plan ---")
    is_valid, error = validate_plan(valid_plan, known_tools)
    print(f"Valid: {is_valid}" + (f", {error}" if error else ""))

    broken_plan_unknown_tool = Plan(
        goal="Handle damaged order ORD-1001",
        steps=[
            Step("s1", "Look up the order", "lookup_order", {"order_id": "ORD-1001"}),
            Step("s2", "Process the item", "process_item", {"order_id": "ORD-1001"}, depends_on=["s1"]),
        ],
    )

    print("\n--- A plan using an unknown tool ---")
    is_valid, error = validate_plan(broken_plan_unknown_tool, known_tools)
    print(f"Valid: {is_valid}" + (f", {error}" if error else ""))

    broken_plan_cycle = Plan(
        goal="Handle damaged order ORD-1001",
        steps=[
            Step("s1", "Look up the order", "lookup_order", {"order_id": "ORD-1001"}, depends_on=["s2"]),
            Step("s2", "Check refund eligibility", "check_refund_eligibility", {"order_id": "ORD-1001"}, depends_on=["s1"]),
        ],
    )

    print("\n--- A plan with a circular dependency ---")
    is_valid, error = validate_plan(broken_plan_cycle, known_tools)
    print(f"Valid: {is_valid}" + (f", {error}" if error else ""))

    print(
        "\nField notes: step_id is how other steps refer to this one. "
        "tool_name and arguments are exactly what gets called. depends_on "
        "is the ordering constraint, a step never runs before everything "
        "in its depends_on list has finished. A plan is only as trustworthy "
        "as these three checks say it is, since every one of them is a way "
        "execution could otherwise get stuck or crash partway through."
    )


if __name__ == "__main__":
    main()
