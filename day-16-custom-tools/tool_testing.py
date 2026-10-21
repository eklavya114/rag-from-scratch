"""
tool_testing.py

A tool handed to an agent runs unattended, with no human double-checking
each call -- so it needs to be tested BEFORE that happens, the same way
you'd test any other function, but with extra attention to the failure
modes an agent is likely to trigger: missing arguments, wrong types, and
edge-case values like zero, negative numbers, and empty strings.
"""

from shopping_tools import add_to_cart, compare_prices, search_products
from support_tools import check_refund_eligibility, create_ticket, lookup_order


def run_test(description, fn, args, expect_ok):
    """
    Runs one test case and reports PASS/FAIL: calls the tool, checks
    whether the result's "ok" field matches what we expected, and
    treats a raised exception as an automatic failure (a well-designed
    tool should never raise on bad input -- it should return a
    structured error instead).
    """
    try:
        result = fn(*args)
        passed = result.get("ok") == expect_ok
        detail = result
    except Exception as exc:
        passed = False
        detail = f"raised {type(exc).__name__}: {exc} (a tool should never raise on bad input!)"

    status = "PASS" if passed else "FAIL"
    print(f"[{status}] {description}")
    print(f"       -> {detail}")
    return passed


def main():
    print("=== Testing Tools Before Giving Them to an Agent ===\n")

    results = []

    print("--- Valid input (expect success) ---")
    results.append(run_test("lookup_order with a real order ID", lookup_order, ["ORD-1001"], expect_ok=True))
    results.append(run_test("search_products with a real query", search_products, ["usb", None], expect_ok=True))

    print("\n--- Missing/empty input (expect a clear error) ---")
    results.append(run_test("lookup_order with an empty string", lookup_order, [""], expect_ok=False))
    results.append(run_test("create_ticket with an empty issue", create_ticket, ["", "normal"], expect_ok=False))

    print("\n--- Wrong types (expect a clear error) ---")
    results.append(run_test("add_to_cart with a string quantity", add_to_cart, ["SKU-1", "two"], expect_ok=False))
    results.append(run_test("search_products with a negative max_price", search_products, ["mouse", -5], expect_ok=False))

    print("\n--- Edge cases: zero, negative, empty ---")
    results.append(run_test("add_to_cart with quantity zero", add_to_cart, ["SKU-1", 0], expect_ok=False))
    results.append(run_test("add_to_cart with a negative quantity", add_to_cart, ["SKU-1", -3], expect_ok=False))
    results.append(run_test("compare_prices with the same product twice", compare_prices, ["SKU-1", "SKU-1"], expect_ok=True))
    results.append(run_test("check_refund_eligibility with an empty order_id", check_refund_eligibility, [""], expect_ok=False))

    passed_count = sum(results)
    total = len(results)
    print(f"\n=== Report: {passed_count}/{total} tests passed ===")

    if passed_count < total:
        print("At least one tool did not behave as expected -- fix it before wiring it into an agent.")
    else:
        print("All tools handled valid input, missing input, wrong types, and edge cases correctly.")

    print(
        "\nWhy this matters: an agent will eventually call every tool with "
        "bad arguments, whether from its own confusion or a bad decision "
        "upstream. Testing that in advance here is far cheaper than "
        "discovering it mid-run, when a tool crash can take down the whole "
        "agent loop instead of producing one handled error."
    )


if __name__ == "__main__":
    main()
