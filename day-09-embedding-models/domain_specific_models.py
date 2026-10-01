"""
domain_specific_models.py

Shows where a domain-specialized embedding model beats a general-purpose
one, and where it doesn't. We simulate this the same way as
model_comparison.py: different concept vocabularies standing in for
different models, each "specialized" by having rich vocabulary for ONE
domain and sparse vocabulary for everything else.
"""

import os
import sys
import math

sys.path.insert(0, os.path.dirname(__file__))


def cosine_similarity(a, b):
    dot = sum(x * y for x, y in zip(a, b))
    ma = math.sqrt(sum(x * x for x in a))
    mb = math.sqrt(sum(y * y for y in b))
    return dot / (ma * mb) if ma and mb else 0.0


# Each domain is broken into multiple SUB-CONCEPTS (not one lump bucket
# per domain), so comparisons have real multi-dimensional structure.
# With only one dimension per domain, cosine similarity trivially hits
# 1.0 whenever query and document share ANY word in that bucket,
# regardless of how much vocabulary a "specialized" model actually adds
# -- a low-dimensional artifact we first ran into back on Day 5/6.
# Sub-concepts avoid that and let richer vocabulary actually show up as
# a measurably higher similarity score, not just a tied 1.0.

GENERAL_PURPOSE_CONCEPTS = {
    "legal_core": ["agreement", "contract", "party"],
    "legal_detail": ["liability", "clause"],
    "medical_core": ["patient", "diagnosis"],
    "medical_detail": ["treatment", "symptom", "dosage"],
    "code_core": ["function", "variable"],
    "code_detail": ["loop", "array", "exception"],
}

# A LEGAL-SPECIALIZED model: much richer legal vocabulary spread across
# several sub-concepts, but the same shallow coverage elsewhere --
# simulating a model fine-tuned heavily on legal text at the cost of
# specializing away from other domains.
LEGAL_SPECIALIZED_CONCEPTS = {
    "legal_core": ["agreement", "contract", "party"],
    "legal_detail": ["liability", "clause"],
    "legal_remedies": ["indemnify", "termination", "breach", "covenant"],
    "legal_procedure": ["jurisdiction", "warranty", "severability"],
    "medical_core": ["patient", "diagnosis"],
    "code_core": ["function", "variable"],
}

# A MEDICAL-SPECIALIZED model: same idea, specialized for health terms.
MEDICAL_SPECIALIZED_CONCEPTS = {
    "legal_core": ["agreement", "contract"],
    "medical_core": ["patient", "diagnosis"],
    "medical_detail": ["treatment", "symptom", "dosage"],
    "medical_prognosis": ["contraindication", "prognosis", "etiology", "comorbidity"],
    "medical_clinical": ["pathology", "prescription"],
    "code_core": ["function", "variable"],
}

# A CODE-SPECIALIZED model: specialized for programming terminology.
CODE_SPECIALIZED_CONCEPTS = {
    "legal_core": ["agreement", "contract"],
    "medical_core": ["patient", "diagnosis"],
    "code_core": ["function", "variable"],
    "code_detail": ["loop", "array", "exception"],
    "code_advanced": ["recursion", "pointer", "compiler", "runtime"],
    "code_systems": ["asynchronous", "middleware", "dependency"],
}


MODELS = {
    "General-purpose": GENERAL_PURPOSE_CONCEPTS,
    "Legal-specialized": LEGAL_SPECIALIZED_CONCEPTS,
    "Medical-specialized": MEDICAL_SPECIALIZED_CONCEPTS,
    "Code-specialized": CODE_SPECIALIZED_CONCEPTS,
}


def embed(text, concepts):
    words = set(w.strip("?.,!").lower() for w in text.split())
    return [float(sum(1 for w in words if w in concept_words)) for concept_words in concepts.values()]


# One representative query + matching document per domain, used to
# measure how well each model's vocabulary captures domain-specific
# meaning beyond the few words the GENERAL model already knows.
DOMAIN_TEST_CASES = {
    "legal": {
        "query": "What happens if a party breaches the agreement and needs to indemnify the other?",
        "document": "This contract's termination clause covers breach of covenant, including indemnification obligations and jurisdiction for disputes.",
    },
    "medical": {
        "query": "What's the prognosis given the patient's comorbidity and contraindication?",
        "document": "The diagnosis considers the patient's prognosis, comorbidity, and contraindication before treatment.",
    },
    "code": {
        "query": "Why does this recursive function cause a runtime exception with async middleware?",
        "document": "The recursion depth triggers a runtime exception because the asynchronous middleware introduces a dependency on an uninitialized pointer.",
    },
}


def main():
    print("=== Domain-Specific Embedding Models ===\n")

    print(f"{'Domain':<10} | " + " | ".join(f"{name:<19}" for name in MODELS))
    print("-" * (12 + 22 * len(MODELS)))

    domain_scores = {domain: {} for domain in DOMAIN_TEST_CASES}

    for domain, case in DOMAIN_TEST_CASES.items():
        row = [f"{domain:<10}"]
        for model_name, concepts in MODELS.items():
            similarity = cosine_similarity(embed(case["query"], concepts), embed(case["document"], concepts))
            domain_scores[domain][model_name] = similarity
            row.append(f"{similarity:<19.3f}")
        print(" | ".join(row))

    print()
    print("--- Where each specialized model wins ---\n")
    for domain, scores in domain_scores.items():
        best_model = max(scores, key=scores.get)
        general_score = scores["General-purpose"]
        best_score = scores[best_model]
        gap = best_score - general_score
        print(f"  {domain:8s}: best = {best_model} ({best_score:.3f}), general-purpose = {general_score:.3f} (gap: {gap:+.3f})")

    print()
    print("--- Where specialization DOESN'T help ---\n")
    off_domain_query = "What is RAG and how does retrieval work?"
    off_domain_doc = "RAG retrieves relevant documents using embeddings before generating an answer."
    print(f'Query: "{off_domain_query}" (not legal, medical, or code -- none of our models cover this)\n')
    for model_name, concepts in MODELS.items():
        similarity = cosine_similarity(embed(off_domain_query, concepts), embed(off_domain_doc, concepts))
        print(f"  {model_name:<20}: {similarity:.3f}")

    print(
        "\nNotice all models score near zero on the off-domain RAG query -- "
        "NONE of them have vocabulary for it. This is the honest limit of "
        "specialization: a legal model being great at legal text tells you "
        "nothing about how it'll perform on content outside its "
        "specialty. Specialized models win decisively within their "
        "domain and are no better than a coin flip outside it -- which is "
        "exactly why picking one means first being confident about what "
        "domain your actual documents live in."
    )


if __name__ == "__main__":
    main()
