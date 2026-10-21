"""
tool_design_mistakes.py

Four common tool design mistakes, each shown in a "bad" version that
actually runs (so the confusion is demonstrated concretely, not just
asserted) and a "fixed" version alongside it.
"""


# ============================================================
# MISTAKE 1: a tool that does too many things
# ============================================================

def handle_order_bad(order_id, action, refund_amount=None):
    """Does something to an order -- what, depends on a hidden 'action' flag the agent has to already know about."""
    if action == "lookup":
        return f"Order {order_id} status: shipped"
    elif action == "refund":
        return f"Refunded ${refund_amount} for order {order_id}"
    elif action == "cancel":
        return f"Order {order_id} cancelled"
    return "Unknown action"


# FIX: split into three tools, each with one job and a name that says exactly what it does.
def lookup_order_status(order_id):
    """Looks up the current status of an order."""
    return f"Order {order_id} status: shipped"


def refund_order(order_id, amount):
    """Issues a refund of the given amount for an order."""
    return f"Refunded ${amount} for order {order_id}"


def cancel_order(order_id):
    """Cancels an order."""
    return f"Order {order_id} cancelled"


# ============================================================
# MISTAKE 2: a vague tool name
# ============================================================

def process(x):
    """Processes something. (Processes WHAT? Nothing about the name or signature says.)"""
    return x.upper()


# FIX: a name that says exactly what transformation happens.
def convert_to_uppercase(text):
    """Converts the given text to uppercase."""
    return text.upper()


# ============================================================
# MISTAKE 3: unclear parameters
# ============================================================

def do_thing(x, y, z):
    """Does a thing with three unlabeled values. An agent has no way to know what to pass for x, y, or z."""
    return x * y + z


# FIX: parameter names that describe their role, plus a docstring that explains the formula.
def calculate_total_with_tax(price, tax_rate, shipping_cost):
    """Calculates a final total: price * (1 + tax_rate) + shipping_cost."""
    return price * (1 + tax_rate) + shipping_cost


# ============================================================
# MISTAKE 4: a tool that returns a messy, unstructured result
# ============================================================

def get_customer_info_bad(customer_id):
    """Returns customer info as one mashed-together string the caller has to parse back apart."""
    return f"name:Jordan Lee,plan:pro,signup_year:2024,customer_id:{customer_id}"


# FIX: return a structured dict -- no parsing required on the other end.
def get_customer_info(customer_id):
    """Returns customer info as a structured dict."""
    return {"customer_id": customer_id, "name": "Jordan Lee", "plan": "pro", "signup_year": 2024}


def main():
    print("=== Tool Design Mistakes, and Their Fixes ===\n")

    print("--- Mistake 1: a tool that does too many things ---")
    print(f"Bad:   handle_order_bad('ORD-1', 'refund', refund_amount=20) -> {handle_order_bad('ORD-1', 'refund', refund_amount=20)}")
    print("  Why this confuses an agent: the tool's description can't explain what it")
    print("  does without listing every possible 'action' value, and a wrong or missing")
    print("  action silently does nothing instead of failing clearly.")
    print(f"Fixed: lookup_order_status('ORD-1') -> {lookup_order_status('ORD-1')}")
    print(f"Fixed: refund_order('ORD-1', 20) -> {refund_order('ORD-1', 20)}")
    print(f"Fixed: cancel_order('ORD-1') -> {cancel_order('ORD-1')}\n")

    print("--- Mistake 2: a vague tool name ---")
    print(f"Bad:   process('hello') -> {process('hello')}")
    print("  Why this confuses an agent: 'process' could mean anything -- an agent")
    print("  choosing between tools has no way to tell this one converts case.")
    print(f"Fixed: convert_to_uppercase('hello') -> {convert_to_uppercase('hello')}\n")

    print("--- Mistake 3: unclear parameters ---")
    print(f"Bad:   do_thing(100, 0.08, 5) -> {do_thing(100, 0.08, 5)}")
    print("  Why this confuses an agent: x, y, and z give no hint about what values")
    print("  to pass or in what order -- the agent would have to guess.")
    print(f"Fixed: calculate_total_with_tax(100, 0.08, 5) -> {calculate_total_with_tax(100, 0.08, 5)}\n")

    print("--- Mistake 4: a messy, unstructured result ---")
    print(f"Bad:   get_customer_info_bad('CUST-1') -> {get_customer_info_bad('CUST-1')!r}")
    print("  Why this confuses an agent: it would need to parse this string back apart")
    print("  itself, guessing at the separator and field order every time.")
    print(f"Fixed: get_customer_info('CUST-1') -> {get_customer_info('CUST-1')}")


if __name__ == "__main__":
    main()
