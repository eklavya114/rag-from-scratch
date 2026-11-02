"""
pii_redaction.py

Finds and masks personal data BEFORE it is ever stored or logged. PII
(personally identifiable information) is anything that could identify a
specific real person: an email address, a phone number, a payment card
number. Redaction has to happen before logging, not after, since a log
line already written to disk or shipped to a log aggregator cannot be
un-logged. Once it is out, it is out.
"""

import re

EMAIL_PATTERN = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")
PHONE_PATTERN = re.compile(r"(?<!\d)(\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}(?!\d)")

# Matches a run of 13 to 19 digits, allowing spaces or dashes as
# separators BETWEEN digits only (how card numbers are usually written),
# which is then verified with a Luhn check before being treated as a
# real card number. The separator is required before each digit except
# the first, so the match never swallows a trailing space or dash that
# belongs to the surrounding sentence.
CARD_LIKE_PATTERN = re.compile(r"(?<!\d)\d(?:[ -]?\d){12,18}(?!\d)")


def luhn_checksum(digits):
    """
    The Luhn algorithm: a simple checksum real card numbers are
    constructed to satisfy. Doubling every second digit from the right,
    subtracting 9 from any result over 9, and summing everything should
    land on a multiple of 10 for a genuinely valid card number. This is
    what separates an actual card number from an arbitrary 16-digit
    string that happens to look like one, reducing false positives.
    """
    total = 0
    reversed_digits = digits[::-1]
    for i, digit in enumerate(reversed_digits):
        value = int(digit)
        if i % 2 == 1:
            value *= 2
            if value > 9:
                value -= 9
        total += value
    return total % 10 == 0


def passes_luhn(card_like_text):
    digits = re.sub(r"[ -]", "", card_like_text)
    if not digits.isdigit():
        return False
    return luhn_checksum(digits)


def redact_text(text):
    """
    Replaces every email, phone number, and Luhn-valid card-like number
    with a clear label, keeping everything else in the text readable.
    Returns the redacted text plus a summary of what was found, so a
    caller can also know WHETHER anything was redacted, not just see the
    masked result.
    """
    findings = {"emails": 0, "phones": 0, "cards": 0}

    def replace_email(match):
        findings["emails"] += 1
        return "[EMAIL]"

    def replace_phone(match):
        findings["phones"] += 1
        return "[PHONE]"

    def replace_card(match):
        if passes_luhn(match.group(0)):
            findings["cards"] += 1
            return "[CARD]"
        return match.group(0)  # not a real card number, leave it alone

    redacted = EMAIL_PATTERN.sub(replace_email, text)
    redacted = PHONE_PATTERN.sub(replace_phone, redacted)
    redacted = CARD_LIKE_PATTERN.sub(replace_card, redacted)

    return redacted, findings


def main():
    print("=== PII Redaction ===\n")

    print("--- A message with real personal data ---")
    message = (
        "Hi, my email is jane.doe@example.com and my phone is 555-123-4567. "
        "I tried to pay with card 4111111111111111 but it was declined."
    )
    redacted, findings = redact_text(message)
    print(f"Before: {message}")
    print(f"After:  {redacted}")
    print(f"Findings: {findings}\n")

    print("--- A random 16-digit number that fails the Luhn check ---")
    fake_number_message = "My reference number is 1234567890123456, please look it up."
    redacted, findings = redact_text(fake_number_message)
    print(f"Before: {fake_number_message}")
    print(f"After:  {redacted}")
    print(f"Findings: {findings}")
    print(f"Correctly NOT masked as a card: {'[CARD]' not in redacted}\n")

    print(
        "What counts as personal data, and why redaction happens before "
        "logging: an email, a phone number, or a payment card number can "
        "each be used on their own to identify or contact a specific "
        "real person, which is exactly what makes them sensitive to "
        "store. Redacting them as text is transformed, right before it "
        "touches a log line, a database row, or a metrics label, means "
        "the UNREDACTED version never exists anywhere outside the "
        "original request itself. Redacting AFTER storage is already too "
        "late: the sensitive data has already been written down somewhere "
        "it should never have been."
    )


if __name__ == "__main__":
    main()
