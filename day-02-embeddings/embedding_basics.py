"""
embedding_basics.py

Shows the core idea behind embeddings using plain Python, no ML libraries.

We hand-craft small, fake embeddings for a handful of words. These are NOT
real embeddings from a trained model -- we picked the numbers ourselves so
that similar words (like "cat" and "dog") end up with similar numbers on
purpose. This lets us focus on the MATH of comparing embeddings, without
needing to train or download a real model.
"""

import math


# Each word is represented by a list of 4 numbers. Think of these 4 numbers
# as coordinates on a tiny 4-dimensional map. Real embeddings usually have
# hundreds of numbers, but 4 is easier to reason about by hand.
#
# We designed these numbers so that:
#   - animals (cat, dog, puppy, kitten) all point in a similar direction
#   - vehicles (car, truck) all point in a similar (but different) direction
#   - "cat" and "car" point in very different directions, even though they
#     share 2 out of 3 letters -- proving embeddings care about MEANING,
#     not spelling.
WORD_EMBEDDINGS = {
    "cat":    [0.9, 0.8, 0.1, 0.2],
    "dog":    [0.8, 0.9, 0.2, 0.1],
    "kitten": [0.85, 0.75, 0.15, 0.25],
    "puppy":  [0.75, 0.85, 0.25, 0.15],
    "car":    [0.1, 0.2, 0.9, 0.8],
    "truck":  [0.2, 0.1, 0.8, 0.9],
}


def dot_product(vector_a, vector_b):
    """
    Multiplies matching positions in two vectors and adds up the results.
    This is the core building block of cosine similarity below.
    Example: dot_product([1, 2], [3, 4]) = (1*3) + (2*4) = 11
    """
    return sum(a * b for a, b in zip(vector_a, vector_b))


def magnitude(vector):
    """
    The "length" of a vector, as if you were measuring it with a ruler.
    We need this to make sure we're comparing DIRECTION, not size.
    Two vectors can point the same direction but have different lengths --
    cosine similarity cares about the direction, so we divide it out.
    """
    return math.sqrt(sum(x * x for x in vector))


def cosine_similarity(vector_a, vector_b):
    """
    Measures how similar two embeddings are, as a number from -1 to 1:
        1.0  -> pointing in exactly the same direction (very similar)
        0.0  -> pointing in unrelated directions (no relationship)
       -1.0  -> pointing in opposite directions (opposite meaning)

    The formula is: (dot product of the two vectors) / (their lengths multiplied)
    In plain English: "how aligned are these two arrows, ignoring how long they are?"
    """
    dot = dot_product(vector_a, vector_b)
    mag_a = magnitude(vector_a)
    mag_b = magnitude(vector_b)

    if mag_a == 0 or mag_b == 0:
        # Can't compare a zero-length vector to anything meaningfully.
        return 0.0

    return dot / (mag_a * mag_b)


def compare_words(word_a, word_b):
    """
    Looks up two words' embeddings and prints how similar they are.
    Just a friendly wrapper around cosine_similarity() for the demo below.
    """
    embedding_a = WORD_EMBEDDINGS[word_a]
    embedding_b = WORD_EMBEDDINGS[word_b]
    similarity = cosine_similarity(embedding_a, embedding_b)
    print(f"  {word_a} <-> {word_b}: {similarity:.3f}")
    return similarity


def main():
    print("=== Embedding Basics Demo ===\n")

    print("Word embeddings (words as lists of numbers):")
    for word, embedding in WORD_EMBEDDINGS.items():
        print(f"  {word:8s} -> {embedding}")

    print("\nSimilar words (should score close to 1.0):")
    compare_words("cat", "dog")
    compare_words("cat", "kitten")
    compare_words("car", "truck")

    print("\nDifferent words (should score much lower):")
    compare_words("cat", "car")
    compare_words("dog", "truck")
    compare_words("kitten", "truck")


if __name__ == "__main__":
    main()
