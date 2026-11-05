"""
domain_dataset.py

A small domain, a support knowledge base about orders, refunds, and
shipping, built just for Day 28. The Day 1-6 toy documents are about
Python and RAG concepts, a completely different vocabulary, so this
domain needed its own small document set and its own domain-specific
terms (RMA, backorder, chargeback) to actually demonstrate adaptation.

The train/test split happens HERE, in this one file, before any other
script in this folder touches the data, specifically so every later
step (feedback, vocabulary, tuning) can only ever see the train split
unless it explicitly asks for the test split by name. Splitting early,
in one place, is what makes it hard to accidentally leak test data into
tuning later.
"""

import random

SEED = 2026

DOCUMENTS = [
    {"id": 1, "title": "How to Request an RMA", "text": "To return an item, request a Return Merchandise Authorization (RMA) from your account page. An RMA number must be included with any returned package, or the warehouse cannot process it."},
    {"id": 2, "title": "Refund Processing Times", "text": "Refunds are issued to the original payment method within 5 to 7 business days after the returned item is received and inspected at the warehouse."},
    {"id": 3, "title": "What Is a Chargeback", "text": "A chargeback happens when a customer disputes a charge directly with their bank or card issuer instead of contacting support first. Chargebacks can take 30 to 90 days to resolve and may involve a fee."},
    {"id": 4, "title": "Backorder Status Explained", "text": "A backorder means an item is temporarily out of stock but will ship once restocked. Backordered items show an estimated ship date on the order page, updated weekly."},
    {"id": 5, "title": "Shipping Carrier Options", "text": "Orders ship via standard ground, expedited, or overnight carriers. Expedited and overnight shipping cost more but arrive faster, standard ground is the default free option."},
    {"id": 6, "title": "Tracking a Lost Package", "text": "If a tracking number shows delivered but the package never arrived, file a lost package claim with support within 14 days, the carrier investigates before a replacement ships."},
    {"id": 7, "title": "Order Cancellation Window", "text": "Orders can be cancelled for free within one hour of placing them. After that window, the order may have already entered fulfillment and cannot be cancelled."},
    {"id": 8, "title": "Return Window for Items", "text": "Most items can be returned within 30 days of delivery for a full refund. Final sale items and opened electronics are not eligible for return."},
    {"id": 9, "title": "Partial Shipment Explained", "text": "A partial shipment happens when an order with multiple items ships in separate packages because one item was backordered. Each shipment gets its own tracking number."},
    {"id": 10, "title": "Store Credit Versus Refund", "text": "Customers can choose store credit instead of a refund to the original payment method. Store credit is issued instantly, while a refund takes 5 to 7 business days."},
]

# 25 labeled queries. Each lists the document ids that genuinely answer
# it, built by actually reading the documents above, the same manual
# labeling discipline Day 8's test_dataset_creation.py used.
LABELED_QUERIES = [
    {"query": "How do I get an RMA number?", "relevant_ids": {1}},
    {"query": "What is an RMA?", "relevant_ids": {1}},
    {"query": "How long does a refund take?", "relevant_ids": {2}},
    {"query": "When will I get my money back?", "relevant_ids": {2}},
    {"query": "What is a chargeback?", "relevant_ids": {3}},
    {"query": "My bank disputed a charge, what happens now?", "relevant_ids": {3}},
    {"query": "What does backorder mean?", "relevant_ids": {4}},
    {"query": "Why is my item on backorder?", "relevant_ids": {4}},
    {"query": "What shipping carriers do you use?", "relevant_ids": {5}},
    {"query": "Can I get overnight shipping?", "relevant_ids": {5}},
    {"query": "My tracking says delivered but I never got the package", "relevant_ids": {6}},
    {"query": "How do I file a lost package claim?", "relevant_ids": {6}},
    {"query": "Can I cancel my order?", "relevant_ids": {7}},
    {"query": "How long do I have to cancel an order?", "relevant_ids": {7}},
    {"query": "What is the return window?", "relevant_ids": {8}},
    {"query": "Can I return this item after 30 days?", "relevant_ids": {8}},
    {"query": "Why did my order ship in two boxes?", "relevant_ids": {9}},
    {"query": "What is a partial shipment?", "relevant_ids": {9}},
    {"query": "Can I get store credit instead of a refund?", "relevant_ids": {10}},
    {"query": "Is store credit faster than a refund?", "relevant_ids": {10}},
    {"query": "How do returns work?", "relevant_ids": {1, 8}},
    {"query": "What happens after my item is backordered and then restocked?", "relevant_ids": {4, 9}},
    {"query": "I want a refund, how does that work?", "relevant_ids": {2, 10}},
    {"query": "What if my package is lost after showing delivered?", "relevant_ids": {6}},
    {"query": "How does a dispute with my card issuer affect my order?", "relevant_ids": {3}},
]


def split_queries(queries=LABELED_QUERIES, train_fraction=0.6, seed=SEED):
    """
    Splits queries into a train set and a held-out test set, with a
    FIXED seed so the split is identical every run. This split happens
    BEFORE any tuning, and the test set must stay completely untouched
    by every later step: feedback_collector.py, domain_vocabulary.py,
    and ranker_weight_tuning.py all only ever read from the train split.
    Tuning on data and then testing on that SAME data always looks
    better than it really is, since nothing was ever held back to catch
    a mistake, splitting first is the only way held_out_evaluation.py's
    final numbers can actually be trusted.
    """
    shuffled = list(queries)
    rng = random.Random(seed)
    rng.shuffle(shuffled)

    split_index = round(len(shuffled) * train_fraction)
    train = shuffled[:split_index]
    test = shuffled[split_index:]
    return train, test


def main():
    print("=== Domain Dataset ===\n")

    print(f"Documents: {len(DOCUMENTS)}")
    for doc in DOCUMENTS[:3]:
        print(f"  id={doc['id']}: {doc['title']}")
    print("  ...\n")

    print(f"Labeled queries: {len(LABELED_QUERIES)}\n")

    train, test = split_queries()
    print(f"Train split: {len(train)} queries ({len(train) / len(LABELED_QUERIES):.0%})")
    print(f"Test split:  {len(test)} queries ({len(test) / len(LABELED_QUERIES):.0%})\n")

    print("--- Sample of 3 train queries ---")
    for item in train[:3]:
        print(f"  {item['query']!r} -> relevant_ids={item['relevant_ids']}")

    print("\n--- Sample of 3 test queries ---")
    for item in test[:3]:
        print(f"  {item['query']!r} -> relevant_ids={item['relevant_ids']}")

    train_again, test_again = split_queries()
    print(f"\nSplit is repeatable across runs: {train == train_again and test == test_again}")

    print(
        "\nWhy the split must happen before any tuning: every later "
        "script in this folder (feedback_collector.py, "
        "domain_vocabulary.py, ranker_weight_tuning.py) reads ONLY the "
        "train split returned here. If the split happened after looking "
        "at results, or if test queries leaked into the data used for "
        "tuning, held_out_evaluation.py's final numbers would no longer "
        "mean anything, they would just be reporting how well the "
        "adaptation memorized the exact data it was shown, not how well "
        "it generalizes to a genuinely new question."
    )


if __name__ == "__main__":
    main()
