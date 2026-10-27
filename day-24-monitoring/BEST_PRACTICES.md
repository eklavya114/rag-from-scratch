# Day 24 Best Practices: Monitoring RAG

## Watch the four signals

`instrumented_service.py` records exactly these four: traffic
(`requests_total`), errors (`requests_total` labeled by status), latency
(`request_latency_ms` and `stage_latency_ms`), and saturation
(`in_flight_requests`). `dashboard_sketch.py` builds its panels directly
around them. These four, together, catch almost everything worth
watching about a running service, which is why they are the starting
point before adding anything more specific.

## Alert on symptoms users feel

`alert_rules.py`'s error rate and p95 latency checks both measure things
a real user directly experiences: a failed request, or a slow one. Its
cache hit rate check is different on purpose, a falling hit rate is not
itself something a user feels, it is a leading indicator that latency is
likely to rise soon after, caught earlier specifically so the
user-facing symptom can be headed off before it happens.

## Use percentiles, not averages

`percentile_tracking.py` shows concretely what `traffic_simulation.py`
then demonstrates on real data: an average can barely move while p95
jumps straight into a genuinely slow range, because a mean blends a
small number of slow requests into a much larger number of fast ones.
Alerting on an average risks staying silent exactly when a meaningful
share of real users are already having a bad experience.

## Keep request ids in logs

`log_correlation.py`'s request id travels with a request from the
moment `RagService.query()` creates it, into the structured log line,
and into the returned response. Without that id tying every signal to
the same request, a metric telling you something was slow and a log
line describing one particular request have no way to be connected back
to each other.

## Tune thresholds to avoid alert fatigue

`alert_rules.py`'s `check_in_flight_sustained` requires the same high
reading across three consecutive samples, not just one, specifically so
a brief, normal traffic burst never fires an alert on its own. A
threshold tuned too sensitively trains whoever is on call to ignore
alerts, which is far more dangerous than a quiet monitoring system,
since the next alert that fires might be the one that actually mattered.
