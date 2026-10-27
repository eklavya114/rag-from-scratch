# Day 24: Monitoring and Observability

## Logs, metrics, and traces, in plain words

- **Logs** are individual events: one line per thing that happened, with
  detail. Good for answering "what exactly happened on this one request."
- **Metrics** are numbers that accumulate over time: how many requests,
  how many errors, how long things took. Good for answering "how is the
  whole service doing right now, and how was it doing an hour ago."
- **Traces** follow one request across every stage it passes through.
  Good for answering "where exactly, inside this one slow request, did
  the time go."

Day 22 already built structured logs. Today adds metrics and a simple
way to trace one request across stages using the request id logs
already carry.

## Why you need to see things over time, not just once

A single number tells you almost nothing. "The error rate is 2%" could
mean a healthy service, or a service that just started failing a minute
ago and is climbing fast. Only watching the same number repeatedly,
over time, lets you tell those apart, and that is the entire reason
metrics exist: not to answer one question once, but to keep answering
it, continuously, so a trend becomes visible before it becomes a crisis.

## The four signals to watch

- **Latency**: how long requests take
- **Traffic**: how many requests are coming in
- **Errors**: how many requests are failing
- **Saturation**: how close the service is to its limits (for example,
  how many requests are in flight at once)

These four, together, cover almost everything worth watching about a
running service. A problem that matters to a real user almost always
shows up in at least one of them.

## What we're building today

A tiny metrics library (counters, gauges, histograms), a way to wrap Day
22's RagService with metrics without changing RagService itself, a text
metrics endpoint any scraper could read, a set of alert rules evaluated
against real numbers, a traffic simulation that shows the four signals
actually moving, a way to trace one request's stages using its request
id, and a plain text dashboard sketch.

## The car dashboard analogy

A car's dashboard shows speed, fuel, and an engine warning light. You do
not open the hood every mile to check if the engine is fine. The
dashboard is designed so a glance tells you whether everything is
normal, and a warning light tells you exactly when it is not. Today's
work is that dashboard for a RAG service: metrics are the gauges, alert
rules are the warning lights, and the four signals are what every
dashboard, on every car or every service, ends up built around.

## How this connects to Day 22 and Day 23

Day 22 built structured logging and a health check. Today's metrics
reuse the exact same stage timings and request statuses Day 22's
`RagResponse` and `ServiceMetrics` already produce, just accumulated
into counters and histograms instead of only being averaged once per
batch. Day 23 built an HTTP API with a `/metrics` JSON endpoint. Today
adds a second metrics endpoint in the Prometheus text format, the
standard way a real monitoring system actually scrapes a service, built
on top of Day 23's server without editing it.
