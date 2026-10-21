"""
support_tools.py

Customer support tools built against a small in-memory dataset
(simulated -- no real order system or ticketing backend). Each tool
validates its inputs up front and returns a clear, structured error
instead of raising, matching Day 15's tool_examples.py convention: a
tool call always returns something usable, success or failure.
"""

import datetime

ORDERS = {
    "ORD-1001": {"status": "delivered", "ordered_on": "2026-09-20", "item": "Wireless Mouse", "damaged": True},
    "ORD-1002": {"status": "shipped", "ordered_on": "2026-10-15", "item": "Keyboard", "damaged": False},
    "ORD-1003": {"status": "delivered", "ordered_on": "2026-06-01", "item": "Monitor", "damaged": False},
}

TICKETS = []

TODAY = datetime.date(2026, 10, 21)


def lookup_order(order_id):
    """Looks up an order's status and details by its order ID (e.g. 'ORD-1001')."""
    if not isinstance(order_id, str) or not order_id.strip():
        return {"ok": False, "error": "order_id must be a non-empty string, e.g. 'ORD-1001'."}

    order = ORDERS.get(order_id)
    if order is None:
        return {"ok": False, "error": f"No order found with ID '{order_id}'."}

    return {"ok": True, "order_id": order_id, **order}


def check_refund_eligibility(order_id):
    """Checks whether an order is still eligible for a refund, using a 30-day-from-order-date rule."""
    lookup_result = lookup_order(order_id)
    if not lookup_result["ok"]:
        return lookup_result

    ordered_on = datetime.date.fromisoformat(lookup_result["ordered_on"])
    days_since_order = (TODAY - ordered_on).days
    eligible = days_since_order <= 30

    return {
        "ok": True,
        "order_id": order_id,
        "days_since_order": days_since_order,
        "eligible": eligible,
        "reason": "within the 30-day refund window" if eligible else "past the 30-day refund window",
    }


def create_ticket(issue, priority="normal"):
    """Creates a support ticket for an issue, with an optional priority ('low', 'normal', 'high')."""
    if not isinstance(issue, str) or not issue.strip():
        return {"ok": False, "error": "issue must be a non-empty description string."}

    valid_priorities = {"low", "normal", "high"}
    if priority not in valid_priorities:
        return {"ok": False, "error": f"priority must be one of {sorted(valid_priorities)}, got '{priority}'."}

    ticket_id = f"TICKET-{len(TICKETS) + 1001}"
    ticket = {"ticket_id": ticket_id, "issue": issue, "priority": priority}
    TICKETS.append(ticket)
    return {"ok": True, **ticket}


def main():
    print("=== Customer Support Tools ===\n")

    print("--- lookup_order ---")
    print("Good input:", lookup_order("ORD-1001"))
    print("Bad input: ", lookup_order("ORD-9999"))
    print("Bad input: ", lookup_order(""))

    print("\n--- check_refund_eligibility ---")
    print("Recent order (eligible):    ", check_refund_eligibility("ORD-1002"))
    print("Old order (not eligible):   ", check_refund_eligibility("ORD-1003"))
    print("Unknown order:              ", check_refund_eligibility("ORD-0000"))

    print("\n--- create_ticket ---")
    print("Good input:", create_ticket("Item arrived damaged", priority="high"))
    print("Bad input: ", create_ticket("", priority="high"))
    print("Bad input: ", create_ticket("Late delivery", priority="urgent"))

    print(f"\nTickets created this run: {len(TICKETS)}")
    for ticket in TICKETS:
        print(f"  {ticket}")


if __name__ == "__main__":
    main()
