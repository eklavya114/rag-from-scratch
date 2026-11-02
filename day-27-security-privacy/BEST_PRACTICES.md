# Day 27 Best Practices: Security and Privacy

## Keep secrets out of code and logs

`secrets_handling.py` reads secrets only from environment variables,
raising a loud error if one is missing rather than falling back to a
default. `safe_logging_v2.py` redacts sensitive header VALUES by default
through an allowlist, not a denylist, so an unrecognized header (a
cookie, a session token, anything not yet thought of) is redacted
automatically instead of leaking by omission. A secret written into
code or a log line ends up stored wherever that code or log lives,
often with far looser access controls than the system it protects.

## Treat all input and retrieved text as untrusted

`prompt_injection_guard.py` scans the user's query AND every retrieved
document chunk against the same pattern list. A poisoned document
sitting in the index is just as real a risk as a hostile query, since a
RAG system hands retrieved text straight to the generator, any
instruction-like text anywhere in that pipeline deserves the same
scrutiny.

## Redact before logging

`pii_redaction.py` masks emails, phone numbers, and Luhn-verified card
numbers, and `safe_logging_v2.py` runs every query preview through it
before building a log line. Redaction has to happen before data is
stored or logged, never after, a log line already written to disk
cannot be un-logged once it is out.

## Least privilege for keys

`access_control.py` gives each API key a role (reader, admin, none)
with a strictly limited set of permissions, and stores keys as salted
hashes, never in plain text. A leaked reader key should only ever expose
what reading a query actually requires, never the broader access an
admin key would carry.

## Budget every key

`abuse_and_cost_limits.py` adds a daily budget and a scrape detector on
top of Day 23's per-minute rate limit, not in place of it. A per-minute
limit alone cannot catch a key sending low, steady traffic all day that
still adds up to real cost, or a tight burst of near-identical queries
trying to extract the whole index.

## Delete data on schedule

`data_retention.py` deletes log entries older than a retention period
automatically, and supports deleting every record for one specific user
on demand. Holding data forever "just in case" is itself a risk: every
record kept is one more thing that could leak, and one more thing a
real deletion request has to actually reach.

## Get a professional review before real launch

`compliance_notes.py` and this folder's README both say it directly:
this is teaching code, not a security audit, and nothing here is legal
advice. `secure_api_check.py` shows what a repeatable checklist looks
like, but a checklist like this one supplements a real security review,
it never replaces one, before any system handling real user data goes live.
