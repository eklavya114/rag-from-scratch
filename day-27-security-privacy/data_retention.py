"""
data_retention.py

Keeps stored data only as long as it is actually needed, the principle
of DATA MINIMIZATION: holding onto data forever "just in case" is itself
a risk, every record kept is one more thing that could leak, one more
thing a deletion request has to actually reach. This file stores log
entries with a timestamp, deletes anything older than a retention
period, and supports a "delete everything for this user" request, the
kind of RIGHT TO DELETION real privacy regulations (GDPR-style rules)
require a service to actually be able to honor.
"""

import json
import os
import tempfile
import time

RETENTION_PERIOD_SECONDS = 2  # deliberately short, for a fast demo; a real system might use 30 or 90 days


def write_log_entry(log_path, user_id, query_preview, timestamp=None):
    """Appends one entry as a JSON line, with an explicit timestamp, the field every later retention or deletion decision is based on."""
    entry = {"user_id": user_id, "query_preview": query_preview, "timestamp": timestamp if timestamp is not None else time.time()}
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")


def read_all_entries(log_path):
    if not os.path.exists(log_path):
        return []
    with open(log_path, "r", encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def apply_retention(log_path, retention_period_seconds=RETENTION_PERIOD_SECONDS, now=None):
    """
    Rewrites the log file keeping only entries NEWER than the retention
    period, deleting everything older outright. A real system typically
    runs this on a schedule (daily, say), rather than on every write;
    this demo calls it explicitly so the before/after counts are easy
    to see in one run.
    """
    now = now if now is not None else time.time()
    entries = read_all_entries(log_path)
    kept = [e for e in entries if now - e["timestamp"] <= retention_period_seconds]

    with open(log_path, "w", encoding="utf-8") as f:
        for entry in kept:
            f.write(json.dumps(entry) + "\n")

    return len(entries), len(kept)


def delete_all_for_user(log_path, user_id):
    """Honors a 'delete everything for this user' request: removes every entry belonging to that user id, regardless of age, a real right-to-deletion request cannot wait for the normal retention schedule."""
    entries = read_all_entries(log_path)
    remaining = [e for e in entries if e["user_id"] != user_id]
    deleted_count = len(entries) - len(remaining)

    with open(log_path, "w", encoding="utf-8") as f:
        for entry in remaining:
            f.write(json.dumps(entry) + "\n")

    return deleted_count, len(remaining)


def main():
    print("=== Data Retention ===\n")

    log_path = os.path.join(tempfile.gettempdir(), "day27_retention_log.jsonl")
    if os.path.exists(log_path):
        os.remove(log_path)  # start clean, in case a prior crashed run left this behind

    print(f"Writing log entries to a temporary file: {log_path}\n")

    now = time.time()
    write_log_entry(log_path, "user-001", "What is RAG?", timestamp=now)
    write_log_entry(log_path, "user-002", "What is a vector database?", timestamp=now)
    write_log_entry(log_path, "user-001", "What is Python?", timestamp=now)

    entries_before = read_all_entries(log_path)
    print(f"Entries written: {len(entries_before)}\n")

    print(f"--- Waiting {RETENTION_PERIOD_SECONDS + 1} seconds so these entries age past the retention period ---")
    time.sleep(RETENTION_PERIOD_SECONDS + 1)

    print("--- Writing one fresh entry, which should SURVIVE retention ---")
    write_log_entry(log_path, "user-003", "Why does RAG matter?")

    total_before, kept_after = apply_retention(log_path)
    print(f"Entries before retention: {total_before}")
    print(f"Entries kept after retention: {kept_after}")
    print(f"Entries deleted for age: {total_before - kept_after}\n")

    print("--- A fresh query arrives from user-002, then user-002 requests full deletion ---")
    write_log_entry(log_path, "user-002", "A fresh query from user-002")
    entries_with_user_002 = read_all_entries(log_path)
    print(f"Entries before the deletion request: {len(entries_with_user_002)}")
    deleted_count, remaining_count = delete_all_for_user(log_path, "user-002")
    print(f"Deleted for user-002: {deleted_count}, remaining entries overall: {remaining_count}")

    os.remove(log_path)
    print(f"\nTemporary log file removed: {log_path}")

    print(
        "\nWhy data minimization and the right to deletion matter: every "
        "entry kept past the point it is actually needed is pure "
        "downside, it cannot help debug a problem that happened months "
        "ago in a system that has since changed, but it CAN leak, get "
        "subpoenaed, or simply be forgotten about and mishandled. A "
        "retention rule enforced on a real schedule, not just hoped for, "
        "is what keeps 'we only keep what we need' true in practice "
        "rather than only on paper, and being able to delete everything "
        "for one specific user on request, immediately, regardless of "
        "the normal schedule, is exactly what a real deletion right "
        "requires a service to be able to do."
    )


if __name__ == "__main__":
    main()
