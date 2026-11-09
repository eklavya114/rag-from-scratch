"""
knowledge_base.py

The document set this complete system answers from: a small support
knowledge base about orders, refunds, shipping, returns, and backorders,
the same domain Day 28's adaptation work used. In a real system, these
documents would come from a real source, a help center's published
articles, a wiki, a ticketing system's resolved-ticket history, pulled
and refreshed on a schedule, not hand-typed into a Python file. Here they
are hand-typed specifically so the whole system can be read, run, and
understood without needing any external data source at all.
"""

RAW_DOCUMENTS = [
    {"id": 1, "title": "How to Request an RMA", "text": "To return an item, request a Return Merchandise Authorization (RMA) from your account page. An RMA number must be included with any returned package, or the warehouse cannot process it.", "metadata": {"category": "returns", "updated": "2026-09-01"}},
    {"id": 2, "title": "Refund Processing Times", "text": "Refunds are issued to the original payment method within 5 to 7 business days after the returned item is received and inspected at the warehouse.", "metadata": {"category": "refunds", "updated": "2026-08-15"}},
    {"id": 3, "title": "What Is a Chargeback", "text": "A chargeback happens when a customer disputes a charge directly with their bank or card issuer instead of contacting support first. Chargebacks can take 30 to 90 days to resolve and may involve a fee.", "metadata": {"category": "refunds", "updated": "2026-07-20"}},
    {"id": 4, "title": "Backorder Status Explained", "text": "A backorder means an item is temporarily out of stock but will ship once restocked. Backordered items show an estimated ship date on the order page, updated weekly.", "metadata": {"category": "shipping", "updated": "2026-09-10"}},
    {"id": 5, "title": "Shipping Carrier Options", "text": "Orders ship via standard ground, expedited, or overnight carriers. Expedited and overnight shipping cost more but arrive faster, standard ground is the default free option.", "metadata": {"category": "shipping", "updated": "2026-06-01"}},
    {"id": 6, "title": "Tracking a Lost Package", "text": "If a tracking number shows delivered but the package never arrived, file a lost package claim with support within 14 days, the carrier investigates before a replacement ships.", "metadata": {"category": "shipping", "updated": "2026-08-01"}},
    {"id": 7, "title": "Order Cancellation Window", "text": "Orders can be cancelled for free within one hour of placing them. After that window, the order may have already entered fulfillment and cannot be cancelled.", "metadata": {"category": "orders", "updated": "2026-05-15"}},
    {"id": 8, "title": "Return Window for Items", "text": "Most items can be returned within 30 days of delivery for a full refund. Final sale items and opened electronics are not eligible for return.", "metadata": {"category": "returns", "updated": "2026-09-05"}},
    {"id": 9, "title": "Partial Shipment Explained", "text": "A partial shipment happens when an order with multiple items ships in separate packages because one item was backordered. Each shipment gets its own tracking number.", "metadata": {"category": "shipping", "updated": "2026-07-01"}},
    {"id": 10, "title": "Store Credit Versus Refund", "text": "Customers can choose store credit instead of a refund to the original payment method. Store credit is issued instantly, while a refund takes 5 to 7 business days.", "metadata": {"category": "refunds", "updated": "2026-08-20"}},
    {"id": 11, "title": "Duplicate Order Entry (bad data)", "text": "", "metadata": {"category": "orders", "updated": "2026-01-01"}},
    {"id": 2, "title": "Accidental Duplicate Id (bad data)", "text": "This document reuses an id already claimed by a valid document above.", "metadata": {"category": "refunds", "updated": "2026-01-01"}},
]


def load_knowledge_base(raw_documents=RAW_DOCUMENTS):
    """
    Cleans the raw document list and skips bad entries: empty text, and
    duplicate ids. Returns (clean_documents, skip_report), where the
    report explains exactly why each skipped document was skipped,
    matching Day 28's validate_document discipline for catching bad
    data before it ever reaches the index rather than crashing on it.
    """
    seen_ids = set()
    clean_documents = []
    skip_report = []

    for doc in raw_documents:
        if doc["id"] in seen_ids:
            skip_report.append({"id": doc["id"], "title": doc["title"], "reason": f"Duplicate id {doc['id']} (already used by an earlier document)."})
            continue

        if not doc["text"] or not doc["text"].strip():
            skip_report.append({"id": doc["id"], "title": doc["title"], "reason": "text is empty or whitespace-only."})
            continue

        seen_ids.add(doc["id"])
        clean_documents.append(doc)

    return clean_documents, skip_report


def main():
    print("=== Knowledge Base ===\n")

    clean_documents, skip_report = load_knowledge_base()

    print(f"Raw documents: {len(RAW_DOCUMENTS)}")
    print(f"Clean documents loaded: {len(clean_documents)}")
    print(f"Documents skipped: {len(skip_report)}\n")

    print("--- Skip report ---")
    for entry in skip_report:
        print(f"  id={entry['id']:<4} title={entry['title']:<40} reason: {entry['reason']}")

    print("\n--- A sample of clean documents ---")
    for doc in clean_documents[:3]:
        print(f"  id={doc['id']}: {doc['title']} (category={doc['metadata']['category']})")

    print(
        "\nWhere real data would come from: a real support knowledge "
        "base is published and updated by a support or content team, "
        "pulled from a help center's CMS, a wiki, or resolved support "
        "tickets, usually refreshed on a schedule rather than written "
        "once. Hand-typing these 12 documents here keeps the whole "
        "system runnable and readable with zero external dependencies, "
        "the same honest tradeoff this project has made since Day 1."
    )


if __name__ == "__main__":
    main()
