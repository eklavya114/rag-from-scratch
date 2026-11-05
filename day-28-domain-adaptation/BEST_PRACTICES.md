# Day 28 Best Practices: Domain Adaptation

## Split before you tune

`domain_dataset.py`'s `split_queries()` runs once, before anything else
in this folder touches the data, and every later script (feedback,
vocabulary, weight tuning) only ever reads from the train split it
returns. Splitting after looking at results, or letting test queries
leak into tuning, defeats the entire purpose of holding anything back.

## Measure on held-out data

`held_out_evaluation.py` is the first and only file in this folder that
touches the test split for anything other than keeping it set aside, and
its numbers are the ones that actually count. `domain_vocabulary.py` and
`ranker_weight_tuning.py` both only ever score against train data, which
tells you how well an adaptation fits the examples it was shown, not
whether it generalizes to a real new question.

## Expect noisy labels

`feedback_collector.py` deliberately flips a small fraction of otherwise
correct labels, simulating the real imprecision of actual user feedback.
An adaptation built to expect perfectly clean labels will be fragile the
moment it meets real feedback, which is never perfectly clean.

## Watch for overfitting

`overfitting_check.py` measures the exact same adapted system on train
and on test, side by side, and found a real, sizeable gap (train scores
noticeably higher than test) even on this small toy adaptation. A large
gap between train and test performance is the clearest available signal
that an adaptation learned the training examples specifically, rather
than learning something that transfers to new questions.

## Prefer simple fixes first

`when_to_fine_tune.py` makes the case directly: a better prompt or
better retrieval often fixes a problem that looks, at first glance, like
it needs real fine-tuning, for far less cost and far less risk. Real
fine-tuning is worth it only once a real, measured gap exists, with
enough stable, labeled data to justify the cost.

## Write down what you shipped and why

`adaptation_report.py` records exactly what changed (which vocabulary
terms, which ranker weights), the real held-out metrics, and a
per-query breakdown of what got better and what got worse, ending in an
explicit ship, collect more feedback, or do not ship recommendation. A
decision like this needs a written record for the same reason Day 21's
regression checks and Day 26's experiment log did: so it can be reviewed
later by someone who was not there when it was made.
