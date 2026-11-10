# Day 2 Best Practices: Embeddings

Always compare embedding-based search against keyword search on the
same queries. `comparison.py` exists specifically because an embedding
approach is only actually better if you can show it finding things
keyword search misses, not just because it sounds more sophisticated.

Remember a toy embedding is a real embedding's shape, not its power.
This project's hand-built concept vocabulary demonstrates the exact
math (cosine similarity over a vector) a real embedding model uses,
while being honest that a handful of hand-picked word groups is nowhere
near what a model trained on huge amounts of real text actually
captures.

Check what a query's embedding actually looks like before trusting it.
A query sharing no vocabulary with your embedding's concept list
produces an all-zero vector, silently, which later stages would treat
as "nothing matched" without ever explaining why.
