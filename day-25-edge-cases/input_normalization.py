"""
input_normalization.py

Cleans up a query BEFORE it reaches retrieval, so retrieval does not
have to deal with surface-level variation that carries no real meaning:
extra whitespace, stray control characters, visually identical text
represented with different Unicode code points, and words stretched out
far past normal use. Each step is applied in a fixed order, since some
of these interact (collapsing whitespace before capping repeated
characters avoids counting whitespace runs as "repeated characters").
"""

import io
import re
import sys
import unicodedata

if hasattr(sys.stdout, "buffer"):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

MAX_REPEATED_CHARACTERS = 3


def collapse_whitespace(text):
    """Collapses any run of whitespace (spaces, tabs, newlines) down to a single space, and strips leading/trailing whitespace."""
    return re.sub(r"\s+", " ", text).strip()


def strip_control_characters(text):
    """
    Removes Unicode control characters (category starting with 'C',
    except common whitespace like newline and tab, which
    collapse_whitespace already handles). Control characters have no
    visible representation and can carry no real meaning in a search
    query, so they are safe to drop outright rather than merely escape.
    """
    return "".join(ch for ch in text if not unicodedata.category(ch).startswith("C") or ch in "\n\t ")


def unicode_normalize(text):
    """
    Applies NFKC (Normalization Form KC) Unicode normalization, which
    maps visually identical or equivalent characters to a single
    canonical representation. For example, a full-width letter and its
    ordinary ASCII equivalent, or an accented character built from a
    base letter plus a combining accent versus the same character as one
    single code point, both normalize to the same canonical form. Without
    this, two queries a human would read as identical text can fail to
    match each other, or match differently against stored embeddings,
    purely because of how the underlying bytes happened to be encoded.
    """
    return unicodedata.normalize("NFKC", text)


def cap_repeated_characters(text, max_repeats=MAX_REPEATED_CHARACTERS):
    """
    Caps any character repeated more than max_repeats times in a row
    down to exactly max_repeats, so "sooooooo good" becomes "sooo good"
    rather than being left stretched arbitrarily long. This preserves
    the EMPHASIS (the word is still clearly stretched, not flattened
    back to "so") while giving the rest of the pipeline a bounded,
    predictable amount of repetition to deal with instead of an
    unbounded one.
    """
    pattern = re.compile(r"(.)\1{" + str(max_repeats) + r",}")
    return pattern.sub(lambda m: m.group(1) * max_repeats, text)


def normalize_query(text):
    """Runs every normalization step in order and returns the final cleaned query."""
    text = collapse_whitespace(text)
    text = strip_control_characters(text)
    text = unicode_normalize(text)
    text = cap_repeated_characters(text)
    return text


def main():
    print("=== Input Normalization ===\n")

    examples = [
        ("Extra whitespace", "What    is   RAG?\n\n\n   Please explain.  "),
        ("Control characters", "What is RAG?\x00\x01\x02 Tell me more."),
        ("Unicode variants (full-width letters)", "Ｗｈａｔ　ｉｓ　ＲＡＧ？"),
        ("Repeated characters", "soooooooooooooooooooo good, tell me about RAG"),
        ("Combined: all four at once", "Ｗｈａｔ    is\x00 RAG??!!!!!!!!!"),
    ]

    for name, raw in examples:
        normalized = normalize_query(raw)
        print(f"--- {name} ---")
        print(f"Before: {raw!r}")
        print(f"After:  {normalized!r}\n")

    print(
        "Normalization changing meaning, and when that is acceptable: "
        "collapsing 'soooooo good' down to 'sooo good' changes the exact "
        "text, but not the MEANING a human reader takes from it, the word "
        "is still clearly emphasized. That is the bar for when "
        "normalization is safe: it should only remove variation that "
        "carries no real signal (extra whitespace, stray control bytes, "
        "two different byte sequences a human reads as the identical "
        "character) or cap variation that carries diminishing signal past "
        "a point (ten repeated letters communicates the same emphasis as "
        "three). Normalization should never flatten away a difference a "
        "human reader would actually notice and care about, which is why "
        "cap_repeated_characters reduces repetition rather than removing "
        "it outright."
    )


if __name__ == "__main__":
    main()
