# Day 27: Security, Privacy, and Compliance

## Three different questions

- **Security** asks: can a bad actor get in, break something, or make the
  service do something it should not? Keeping bad actors out.
- **Privacy** asks: whose personal data are we touching, and are we
  handling it carefully? Keeping real people's information safe.
- **Compliance** asks: what rules apply to us (laws, regulations, policies),
  and are we actually following them? Following the rules that apply to you.

These three overlap constantly but are not the same question. A service
can be perfectly secure (nobody can break in) while still being a privacy
problem (it logs everyone's full name and email forever). A service can
respect privacy well while still being out of compliance (it never wrote
down what data it collects or why).

## The main risks for a RAG service

- **Prompt injection**: text, in a user's query or hiding inside a
  retrieved document, trying to make the system do something other than
  answer the actual question
- **Data leaks through answers**: an answer that accidentally surfaces
  something private, sensitive, or belonging to someone else
- **Abuse and cost attacks**: a single actor sending enormous volume,
  scraping the whole index, or otherwise running up real cost
- **Storing personal data in logs**: emails, card numbers, or other
  personal details ending up in plain text in a log file nobody is
  watching for that

## Why secrets never belong in code or in logs

A secret written into source code ends up in version control history
forever, readable by anyone with repository access, even after the line
is deleted. A secret printed into a log line ends up wherever that log
is stored, often with far looser access controls than the system the
secret protects. Secrets belong in exactly one place: an environment
variable or a secrets manager, read once at startup, never written down
anywhere else.

## What we're building today

Input and document safety checks for prompt injection, PII redaction
that masks personal data before it is ever stored, a safe logging wrapper
that redacts by default, role-based access control for API keys stored
as hashes, correct secret handling, abuse and cost limits on top of Day
23's rate limiter, a data retention rule with real deletion, and a
security checklist that runs against the real Day 23 API.

## A plain warning

This is teaching code, written to illustrate the IDEAS behind security
and privacy work using only the Python standard library. It is not a
security audit, not production-grade cryptography, and not a substitute
for a professional security review. Any real system handling real user
data needs an actual security review, and likely legal review too,
before launch.

## The building analogy

A real office building does not rely on one single protection. It has a
front desk that checks who comes in, locked doors so not every room is
open to everyone who got past the front desk, shredders so old paperwork
does not just pile up forever, and a visitor log so there is a record of
who was where and when. None of these alone would keep the building
safe. Together, they cover different risks: who gets in, who can reach
what once they are in, what happens to old records, and whether anyone
can check what happened later. Today's work builds that same set of
layers for a RAG service.

## How this connects to Day 22 and Day 23

Day 22 built structured logging that already avoided logging full raw
query text. Today's `safe_logging_v2.py` wraps that same logger and adds
PII redaction on top, so even a short query preview never leaks an email
address or a card number. Day 23 built an API key check and a rate
limit. Today's `access_control.py` and `abuse_and_cost_limits.py` build
directly on that same key-based identity, adding roles and a daily
budget on top of the per-minute limit Day 23 already enforced.
