# Day 29 Best Practices: Building a Complete Project

## Keep one config

`config.py` is the only place `top_k`, `rank_weights`, `cache_size`,
`max_query_length`, and the demo API key are defined. `pipeline.py`,
`service.py`, and `evaluate.py` all import this one `Config`, never
hardcoding their own copy of a setting. A project with settings
scattered across several files is one small edit away from two parts of
the system quietly disagreeing about a value as basic as how many
results to retrieve.

## Import instead of copying

Every file in this folder imports real functions and classes from Days
1 through 28, `chunk_by_paragraphs` from Day 4, `PracticalRanker` from
Day 6, `check_permission` from Day 27, rather than pasting a modified
copy of any of them. A bug fixed in an earlier day's file is
automatically fixed here too. A real module-name collision bug (two
different `config.py` files both importable as plain `config`) was
caught during this exact integration, exactly the kind of problem
importing honestly, instead of copying, is meant to surface early.

## Test the public entry point

`tests.py` exercises `ProjectService.answer()`, the one method anything
outside this project would actually call, not just the individual pieces
behind it in isolation. Testing the public entry point is what confirms
the real ORDER of operations (access control, then validation, then the
injection check, then the real pipeline) actually behaves correctly
together, not just that each piece works on its own.

## Make the structure checkable

`run_all_days.py` checks that every one of the 29 day folders still has
its README, its best practices notes, and at least one runnable script,
in well under a second, without running a single demo. A project this
size cannot be kept intact by memory alone, a cheap, fast structural
check is what catches a missing or accidentally deleted file before it
becomes a surprise.

## Be honest about what the toy parts can and cannot do

`pipeline.py`'s own docstring states plainly that Day 2's original
embedding vocabulary shares no words at all with this project's support
knowledge base, confirmed directly by testing it, and explains the
domain-appropriate concept list used instead. The README does the same
for the toy vector store and the lack of a real language model. Honesty
about a toy system's real limits is what makes every claim elsewhere in
this project trustworthy.

## Write a README a stranger can follow

This folder's `README.md` explains what the project is, how to run it
with one command, how to run the tests, what the system deliberately
does not do, and what to build next, in that order, assuming no prior
context beyond being able to run `python main.py`. A complete project
is not actually complete until someone who was not there when it was
built can pick it up and understand it.
