# Day 30 Best Practices: Releasing a Learning Project

## Verify with a script

`release_check.py` runs real checks, every day folder exists, every day
has its README and BEST_PRACTICES.md, the changelog mentions every
week, and Day 29's `main.py` and `tests.py` both actually run as
subprocesses and exit cleanly. A checklist filled in by hand only
reflects whatever someone remembered to look at, and goes stale the
moment the project changes under it. A script re-checks the same real
facts every time, which is what makes "this release was verified" true.

## Keep a changelog

`CHANGELOG.md` gives one short, plain-language line per day, grouped by
week, and marks this state as v1.0.0. Six months from now, nobody
should need to re-read every day's README to remember what Day 17 or
Day 24 actually added, the changelog is the fast, trustworthy answer to
that question.

## Be honest about limits

The top-level `launch_readme.md`'s "what this is not" section states
plainly: no real embedding model, no real vector database, no real
language model, and not a security audit. Stating a project's real
limits clearly is not an apology, it is exactly what makes every other
claim in the project, its metrics, its security checks, its evaluation
results, trustworthy, since nothing is pretending to be more than it
honestly is.

## Make the entry point obvious

`launch_readme.md`'s "how to start in 3 steps" points straight at
`day-29-complete-system/main.py`. A project with 30 folders and
hundreds of files needs exactly one clearly stated place a newcomer
should run first, or they are left guessing which of many scripts is
the real starting point.

## Tag a version

Once `release_check.py` passes, this exact, verified state gets tagged
as v1.0.0. A tag is a permanent, named bookmark: anyone can come back to
precisely what "done" looked like at this point, regardless of whatever
changes happen in the repository afterward.
