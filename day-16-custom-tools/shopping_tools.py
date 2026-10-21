"""
shopping_tools.py

Shopping tools against a small in-memory catalog (simulated -- no real
store backend). Same convention as support_tools.py: validate inputs,
return a structured success or a clear structured error, never raise.
"""

CATALOG = {
    "SKU-1": {"name": "Wireless Mouse", "price": 25.00, "stock": 12},
    "SKU-2": {"name": "Mechanical Keyboard", "price": 89.00, "stock": 0},
    "SKU-3": {"name": "USB-C Hub", "price": 35.00, "stock": 7},
    "SKU-4": {"name": "Monitor Stand", "price": 45.00, "stock": 3},
}

CART = {}  # product_id -> quantity


def search_products(query, max_price=None):
    """Searches the catalog for products whose name matches the query, optionally capped at max_price."""
    if not isinstance(query, str) or not query.strip():
        return {"ok": False, "error": "query must be a non-empty string."}
    if max_price is not None and (not isinstance(max_price, (int, float)) or max_price < 0):
        return {"ok": False, "error": "max_price must be a non-negative number if given."}

    query_lower = query.lower()
    matches = []
    for product_id, product in CATALOG.items():
        if query_lower in product["name"].lower():
            if max_price is None or product["price"] <= max_price:
                matches.append({"product_id": product_id, **product})

    return {"ok": True, "query": query, "max_price": max_price, "results": matches}


def compare_prices(product_a, product_b):
    """Compares the prices of two products by ID and reports which is cheaper and by how much."""
    for pid in (product_a, product_b):
        if pid not in CATALOG:
            return {"ok": False, "error": f"Unknown product ID '{pid}'."}

    price_a = CATALOG[product_a]["price"]
    price_b = CATALOG[product_b]["price"]
    difference = abs(price_a - price_b)

    if price_a == price_b:
        return {"ok": True, "cheaper": None, "difference": 0.0, "message": "Both products are the same price."}

    cheaper_id = product_a if price_a < price_b else product_b
    return {
        "ok": True,
        "cheaper": cheaper_id,
        "difference": round(difference, 2),
        "message": f"{CATALOG[cheaper_id]['name']} ({cheaper_id}) is cheaper by ${difference:.2f}.",
    }


def add_to_cart(product_id, quantity):
    """Adds a quantity of a product to the cart, validating that it's in stock first."""
    if product_id not in CATALOG:
        return {"ok": False, "error": f"Unknown product ID '{product_id}'."}
    if not isinstance(quantity, int) or quantity <= 0:
        return {"ok": False, "error": "quantity must be a positive integer."}

    available = CATALOG[product_id]["stock"]
    if quantity > available:
        return {"ok": False, "error": f"Only {available} unit(s) of '{CATALOG[product_id]['name']}' in stock, requested {quantity}."}

    CART[product_id] = CART.get(product_id, 0) + quantity
    return {"ok": True, "product_id": product_id, "quantity_added": quantity, "cart_total_for_item": CART[product_id]}


def main():
    print("=== Shopping Tools ===\n")

    print("--- search_products ---")
    print("Good input:", search_products("usb"))
    print("With price cap:", search_products("mouse", max_price=20))
    print("Bad input: ", search_products(""))

    print("\n--- compare_prices ---")
    print(compare_prices("SKU-1", "SKU-2"))
    print("Unknown product:", compare_prices("SKU-1", "SKU-99"))

    print("\n--- add_to_cart ---")
    print("Good input:", add_to_cart("SKU-3", 2))
    print("Out of stock (fails on purpose):", add_to_cart("SKU-2", 1))
    print("Bad quantity:", add_to_cart("SKU-1", -1))

    print(f"\nFinal cart: {CART}")


if __name__ == "__main__":
    main()
