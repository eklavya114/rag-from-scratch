# Deploy Notes

These notes are plain text, not executed anywhere in this project. They
describe how the Dockerfile in this folder would actually be built, run,
configured, and rolled back in a real deployment.

## Building and running the image locally

From the repository root (so both `day-23-deployment/` and
`day-22-production-rag/` are in the build context):

    docker build -f day-23-deployment/Dockerfile -t rag-api:latest .

Running the built image, publishing container port 8000 to host port
8000:

    docker run -p 8000:8000 -e RAG_API_KEY=a-real-secret-key rag-api:latest

After that, the service would be reachable at `http://localhost:8000`,
the same endpoints `api_server.py` defines: `POST /query`, `GET
/health`, `GET /metrics`.

## Environment variables to set

- `RAG_API_KEY`: the real API key clients must send in the `X-API-Key`
  header. Never baked into the image, always passed in at run time.
- `RAG_API_PORT`: which port the server listens on inside the container
  (defaults to 8000, matching the Dockerfile's `EXPOSE`).
- `LOG_LEVEL`: in a real deployment, controls how verbose the service's
  logs are (for example `INFO` in production, `DEBUG` while actively
  investigating an issue). Not read by any code in this toy project, but
  exactly the kind of setting a real deployment manages this way, rather
  than hardcoding a log level into source.

## What to check after deploying

- `GET /health`: confirm it returns `healthy` (HTTP 200), not `degraded`
  or `unhealthy` (HTTP 503).
- Error rate from `GET /metrics`: should sit near zero immediately after
  a deploy. A nonzero rate right after rollout, before any real traffic
  pattern has had time to build up, often points at a bad deploy rather
  than an unrelated issue.
- p95 latency from `GET /metrics`: compare against the number from
  before the deploy. A new version that is meaningfully slower at p95,
  even if it is correct, is still a regression worth investigating.

## Rollback plan

If `GET /health` reports `unhealthy` after a deploy, or the error rate or
p95 latency clearly regress compared to the previous version's numbers,
the fastest safe action is to redeploy the last known good image tag
immediately rather than trying to patch the new version forward under
pressure. Because the Dockerfile here builds a clean, self-contained
image with no external state to migrate or reconcile, rolling back is
just running the previous image tag again, the same way rolling forward
was running the new one, which is exactly the property a containerized
deployment is meant to provide.
