"""
secrets_handling.py

Shows how secrets should be loaded (from environment variables only,
never hardcoded or read from a config file checked into version
control), and how they should never be printed or logged in full. Also
includes a simple scanner that reports text LOOKING like a key sitting
somewhere it should not, a teaching demo using obviously fake keys, not
a real secret-scanning tool.
"""

import os
import re

REQUIRED_SECRET_NAME = "RAG_API_KEY"

# Patterns resembling common API key shapes, used only to FLAG text
# worth a human's attention, not to definitively prove a real secret is
# present. A real secret scanner (gitleaks, trufflehog, and similar
# tools) uses a much larger, maintained set of patterns and additional
# entropy checks; this is a minimal teaching version of the same idea.
KEY_LIKE_PATTERNS = [
    re.compile(r"sk-[a-zA-Z0-9]{20,}"),       # a common "secret key" prefix shape
    re.compile(r"AKIA[A-Z0-9]{16}"),          # shape of an AWS access key id
    re.compile(r"[a-f0-9]{32,64}"),           # a long hex string, like a hashed or raw token
]


def load_required_secret(name=REQUIRED_SECRET_NAME):
    """
    Reads a secret from an environment variable ONLY. Raises a clear
    error if it is missing, rather than silently falling back to a
    default secret value, a missing secret should be loud and obvious at
    startup, not a quiet bug discovered later when something behaves
    unexpectedly.
    """
    value = os.environ.get(name)
    if not value:
        raise RuntimeError(f"Required secret '{name}' is not set. Set it as an environment variable before starting the service.")
    return value


def mask_secret(value):
    """Returns a masked version of a secret: the first 4 characters, then asterisks, never the full value. Safe to print in logs, error messages, or debug output."""
    if len(value) <= 4:
        return "*" * len(value)
    return value[:4] + "*" * (len(value) - 4)


def scan_text_for_key_like_values(text):
    """
    Scans a block of text for anything matching a key-like pattern,
    returning each match found. A teaching demo: real secret scanning
    tools are far more sophisticated (entropy analysis, a much larger
    pattern library, awareness of specific providers' exact key formats)
    and should be run in addition to, not instead of, this simple check.
    """
    findings = []
    for pattern in KEY_LIKE_PATTERNS:
        for match in pattern.finditer(text):
            findings.append(match.group(0))
    return findings


def main():
    print("=== Secrets Handling ===\n")

    print("--- Loading a required secret from the environment ---")
    os.environ["RAG_API_KEY"] = "sk-fake1234567890abcdefghij"  # set here ONLY to demonstrate load_required_secret(); a real deployment sets this outside the process entirely
    secret = load_required_secret()
    print(f"Loaded secret, masked for safe printing: {mask_secret(secret)}\n")

    print("--- A missing secret raises a clear, loud error ---")
    try:
        load_required_secret("RAG_SOME_OTHER_SECRET_THAT_IS_NOT_SET")
    except RuntimeError as e:
        print(f"Correctly raised: {e}\n")

    print("--- Scanning a file-like block of text for key-like values ---")
    demo_file_contents = (
        "# config.py (example contents, all values below are FAKE demo keys)\n"
        "DATABASE_URL = 'postgres://user:pass@localhost/db'\n"
        "API_KEY = 'sk-fake9876543210zyxwvutsrqp'\n"
        "AWS_ACCESS_KEY_ID = 'AKIAFAKEEXAMPLE1234'\n"
        "DEBUG = True\n"
    )
    findings = scan_text_for_key_like_values(demo_file_contents)
    print(f"Key-like values found: {len(findings)}")
    for finding in findings:
        print(f"  {mask_secret(finding)}")

    print(
        "\nWhy rotation matters, and where secrets belong: a secret "
        "loaded once from an environment variable at startup can be "
        "ROTATED (replaced with a new value) by changing that environment "
        "variable and restarting the service, without touching any code "
        "at all. A secret hardcoded into source, by contrast, requires a "
        "code change, a review, and a deploy just to rotate, and the old "
        "value stays visible in version control history forever even "
        "after being replaced. Secrets belong in environment variables "
        "or a dedicated secrets manager, read at startup, never written "
        "into a file that gets committed."
    )


if __name__ == "__main__":
    main()
