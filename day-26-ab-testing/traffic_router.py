"""
traffic_router.py

Assigns each user to a variant, STICKILY: the same user id always lands
in the same group, every time, across every request they ever send. This
is done by hashing the user id into a number, rather than rolling a
fresh random choice per request, since a user who sometimes sees variant
A and sometimes variant B would make both their own experience
inconsistent and the experiment's results meaningless, you could never
tell which version actually produced any given outcome for them.
"""

import hashlib


def _stable_fraction(user_id):
    """
    Hashes a user id into a stable number between 0.0 and 1.0, using
    hashlib (not Python's built-in hash(), which is randomized per
    process run by default and would NOT be stable across runs or even
    across the same run with hash randomization). The same user id
    always produces the exact same fraction, forever.
    """
    digest = hashlib.sha256(user_id.encode("utf-8")).hexdigest()
    # Take the first 8 hex characters (32 bits) as an integer, and scale
    # it down to a fraction of the full 32-bit range.
    as_int = int(digest[:8], 16)
    return as_int / 0xFFFFFFFF


def assign_variant(user_id, split=0.5):
    """
    Returns "A" or "B" for a given user id, deterministically. split is
    the fraction of users assigned to B (0.5 for an even 50/50 split,
    0.1 for a 90/10 canary split where only 10 percent of traffic
    reaches the new variant).
    """
    return "B" if _stable_fraction(user_id) < split else "A"


def main():
    print("=== Traffic Router ===\n")

    print("--- Sticky assignment: the same user id always lands in the same group ---\n")
    test_user = "user-00042"
    assignments = [assign_variant(test_user, split=0.5) for _ in range(5)]
    print(f"user_id={test_user!r}, assigned 5 times: {assignments}")
    print(f"All identical: {len(set(assignments)) == 1}\n")

    print("--- 50/50 split over 1000 simulated users ---")
    user_ids = [f"user-{i:05d}" for i in range(1000)]
    counts_50_50 = {"A": 0, "B": 0}
    for user_id in user_ids:
        counts_50_50[assign_variant(user_id, split=0.5)] += 1
    print(f"A: {counts_50_50['A']}, B: {counts_50_50['B']}  "
          f"(B fraction: {counts_50_50['B'] / len(user_ids):.1%})\n")

    print("--- 90/10 canary split over the same 1000 users ---")
    counts_90_10 = {"A": 0, "B": 0}
    for user_id in user_ids:
        counts_90_10[assign_variant(user_id, split=0.1)] += 1
    print(f"A: {counts_90_10['A']}, B: {counts_90_10['B']}  "
          f"(B fraction: {counts_90_10['B'] / len(user_ids):.1%})\n")

    print(
        "Why sticky assignment matters: a user who sees variant A on "
        "Monday and variant B on Tuesday has an inconsistent experience, "
        "and worse for the experiment, any outcome they produce (helpful "
        "or not) cannot be cleanly attributed to either variant, since "
        "both versions contributed to how they feel about the service "
        "overall. Hashing the user id means the assignment is computed "
        "fresh every time from the same stable input, with no state to "
        "store or look up, and it reliably produces the exact same "
        "answer for that user on every single call."
    )


if __name__ == "__main__":
    main()
