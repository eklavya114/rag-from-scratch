# Day 23: Deploying RAG as an API

## The gap between a service that runs on your laptop and one other people can call

Day 22 built a `RagService` with one clean entry point, `query()`. It
runs correctly, but only inside a Python process you start yourself, on
your own machine. Nobody outside that process can reach it. A service
that only you can call is not useful to anyone else yet. Getting from
"it works on my laptop" to "other people can actually use it" means
putting a door in front of it: a fixed way for any program, written in
any language, on any machine, to send it a request and get a response
back.

## What an API is, in plain words

An API is a door with fixed rules. You do not need to know anything
about the kitchen behind it. You knock in a specific way (send a
request, in an agreed format, to a specific address), and you get a
specific kind of answer back (a response, in an agreed format, with a
status telling you what happened). The rules are fixed so that anyone
can knock correctly, without needing to understand how the kitchen
actually cooks.

## The endpoints we are building

- `POST /query`: ask a real question, get back an answer, its sources, and a status
- `GET /health`: ask whether the service is currently working correctly
- `GET /metrics`: ask for the numbers behind that: request counts, error rate, latency

## What Docker does

Docker packs the code and the exact Python version it needs into one
self-contained box, called an image. That image runs the same way on
your laptop, a teammate's laptop, or a real server, because it carries
its own environment with it instead of depending on whatever happens to
already be installed on whichever machine runs it.

## What we're building today

A small HTTP server, built entirely with Python's standard library
(`http.server` and `json`, nothing installed), that wraps the Day 22
`RagService` behind the three endpoints above. On top of that: a simple
API key check and a rate limit, a Dockerfile describing how the service
would be packaged, and deployment notes describing how it would actually
get shipped and rolled back.

## The restaurant, continued

Day 22's restaurant kitchen had order tickets, timing, a cleanup
routine, and a health inspector, everything needed to run well
internally. What it still lacked was a front door and a menu board.
Today adds exactly that: a door anyone can walk up to (`POST /query`), a
sign showing whether the kitchen is currently open (`GET /health`), and
a board showing how busy it has been (`GET /metrics`). The recipes
inside have not changed since Day 22. What changed is that strangers can
now actually walk in and order.

## How this ties to Day 22

`api_server.py` does not reimplement retrieval, ranking, generation, or
caching. It imports the real `RagService`, `Config`, and
`ServiceMetrics` built on Day 22 and calls them exactly as Day 22 itself
did, just reached over HTTP instead of a direct Python method call. Every
status Day 22's `RagResponse` already produces (`ok`, `rejected`,
`no_results`, `error`) gets mapped to a specific HTTP status code today,
so a client speaking plain HTTP sees the same honest distinctions Day 22
built internally.
