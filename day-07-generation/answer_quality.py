"""
answer_quality.py

Turns "this answer seems fine" into actual measurable checks: does it
address the question, is it a reasonable length, does it stick to what
the sources actually say, and is it written clearly?
"""

import re


STOPWORDS = {
    "what", "is", "a", "an", "the", "are", "of", "in", "to", "and", "for",
    "how", "do", "does", "i", "you", "it", "its", "on", "at", "as", "why",
}


def _keywords(text):
    words = [w.strip("?.,!").lower() for w in text.split()]
    return {w for w in words if w and w not in STOPWORDS}


def answers_the_question(query, answer):
    """
    CHECKS RELEVANCE: a crude but useful signal -- does the answer share
    any meaningful keywords with the question at all? An answer that
    shares zero keywords with the query is very likely answering a
    different question entirely, or dodging the question altogether.
    """
    query_words = _keywords(query)
    answer_words = _keywords(answer)
    if not query_words:
        return True, 1.0
    overlap = query_words & answer_words
    overlap_ratio = len(overlap) / len(query_words)
    return overlap_ratio > 0, overlap_ratio


def length_appropriateness(answer, min_words=8, max_words=150):
    """
    CHECKS LENGTH: an answer that's too short ("Yes.") is often
    unhelpful even if technically correct. An answer that's too long
    risks burying the actual answer in filler. This flags both extremes
    without assuming there's one "correct" length for every question.
    """
    word_count = len(answer.split())
    if word_count < min_words:
        return "too_short", word_count
    if word_count > max_words:
        return "too_long", word_count
    return "appropriate", word_count


def factual_consistency(answer, source_texts):
    """
    CHECKS GROUNDING: a simple proxy for "does the answer actually
    reflect what the sources say" -- what fraction of the answer's
    meaningful words also appear somewhere in the combined source text.
    This can't catch subtle misrepresentation, but it catches the
    obvious case: an answer built almost entirely from words that never
    appear in any source is a strong signal of fabrication.
    """
    answer_words = _keywords(answer)
    if not answer_words:
        return 1.0

    combined_source_words = set()
    for text in source_texts:
        combined_source_words |= _keywords(text)

    grounded = answer_words & combined_source_words
    return len(grounded) / len(answer_words)


def detect_unsupported_claims(answer, source_texts, threshold=0.5):
    """
    DETECTS POSSIBLE FABRICATION: flags an answer whose factual
    consistency score falls below a threshold. This is deliberately
    named "detect_unsupported_claims" rather than "detect hallucination"
    -- a low score means the answer LIKELY contains information not
    grounded in the sources, not a certainty, since some legitimate
    words (common English, question terms) won't appear in sources
    either.
    """
    score = factual_consistency(answer, source_texts)
    return score < threshold, score


def clarity_score(answer):
    """
    CHECKS READABILITY: a simple proxy using average sentence length.
    Very long sentences (packed with clauses) are harder to read than
    several shorter ones, even if the content is identical. This isn't a
    full readability formula (like Flesch-Kincaid), but it captures the
    same basic idea cheaply.
    """
    sentences = [s.strip() for s in re.split(r'[.!?]', answer) if s.strip()]
    if not sentences:
        return 0.0

    avg_words_per_sentence = sum(len(s.split()) for s in sentences) / len(sentences)

    if avg_words_per_sentence <= 20:
        return 1.0
    if avg_words_per_sentence <= 35:
        return 0.6
    return 0.3


def evaluate_answer(query, answer, source_texts):
    """Runs every check and returns one combined quality report."""
    relevant, relevance_score = answers_the_question(query, answer)
    length_status, word_count = length_appropriateness(answer)
    consistency_score = factual_consistency(answer, source_texts)
    unsupported, _ = detect_unsupported_claims(answer, source_texts)
    clarity = clarity_score(answer)

    return {
        "relevant": relevant,
        "relevance_score": relevance_score,
        "length_status": length_status,
        "word_count": word_count,
        "factual_consistency_score": consistency_score,
        "likely_has_unsupported_claims": unsupported,
        "clarity_score": clarity,
    }


def print_report(label, report):
    print(f"--- {label} ---")
    print(f"  Answers the question?    {report['relevant']} (overlap: {report['relevance_score']:.0%})")
    print(f"  Length:                  {report['length_status']} ({report['word_count']} words)")
    print(f"  Factual consistency:     {report['factual_consistency_score']:.0%}")
    print(f"  Likely unsupported?      {report['likely_has_unsupported_claims']}")
    print(f"  Clarity score:           {report['clarity_score']:.1f}")
    print()


def main():
    print("=== Answer Quality Metrics ===\n")

    query = "What is RAG and why does it matter?"
    source_texts = [
        "RAG stands for Retrieval-Augmented Generation. It retrieves relevant "
        "documents before generating an answer.",
        "RAG matters because language models can be outdated. Retrieval lets "
        "them use fresh information without retraining.",
    ]

    good_answer = (
        "RAG (Retrieval-Augmented Generation) retrieves relevant documents "
        "before generating an answer. It matters because it lets language "
        "models use fresh information instead of relying on outdated training."
    )
    print_report("Good answer (grounded, relevant, reasonable length)", evaluate_answer(query, good_answer, source_texts))

    too_short_answer = "It's a search technique."
    print_report("Too-short answer", evaluate_answer(query, too_short_answer, source_texts))

    fabricated_answer = (
        "RAG was invented in 2019 by a team at a major university and won "
        "several awards for its groundbreaking approach to neural architecture "
        "search across distributed cloud computing clusters."
    )
    print_report("Fabricated answer (unrelated invented details)", evaluate_answer(query, fabricated_answer, source_texts))

    off_topic_answer = (
        "Python is a popular programming language known for its readable "
        "syntax and wide use in data science and web development projects."
    )
    print_report("Off-topic answer", evaluate_answer(query, off_topic_answer, source_texts))

    print(
        "These metrics aren't perfect proxies -- factual_consistency() just "
        "checks word overlap, not true semantic accuracy, and could be "
        "fooled by an answer that reuses source WORDS in a false new claim. "
        "But even simple, measurable checks like these catch the most "
        "common failure modes: answers that dodge the question, answers "
        "that are too short to be useful, and answers that appear to "
        "invent information the sources never actually said."
    )


if __name__ == "__main__":
    main()
