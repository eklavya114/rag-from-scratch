"""
basic_rewriting.py

The simplest useful layer of query rewriting: cleaning, stopword
removal, abbreviation expansion, and typo fixing. Reuses Day 5's
clean_query()/remove_stopwords() rather than reimplementing them, and
adds the two pieces Day 5 didn't cover: known abbreviations and common
typos.
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "day-05-retrieval"))
from query_preprocessing import clean_query, remove_stopwords  # Day 5


# A small dictionary of abbreviations/acronyms common in this project's
# domain, expanded to their full form. Expanding (rather than just
# recognizing) an abbreviation means a query using the short form can
# still match documents that spelled it out, and vice versa.
ABBREVIATIONS = {
    "rag": "retrieval augmented generation",
    "llm": "large language model",
    "ann": "approximate nearest neighbor",
    "ndcg": "normalized discounted cumulative gain",
    "mrr": "mean reciprocal rank",
    "map": "mean average precision",
    "api": "application programming interface",
    "db": "database",
}

# A small table of common misspellings -> corrections, specific to
# vocabulary this project actually uses. A real system would use a
# general-purpose spell checker (edit-distance against a large
# dictionary, or a model-based corrector); a fixed table is a simple,
# fully-transparent stand-in that shows the same idea.
COMMON_TYPOS = {
    "vektor": "vector",
    "embeding": "embedding",
    "embeddnig": "embedding",
    "retreival": "retrieval",
    "similarty": "similarity",
    "databse": "database",
    "langauge": "language",
    "generaton": "generation",
}


def expand_abbreviations(query):
    """
    Replaces any standalone word matching a known abbreviation with its
    expanded form. Only whole-word matches count (so "map" the word
    doesn't get mangled inside "mapping") -- this is the same
    whole-word-matching lesson learned the hard way on Day 2's
    substring-matching bug.
    """
    words = query.split()
    expanded = []
    for word in words:
        core = word.strip("?.,!").lower()
        if core in ABBREVIATIONS:
            expanded.append(ABBREVIATIONS[core])
        else:
            expanded.append(word)
    return " ".join(expanded)


def fix_typos(query):
    """
    Replaces any standalone word matching a known typo with its
    correction. Same whole-word approach as expand_abbreviations() --
    deliberately simple and fully predictable, at the cost of only
    catching typos we already know about.
    """
    words = query.split()
    fixed = []
    for word in words:
        core = word.strip("?.,!").lower()
        if core in COMMON_TYPOS:
            fixed.append(COMMON_TYPOS[core])
        else:
            fixed.append(word)
    return " ".join(fixed)


def basic_rewrite(query):
    """
    Runs the full basic rewriting pipeline in a sensible order: fix
    typos and expand abbreviations FIRST (while the query still has its
    original casing/punctuation context), then clean and strip
    stopwords last, since those steps are meant to run right before the
    query goes to embedding/search.
    """
    step1 = fix_typos(query)
    step2 = expand_abbreviations(step1)
    step3 = clean_query(step2)
    step4 = remove_stopwords(step3)
    return {
        "original": query,
        "after_typo_fix": step1,
        "after_abbreviation_expansion": step2,
        "after_cleaning": step3,
        "after_stopword_removal": step4,
    }


def main():
    print("=== Basic Query Rewriting ===\n")

    example_queries = [
        "What is RAG?",
        "why is my vektor databse so slow for similarty search",
        "What's the difference between an LLM and a regular program?",
        "How do I use embeding for retreival?",
    ]

    for query in example_queries:
        result = basic_rewrite(query)
        print(f"Original:                \"{result['original']}\"")
        if result["after_typo_fix"] != result["original"]:
            print(f"After typo fix:          \"{result['after_typo_fix']}\"")
        if result["after_abbreviation_expansion"] != result["after_typo_fix"]:
            print(f"After abbreviation exp.: \"{result['after_abbreviation_expansion']}\"")
        print(f"After cleaning:          \"{result['after_cleaning']}\"")
        print(f"Final (stopwords removed): \"{result['after_stopword_removal']}\"")
        print()

    print(
        "Note the final stopword-stripped versions read as word fragments, "
        "not grammatical sentences ('why my vector database so slow "
        "similarity search') -- that's expected, not a bug. The goal of "
        "this stage is a bag of search-relevant keywords for matching, "
        "not readable prose; readability was never the point past this "
        "step.\n\n"
        "Each step fixes a different, narrow problem: typo fixing recovers "
        "words that would otherwise match nothing at all; abbreviation "
        "expansion bridges short-form and spelled-out versions of the same "
        "term; cleaning and stopword removal (from Day 5) strip noise that "
        "doesn't carry real search signal. None of these require "
        "understanding the query's MEANING -- that's where the later files "
        "in this folder go further."
    )


if __name__ == "__main__":
    main()
