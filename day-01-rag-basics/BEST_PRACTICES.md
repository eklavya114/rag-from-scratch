# Day 1 Best Practices: RAG Basics

Keep retrieval and generation as two separate, visible steps, not one
black box. When something goes wrong with an answer, you need to be
able to ask "did it find the wrong document, or did it misread the
right one" separately, which is only possible if those two steps are
actually separate in your code, not fused together.

Test with real, known documents. `test_basic.py` checks against a small
set of documents where you already know what the right answer should
be, since you cannot tell whether retrieval found the right thing if
you do not already know what the right thing is.

Start with keyword search before reaching for anything fancier.
Keyword search is simple, fast, and easy to debug, exactly why it is
the baseline every later day's improvement gets compared against.
