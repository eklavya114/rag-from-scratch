# Day 28: Fine-Tuning and Domain Adaptation

## Generic knowledge versus local knowledge

A generic model is good at general language: grammar, common topics, the
shape of a normal sentence. It has never seen your company's own
vocabulary, your specific products, or the exact words your customers
actually use. A support ticket that mentions an "RMA" or a "chargeback"
means something very specific in your domain, and a generic system has
no built-in reason to treat those words as important.

## What fine-tuning means, and why it is expensive in real life

Fine-tuning a real model means training it further on examples from your
own domain, so it picks up your specific vocabulary and patterns on top
of what it already knows. Done properly, this takes real labeled data,
real compute (often a GPU, sometimes many), and real ongoing maintenance
as your domain keeps changing. It is a genuine engineering investment,
not a quick toggle.

## What we can honestly do here

This project has no GPU, no real model to fine-tune, and no internet
access, so nothing here is real fine-tuning. What we CAN do, honestly,
is adapt the toy components this project already built, retrieval's
vocabulary and the ranker's weights, using labeled domain feedback, and
then measure whether that adaptation actually helped. The underlying
idea is identical to real fine-tuning: collect examples, adjust
something based on them, measure the result on data the adjustment never
saw. Only the scale and the tools are smaller.

## The most important rule

Measure on HELD-OUT data the adaptation never saw. Adjusting something
based on a set of examples and then checking whether it helps using
those SAME examples will always look good, since you are testing on the
very thing you optimized for. Splitting data into a training set and a
held-out test set, before any tuning happens, is what makes a measured
improvement trustworthy instead of a number you accidentally rigged in
your own favor.

## What we're building today

A small labeled domain dataset split into train and test before any
tuning begins, a feedback collector that simulates noisy real-world
feedback from the train split only, a domain vocabulary builder that
learns new terms from train data, a ranker weight tuner that searches a
small grid on train feedback, a held-out evaluation that is the only
number that actually counts, an overfitting check that shows what
measuring on the wrong data looks like, and a written adaptation report.

## The new hire analogy

A new hire starts with the same general knowledge and judgment anyone in
their role would have. What makes them effective at YOUR company
specifically is reading your own manuals, learning your own product
names, and picking up the particular way your customers phrase their
problems. Same brain, better local knowledge. Nobody retrains the new
hire's entire personality, they just learn the specifics of this one
job. Today's adaptation works the same way: the retriever and ranker
keep their same underlying logic, they just pick up a bit of local,
domain-specific knowledge on top.

## How this connects to Day 8 and Day 9

Day 8 built the real precision, recall, NDCG, and MRR metrics this
entire adaptation is measured with, reused directly here on the held-out
test split, the exact same discipline applied to a domain-specific
question instead of a general one. Day 9 covered when and how to choose
a real embedding model, including a brief look at what real fine-tuning
involves. Today's `when_to_fine_tune.py` picks up that thread directly:
given what Day 9 already explained about real models, when is spending
on an actual fine-tuning run worth it, and when does a simpler fix (a
better prompt, better retrieval, more relevant documents) solve the same
problem for far less cost.
