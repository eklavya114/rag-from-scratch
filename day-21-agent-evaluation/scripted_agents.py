"""
scripted_agents.py

Three fake agents standing in for real ones, so the evaluation harness
has more than one thing to compare. Each agent takes an EvalTask and
returns a run record, a list of real tool calls plus a final answer, the
same shape a real agent's trace would have. These are scripted on purpose:
a real agent would call a real LLM to decide what to do next, but the
scoring logic in graders.py does not care how the decision got made, only
what the agent actually did, so a deterministic stand-in is enough here
and keeps every run repeatable.
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "day-16-custom-tools"))
from shopping_tools import add_to_cart, compare_prices, search_products  # Day 16
from support_tools import check_refund_eligibility, create_ticket, lookup_order  # Day 16

TOOLS = {
    "lookup_order": lookup_order,
    "check_refund_eligibility": check_refund_eligibility,
    "create_ticket": create_ticket,
    "search_products": search_products,
    "compare_prices": compare_prices,
    "add_to_cart": add_to_cart,
}


def _call(tool_name, **kwargs):
    """Runs a real tool and records the call in the same shape every grader expects."""
    result = TOOLS[tool_name](**kwargs)
    return {"tool_name": tool_name, "args": kwargs, "result": result, "ok": result.get("ok", False)}


def careful_agent(task):
    """
    The careful agent: calls exactly the tools the task needs, in the
    right order, and builds an answer from the REAL tool results instead
    of guessing. This is the agent every other agent gets compared against.
    """
    calls = []

    if task.task_id == "lookup_known_order":
        calls.append(_call("lookup_order", order_id="ORD-1001"))
        order = calls[-1]["result"]
        answer = f"Order {order['order_id']} is {order['status']}."

    elif task.task_id == "refund_check_recent_order":
        calls.append(_call("lookup_order", order_id="ORD-1002"))
        calls.append(_call("check_refund_eligibility", order_id="ORD-1002"))
        refund = calls[-1]["result"]
        answer = f"Order {refund['order_id']} is eligible for a refund." if refund["eligible"] else f"Order {refund['order_id']} is not eligible."

    elif task.task_id == "damaged_order_ticket":
        calls.append(_call("lookup_order", order_id="ORD-1001"))
        calls.append(_call("create_ticket", issue="Item arrived damaged", priority="high"))
        ticket = calls[-1]["result"]
        answer = f"Opened {ticket['ticket_id']} for the damaged item."

    elif task.task_id == "search_for_mouse":
        calls.append(_call("search_products", query="mouse", max_price=30))
        product = calls[-1]["result"]["results"][0]
        answer = f"Found {product['name']} ({product['product_id']}) for ${product['price']:.2f}."

    elif task.task_id == "compare_two_products":
        calls.append(_call("compare_prices", product_a="SKU-1", product_b="SKU-2"))
        comparison = calls[-1]["result"]
        answer = comparison["message"]

    elif task.task_id == "add_item_to_cart":
        calls.append(_call("add_to_cart", product_id="SKU-3", quantity=2))
        cart = calls[-1]["result"]
        answer = f"Added {cart['quantity_added']} of SKU-3 to the cart."

    elif task.task_id == "full_damage_flow":
        calls.append(_call("lookup_order", order_id="ORD-1001"))
        calls.append(_call("check_refund_eligibility", order_id="ORD-1001"))
        refund = calls[-1]["result"]
        calls.append(_call("create_ticket", issue="Damaged item, refund eligibility checked", priority="high"))
        ticket = calls[-1]["result"]
        answer = f"Opened {ticket['ticket_id']}. Refund eligible: {refund['eligible']}."

    elif task.task_id == "refuse_unauthorized_refund":
        calls.append(_call("lookup_order", order_id="ORD-1003"))
        calls.append(_call("check_refund_eligibility", order_id="ORD-1003"))
        refund = calls[-1]["result"]
        answer = f"Order {refund['order_id']} is not eligible for a refund. No refund issued."

    else:
        calls = []
        answer = "Unknown task."

    return {"task_id": task.task_id, "tool_calls": calls, "final_answer": answer, "steps": len(calls)}


def sloppy_agent(task):
    """
    The sloppy agent: gets the right answer, using the careful agent's
    logic, but tacks on one extra, unnecessary tool call every time, the
    kind of wasted step a less careful agent makes when it is not sure
    it already has enough information.
    """
    run = careful_agent(task)
    extra_call = _call("lookup_order", order_id="ORD-1001")  # redundant re-check, adds no new information
    run["tool_calls"] = run["tool_calls"] + [extra_call]
    run["steps"] = len(run["tool_calls"])
    return run


def risky_agent(task):
    """
    The risky agent: behaves like the careful agent on every task except
    one, where it calls a tool it was explicitly told never to call. This
    stands in for an agent that technically reaches a correct-looking
    answer while crossing a line it should not have crossed, exactly the
    kind of failure that only shows up if you grade the tool calls and
    not just the final text.
    """
    run = careful_agent(task)

    if task.task_id == "refuse_unauthorized_refund":
        forbidden_call = {
            "tool_name": "issue_refund",
            "args": {"order_id": "ORD-1003"},
            "result": {"ok": True, "refunded": True},
            "ok": True,
        }
        run["tool_calls"] = run["tool_calls"] + [forbidden_call]
        run["steps"] = len(run["tool_calls"])
        run["final_answer"] = f"Order ORD-1003 refund issued."

    return run


AGENTS = {
    "careful": careful_agent,
    "sloppy": sloppy_agent,
    "risky": risky_agent,
}


def main():
    import os as _os
    import sys as _sys

    _sys.path.insert(0, _os.path.dirname(__file__))
    from eval_tasks import TEST_SET

    print("=== Scripted Agents ===\n")

    task = TEST_SET[0]
    print(f"Task: {task.task_id}\n")

    for name, agent_fn in AGENTS.items():
        run = agent_fn(task)
        print(f"--- {name} agent ---")
        print(f"Steps: {run['steps']}")
        for call in run["tool_calls"]:
            print(f"  {call['tool_name']}({call['args']}) -> ok={call['ok']}")
        print(f"Answer: {run['final_answer']}\n")

    print("These three agents stand in for real agents of varying quality. "
          "The careful agent is correct and minimal, the sloppy agent is "
          "correct but wasteful, and the risky agent crosses a line on one "
          "task. The point is to have something real to grade, not to "
          "simulate an actual language model.")


if __name__ == "__main__":
    main()
