"""
visualization.py

A text-only way to "see" embeddings clustering together. No charting
library, no matplotlib -- just print statements and basic ASCII bars.

We take 10 sample words, calculate the similarity between every pair,
and show which ones cluster close together. If embeddings are working
the way they should, animals will cluster with animals, vehicles will
cluster with vehicles, and food will cluster with food.
"""

from embedding_basics import cosine_similarity


# 10 words across 3 categories (animals, vehicles, food), plus their fake
# embeddings. Same idea as embedding_basics.py: we hand-picked these numbers
# so words in the same category point in similar directions.
WORDS = {
    "cat":     [0.9, 0.8, 0.1, 0.1, 0.1],
    "dog":     [0.8, 0.9, 0.1, 0.2, 0.1],
    "kitten":  [0.85, 0.75, 0.15, 0.1, 0.1],
    "car":     [0.1, 0.1, 0.9, 0.8, 0.1],
    "truck":   [0.1, 0.2, 0.8, 0.9, 0.1],
    "bicycle": [0.15, 0.1, 0.85, 0.7, 0.1],
    "pizza":   [0.1, 0.1, 0.1, 0.1, 0.9],
    "burger":  [0.1, 0.15, 0.1, 0.1, 0.85],
    "pasta":   [0.15, 0.1, 0.1, 0.15, 0.8],
    "bus":     [0.1, 0.15, 0.75, 0.85, 0.1],
}


def all_pairs(words):
    """
    Generates every unique pair of words, without repeating a pair
    in both orders (so we get "cat, dog" but not also "dog, cat").
    """
    word_list = list(words.keys())
    for i in range(len(word_list)):
        for j in range(i + 1, len(word_list)):
            yield word_list[i], word_list[j]


def calculate_all_distances(words):
    """
    Computes cosine similarity for every pair of words and returns a
    list of (word_a, word_b, similarity) sorted from most similar
    to least similar.
    """
    results = []
    for word_a, word_b in all_pairs(words):
        similarity = cosine_similarity(words[word_a], words[word_b])
        results.append((word_a, word_b, similarity))

    results.sort(key=lambda item: item[2], reverse=True)
    return results


def print_bar_chart(results, top_n=10):
    """
    Draws a simple ASCII bar chart for the most similar word pairs.
    Each '#' represents a chunk of similarity, so longer bars mean
    the two words are more alike.
    """
    print(f"Top {top_n} most similar word pairs:\n")
    for word_a, word_b, similarity in results[:top_n]:
        bar_length = int(similarity * 40)  # scale 0.0-1.0 up to 0-40 chars
        bar = "#" * bar_length
        pair_label = f"{word_a} <-> {word_b}"
        print(f"  {pair_label:20s} {bar} {similarity:.3f}")


def find_clusters(words, threshold=0.9):
    """
    Groups words into rough clusters: any two words with similarity
    above the threshold are considered "close" and grouped together.
    This is a simplified stand-in for real clustering algorithms.
    """
    word_list = list(words.keys())
    clusters = []
    assigned = set()

    for word in word_list:
        if word in assigned:
            continue

        cluster = [word]
        assigned.add(word)

        for other_word in word_list:
            if other_word in assigned:
                continue
            similarity = cosine_similarity(words[word], words[other_word])
            if similarity >= threshold:
                cluster.append(other_word)
                assigned.add(other_word)

        clusters.append(cluster)

    return clusters


def main():
    print("=== Embedding Visualization Demo ===\n")

    results = calculate_all_distances(WORDS)
    print_bar_chart(results, top_n=10)

    print("\n" + "=" * 60)
    print("\nClusters found (words grouped by similarity >= 0.9):\n")
    clusters = find_clusters(WORDS, threshold=0.9)
    for i, cluster in enumerate(clusters, start=1):
        print(f"  Cluster {i}: {', '.join(cluster)}")

    print(
        "\nNotice how animals grouped with animals, vehicles with "
        "vehicles, and food with food -- even though we never told "
        "the program what an 'animal' or 'vehicle' is. That grouping "
        "came entirely from the numbers being close together."
    )


if __name__ == "__main__":
    main()
