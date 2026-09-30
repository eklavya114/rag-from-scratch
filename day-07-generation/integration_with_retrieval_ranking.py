"""
integration_with_retrieval_ranking.py

Wires together Days 5, 6, and 7 into the full pipeline:

  Day 5: Retriever finds candidate chunks for a query
  Day 6: PracticalRanker re-orders them using similarity + recency + quality
  Day 7: Generator produces a final, attributed answer from the ranked chunks

We also compare generation WITH ranking against generation using
retrieval's raw (un-ranked) order, to show that ranking's effect isn't
just theoretical -- it changes what the generator actually sees, and
therefore what answer comes out.
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "day-05-retrieval"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "day-06-ranking"))
sys.path.insert(0, os.path.dirname(__file__))

from basic_retriever import Retriever, DOCUMENTS                  # Day 5
from practical_ranker import PracticalRanker, DOCUMENT_METADATA   # Day 6
from simple_generator import Generator                             # Day 7
from source_attribution import generate_attributed_answer          # Day 7


def run_full_pipeline(query, retriever, ranker, generator, top_k=5):
    """
    The complete flow: retrieve -> rank -> generate. Returns all three
    intermediate results so we can inspect and compare each stage.
    """
    retrieved = retriever.retrieve(query, top_k=top_k)
    ranked = ranker.rank(retrieved)
    answer = generator.generate_concatenation(query, ranked, max_chunks=2)
    attributed = generate_attributed_answer(query, ranked[:2])
    return retrieved, ranked, answer, attributed


def main():
    print("=== Full Pipeline: Retrieval -> Ranking -> Generation ===\n")

    retriever = Retriever()
    total_chunks = retriever.index_documents(DOCUMENTS)
    ranker = PracticalRanker(metadata=DOCUMENT_METADATA)
    generator = Generator()

    print(f"Indexed {len(DOCUMENTS)} documents into {total_chunks} chunks.\n")

    # This query is deliberately chosen because ranking (recency + quality)
    # actually changes WHICH chunks land in the top 2, not just their
    # order -- so the generated answer's content genuinely differs
    # between "with ranking" and "without ranking" below.
    query = "What programming language is easy to read?"
    retrieved, ranked, answer, attributed = run_full_pipeline(query, retriever, ranker, generator)

    print("=" * 60)
    print(f"Query: \"{query}\"\n")

    print("Step 1 (Day 5 - Retrieval): raw order by similarity")
    for i, r in enumerate(retrieved, start=1):
        print(f"  #{i}: {r['metadata']['title']:20s} similarity={r['similarity']:.3f}")

    print("\nStep 2 (Day 6 - Ranking): re-ordered by similarity + recency + quality")
    for i, r in enumerate(ranked, start=1):
        print(f"  #{i}: {r['metadata']['title']:20s} final_score={r['final_score']:.3f} (driven by: {r['dominant_signal']})")

    print("\nStep 3 (Day 7 - Generation): answer built from the top-RANKED chunks")
    print(answer)

    print("\nStep 3b (Day 7 - Attribution): same top chunks, quoted and cited")
    print(attributed)

    # Now show what generation would have produced WITHOUT ranking --
    # i.e. straight from retrieval's raw similarity order. Since our
    # generator only uses the top max_chunks results, if ranking changed
    # WHICH chunks land in the top 2, the answer itself changes too.
    print("\n" + "=" * 60)
    print("\nWithout ranking (generation straight from retrieval's raw order):\n")
    unranked_answer = generator.generate_concatenation(query, retrieved, max_chunks=2)
    print(unranked_answer)

    ranked_top_2 = {r["metadata"]["title"] for r in ranked[:2]}
    retrieved_top_2 = {r["metadata"]["title"] for r in retrieved[:2]}

    print("\n" + "=" * 60)
    if ranked_top_2 == retrieved_top_2:
        print(
            "\nFor this particular query, ranking didn't change WHICH chunks "
            "ended up in the top 2 (only their internal order) -- so the "
            "generated answer's content is the same either way. Ranking's "
            "impact isn't always visible in the final text; sometimes its "
            "job is simply confirming retrieval already got it right."
        )
    else:
        print(
            "\nNotice the top 2 chunks are DIFFERENT with vs. without "
            "ranking -- which means the generated answer itself is built "
            "from different source material. This is the concrete proof "
            "that ranking isn't a cosmetic reordering step: it can change "
            "what information actually reaches the user.\n\n"
            "Worth being honest about here: in THIS case, ranking's "
            "recency weight pulled in a barely-relevant 'What is RAG' "
            "chunk ahead of a genuinely on-topic Python-readability chunk "
            "that retrieval alone would have used instead. The generated "
            "answer arguably got WORSE, not better. This is the same "
            "lesson Day 6 already surfaced: a ranking signal that helps "
            "some queries can actively hurt others, and generation has no "
            "way to correct for that -- it can only work with whatever "
            "ranking hands it. That's exactly why ranking weights need to "
            "be evaluated (Day 6's ranking_evaluation.py), not just "
            "trusted by default."
        )


if __name__ == "__main__":
    main()
