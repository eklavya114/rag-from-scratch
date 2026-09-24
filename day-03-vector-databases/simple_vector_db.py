"""
simple_vector_db.py

A real, working vector database, built from scratch with plain Python.

It does exactly two things, same as any vector database:
  1. Store embeddings, along with whatever metadata you want attached to them
     (like the original text, a title, a source).
  2. Given a new embedding, find the top K stored embeddings most similar to it.

This version uses BRUTE FORCE search: to answer a query, it checks every single
stored embedding, one at a time. That's the simplest possible approach, and it's
exactly what real vector databases avoid doing once you have millions of vectors
(see indexing_basics.py for why). But brute force is the right place to start,
because it's honest and easy to follow.
"""

import math


def cosine_similarity(vector_a, vector_b):
    """
    Same cosine similarity from Day 2: measures how similar two embeddings
    are, from -1 (opposite) to 1 (identical direction).
    """
    dot = sum(a * b for a, b in zip(vector_a, vector_b))
    mag_a = math.sqrt(sum(a * a for a in vector_a))
    mag_b = math.sqrt(sum(b * b for b in vector_b))

    if mag_a == 0 or mag_b == 0:
        return 0.0

    return dot / (mag_a * mag_b)


class SimpleVectorDB:
    """
    A minimal vector database. Stores (embedding, metadata) pairs and lets
    you search for the most similar ones to a query embedding.

    Real vector databases add a lot on top of this: fast indexing, disk
    storage, filtering, replication, etc. But the core idea -- store
    vectors, search by similarity -- is exactly what's happening here.
    """

    def __init__(self):
        # Each entry is a dict: {"id": ..., "embedding": [...], "metadata": {...}}
        # Using a plain list keeps this transparent -- you can see exactly
        # where every vector lives.
        self.entries = []
        self._next_id = 1

    def add(self, embedding, metadata=None):
        """
        Stores one embedding, along with optional metadata (like the
        original text or a title). Returns the id assigned to this entry,
        so you can look it up again later if needed.
        """
        entry = {
            "id": self._next_id,
            "embedding": embedding,
            "metadata": metadata or {},
        }
        self.entries.append(entry)
        self._next_id += 1
        return entry["id"]

    def add_many(self, items):
        """
        Convenience method to add several (embedding, metadata) pairs at
        once. Just calls add() in a loop -- there's no trick here, it's
        just less typing when you're loading a whole dataset.
        """
        ids = []
        for embedding, metadata in items:
            ids.append(self.add(embedding, metadata))
        return ids

    def search(self, query_embedding, top_k=3):
        """
        BRUTE FORCE SEARCH: compares the query embedding against every
        single stored embedding, computes cosine similarity for each one,
        and returns the top_k most similar entries.

        This is simple and always finds the true best matches -- there's
        no approximation happening. The tradeoff is speed: this gets
        slower the more entries you store, because every search has to
        touch every entry. See indexing_basics.py for how real vector
        databases avoid this.
        """
        scored = []
        for entry in self.entries:
            similarity = cosine_similarity(query_embedding, entry["embedding"])
            scored.append((entry, similarity))

        # Best matches first.
        scored.sort(key=lambda pair: pair[1], reverse=True)

        results = []
        for entry, similarity in scored[:top_k]:
            results.append({
                "id": entry["id"],
                "similarity": similarity,
                "metadata": entry["metadata"],
            })
        return results

    def __len__(self):
        return len(self.entries)


def main():
    print("=== Simple Vector Database Demo ===\n")

    db = SimpleVectorDB()

    # Reuse the same fake word embeddings style from Day 2.
    db.add([0.9, 0.8, 0.1, 0.2], {"word": "cat"})
    db.add([0.8, 0.9, 0.2, 0.1], {"word": "dog"})
    db.add([0.85, 0.75, 0.15, 0.25], {"word": "kitten"})
    db.add([0.1, 0.2, 0.9, 0.8], {"word": "car"})
    db.add([0.2, 0.1, 0.8, 0.9], {"word": "truck"})

    print(f"Stored {len(db)} embeddings.\n")

    query = [0.88, 0.82, 0.12, 0.18]  # something close to "cat"
    print(f"Searching for something similar to: {query}\n")

    results = db.search(query, top_k=3)
    for rank, result in enumerate(results, start=1):
        word = result["metadata"]["word"]
        similarity = result["similarity"]
        print(f"  #{rank}: {word:8s} (similarity {similarity:.3f})")


if __name__ == "__main__":
    main()
