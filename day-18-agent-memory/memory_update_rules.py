"""
memory_update_rules.py

Not everything said in a conversation deserves to become a long-term
memory. This file shows the rules that decide when memory should
change: saving only stable facts, overwriting instead of duplicating
when a user corrects something, forgetting on request, and refusing to
save obviously sensitive data in the first place.
"""

import re

SENSITIVE_PATTERNS = [
    re.compile(r"\b(?:\d[ -]*?){13,19}\b"),  # a run of 13 to 19 digits, the shape of a card number
    re.compile(r"\b\d{3}-\d{2}-\d{4}\b"),     # a US social security number shape
]


def is_stable_fact(key, value):
    """
    SAVE ONLY STABLE FACTS: a preferred contact method or an account ID
    is worth remembering because it stays true across many future
    conversations. One-off chatter like "I'm in a hurry today" or
    "that's annoying" describes a moment, not a lasting property of the
    user, and shouldn't be written to long-term memory at all.
    """
    one_off_keys = {"current_mood", "todays_complaint", "last_message_tone"}
    return key not in one_off_keys


def contains_sensitive_data(value):
    """AVOID SAVING SENSITIVE DATA: checks the value against simple patterns for things that should never land in long-term memory, regardless of how the conversation came up."""
    text = str(value)
    return any(pattern.search(text) for pattern in SENSITIVE_PATTERNS)


def update_fact(facts, key, value, consented=True):
    """
    Applies the update rules before writing anything: refuses
    one-off chatter, refuses sensitive data, and otherwise overwrites
    any existing value for the key, since a correction should replace
    the old fact, not sit alongside it as a second, conflicting entry.
    """
    if not consented:
        return {"ok": False, "reason": "User has not consented to storing this fact."}

    if not is_stable_fact(key, value):
        return {"ok": False, "reason": f"'{key}' looks like one-off chatter, not a stable fact. Not saved."}

    if contains_sensitive_data(value):
        return {"ok": False, "reason": "Value appears to contain sensitive data (card number or SSN pattern). Not saved."}

    previous_value = facts.get(key)
    facts[key] = value

    if previous_value is not None and previous_value != value:
        return {"ok": True, "action": "corrected", "previous_value": previous_value, "new_value": value}
    return {"ok": True, "action": "saved", "new_value": value}


def forget_fact(facts, key, requested_by_user=True):
    """FORGET ON REQUEST: removing a fact should always be honored when the user asks, no stability or sensitivity check needed, since removing information is never the risky direction."""
    if not requested_by_user:
        return {"ok": False, "reason": "Forget requests should come from the user, not be inferred silently."}
    existed = key in facts
    facts.pop(key, None)
    return {"ok": True, "existed": existed}


def main():
    print("=== Memory Update Rules ===\n")

    facts = {}

    print("--- Saving a stable fact ---")
    result = update_fact(facts, "preferred_contact_method", "email")
    print(result)

    print("\n--- Rejecting one-off chatter ---")
    result = update_fact(facts, "current_mood", "frustrated")
    print(result)

    print("\n--- Overwriting when the user corrects a fact ---")
    result = update_fact(facts, "preferred_contact_method", "phone")
    print(result)
    print(f"Current value: {facts['preferred_contact_method']}")

    print("\n--- Refusing to save sensitive data ---")
    result = update_fact(facts, "payment_note", "card number 4111 1111 1111 1111")
    print(result)

    print("\n--- Forgetting a fact on request ---")
    result = forget_fact(facts, "preferred_contact_method", requested_by_user=True)
    print(result)
    print(f"Fact still present: {'preferred_contact_method' in facts}")

    print("\n--- Declining to save without consent ---")
    result = update_fact(facts, "account_id", "CUST-42", consented=False)
    print(result)

    print(f"\nFinal stored facts: {facts}")

    print(
        "\nPrivacy and consent: memory should only ever hold what a user "
        "would recognize and accept as something worth remembering about "
        "them. A fact saved without consent, a one-off emotional comment "
        "treated as a permanent trait, or a stray card number captured in "
        "passing are all the same underlying mistake: writing something to "
        "long-term storage that nobody actually decided should live there."
    )


if __name__ == "__main__":
    main()
