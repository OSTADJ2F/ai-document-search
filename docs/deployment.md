# Deployment

## Render Blueprint target

The root `render.yaml` defines a web frontend, API, background worker, PostgreSQL,
and Render Key Value. The API container runs Alembic migrations before serving.
Uploaded objects use any S3-compatible service so the API and worker share the
same durable source files.

1. Push the repository to GitHub.
2. In Render, create a Blueprint from the repository.
3. Supply the prompted `NEXT_PUBLIC_API_URL` and `CORS_ORIGINS` values using the
   final public service URLs.
4. Supply one S3-compatible bucket, endpoint, region, access key, and secret to
   both the API and worker prompts.
5. Deploy and verify `/health`, `/ready`, `/metrics`, registration, upload, ready status,
   search, and citations.

Do not use local container storage in a multi-service cloud deployment: API and
worker filesystems are not a shared object store. Rotate credentials through the
Render dashboard and never commit them.

## Generic container platform

Build `backend/Dockerfile` for the API and worker, and `frontend/Dockerfile` for
the web application. Provide PostgreSQL with pgvector, Redis-compatible storage,
and a shared S3-compatible object store. Run the worker image with:

```bash
rq worker ingestion --url "$REDIS_URL"
```

Run `alembic upgrade head` as a release step before shifting traffic. The API is
ready when `/ready` returns HTTP 200 with both dependencies reported as `ok`.
