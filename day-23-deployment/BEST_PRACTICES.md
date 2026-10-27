# Day 23 Best Practices: Deploying RAG as an API

## Keep secrets out of code

`auth_and_rate_limit.py`'s `get_configured_api_key()` reads the real key
from `RAG_API_KEY`, falling back to a key that is clearly labeled
"do-not-use-in-real-deployments". A key hardcoded in source code ends up
in version control history forever, readable by anyone with repository
access, even after the line is later deleted. `deploy_notes.md` makes the
same point for a real deployment: the key is passed in at `docker run`
time, never written into the image.

## Cap body size

`request_handling_rules.py`'s `MAX_BODY_SIZE_BYTES` and `api_server.py`'s
`_read_body()` reject any request larger than the limit with a 413,
before ever attempting to parse it as JSON. An uncapped body size lets
one request consume unbounded memory just by being large, a cheap way
for a single bad actor to degrade the whole service for everyone else.

## Return safe errors

`api_server.py`'s `_send_error_json()` is the only place any error
response gets built, and it only ever sends a clean, readable message,
never a raw exception or stack trace. The security review of this
folder's own code caught a real version of what this protects against:
an early version of `_read_body()` could leave a connection in a state
where a later request on the same connection got misread, exactly the
kind of subtle failure a safe, deliberate error path prevents.

## Use health checks

`GET /health` reports `healthy`, `degraded`, or `unhealthy`, backed by
Day 22's real `ServiceMetrics`, with `unhealthy` mapped to HTTP 503 so a
load balancer or monitoring system can act on it automatically. A
service with no health check can only be judged by whether individual
requests happen to succeed, which misses a service that is technically
up but failing most of its real traffic.

## Rate limit public endpoints

`auth_and_rate_limit.py`'s `FixedWindowRateLimiter` caps each API key to
a fixed number of requests per window, returning 429 once exceeded. An
API reachable from outside a single trusted process has to assume
someone, intentionally or not, will eventually send it more traffic than
it can handle. A rate limit turns that into a controlled, honest
rejection instead of the whole service slowing down or falling over for
every caller at once.

## Roll back fast

`deploy_notes.md`'s rollback plan is one paragraph for a reason: when
`GET /health` or the metrics clearly regress after a deploy, the fastest
safe action is redeploying the last known good image tag immediately,
not trying to patch the new version forward under pressure. A
containerized deployment with no external state to migrate makes
rolling back exactly as simple as rolling forward was, which is the
entire point of packaging the service this way in the first place.
