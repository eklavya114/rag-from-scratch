# Day 3 Best Practices: Vector Databases

Benchmark before assuming a vector database is fast enough. `benchmark.py`
exists because "it feels fast with six documents" tells you nothing
about how it behaves at a thousand, or a million, and real vector
databases exist specifically to solve the performance problem a plain
list-and-compare search runs into at scale.

Know the difference between a toy implementation and a real one.
`SimpleVectorDB` stores every embedding in a Python list and checks
every one of them on every search, which is fine for a handful of
documents and completely impractical past that, `real_vector_dbs.py`
and `COMPARISON.md` cover what a real indexed database actually does
differently.

Keep metadata attached to every stored embedding, not just the vector
itself. A search result that cannot tell you which document, which
chunk, or which title it came from is not actually useful, regardless
of how accurate the similarity score is.
