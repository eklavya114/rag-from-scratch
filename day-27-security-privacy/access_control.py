"""
access_control.py

Gives each API key a ROLE with a limited set of permissions, the
principle of LEAST PRIVILEGE: a key can do exactly what its role allows,
nothing more, even if the service itself is technically capable of more.
A reader key that leaks should only ever let someone send queries, never
read internal metrics, since those two capabilities should never have
been bundled behind the same permission in the first place.

Keys are stored as SALTED HASHES, never as plain text, in the key table.
If this table were ever read by someone who should not have access (a
backup, a misconfigured database, a careless log line), a hash reveals
nothing usable, an attacker cannot reconstruct the original key from it,
the same reason real systems never store plain-text passwords either.
"""

import hashlib
import secrets

ROLE_PERMISSIONS = {
    "reader": {"query"},
    "admin": {"query", "read_metrics"},
    "none": set(),
}

# A fixed demo salt, for repeatable output across runs. A real system
# uses a UNIQUE, randomly generated salt PER KEY, stored alongside each
# hash, never one shared constant like this across every key, a shared
# salt makes it far cheaper for an attacker to precompute a lookup table
# against every key in the table at once.
DEMO_SALT = "day27-demo-salt-not-for-production"


def hash_key(raw_key, salt=DEMO_SALT):
    """Hashes a raw API key with a salt using SHA-256. The salt makes a precomputed hash lookup table far less useful, since the same raw key hashes differently under a different salt."""
    return hashlib.sha256((salt + raw_key).encode("utf-8")).hexdigest()


def build_key_table(entries):
    """Builds a lookup table keyed by HASHED key, never the raw key, from a list of (raw_key, role) pairs. The raw keys only ever exist transiently, while building this table and in the caller's own hands, never stored."""
    return {hash_key(raw_key): role for raw_key, role in entries}


def check_permission(key_table, raw_key, requested_permission):
    """
    Looks up a raw key by hashing it and checking the table, then
    checks whether that key's role actually grants the requested
    permission. Returns (allowed, reason), so a denial always comes with
    a specific, loggable explanation.
    """
    key_hash = hash_key(raw_key)
    role = key_table.get(key_hash)

    if role is None:
        return False, "Key not recognized."

    permissions = ROLE_PERMISSIONS.get(role, set())
    if requested_permission not in permissions:
        return False, f"Role '{role}' does not include permission '{requested_permission}'."

    return True, f"Role '{role}' grants permission '{requested_permission}'."


def main():
    print("=== Access Control ===\n")

    reader_key = secrets.token_hex(16)
    admin_key = secrets.token_hex(16)
    wrong_key = secrets.token_hex(16)  # never added to the table at all

    key_table = build_key_table([
        (reader_key, "reader"),
        (admin_key, "admin"),
    ])

    print(f"Key table has {len(key_table)} entries, storing only hashes:")
    for key_hash in key_table:
        print(f"  {key_hash[:16]}...  (role stored alongside, raw key never stored)")
    print()

    print("--- A reader key trying to read metrics (should be denied) ---")
    allowed, reason = check_permission(key_table, reader_key, "read_metrics")
    print(f"Allowed: {allowed}, reason: {reason}\n")

    print("--- An admin key reading metrics (should be allowed) ---")
    allowed, reason = check_permission(key_table, admin_key, "read_metrics")
    print(f"Allowed: {allowed}, reason: {reason}\n")

    print("--- A key that was never issued (should be denied) ---")
    allowed, reason = check_permission(key_table, wrong_key, "query")
    print(f"Allowed: {allowed}, reason: {reason}\n")

    print("--- A reader key making a normal query (should be allowed) ---")
    allowed, reason = check_permission(key_table, reader_key, "query")
    print(f"Allowed: {allowed}, reason: {reason}\n")

    print(
        "Why keys are stored hashed, and why least privilege matters: "
        "if this key table ever leaked, say, through a misconfigured "
        "backup, a hash on its own cannot be turned back into the "
        "original key, so the leak would not actually hand out working "
        "credentials. Giving the reader role only 'query' permission, "
        "never 'read_metrics', means a leaked reader key exposes far "
        "less than a leaked admin key would, scoping each key down to "
        "the minimum it actually needs is what limits the real damage "
        "any single leaked credential can do."
    )


if __name__ == "__main__":
    main()
