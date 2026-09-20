# Performance and load testing

The API exports Prometheus metrics at `/metrics` for request volume and latency,
retrieval latency, generation latency, ingestion outcomes, cache outcomes, and
ingestion queue depth. Every response includes an `X-Request-ID`, and application
logs are structured JSON.

Search responses use a short, owner-scoped Redis cache. Embeddings are produced
in batches, uploads use content hashes to prevent duplicate processing, lists are
paginated, and question context is capped at 20 chunks.

## Reproducible load profile

1. Start the Docker Compose stack.
2. Register, upload seed documents, and wait until they are ready.
3. Run `python backend/tests/load/search_load.py TOKEN`.
4. Capture mean and p95 latency, failure rate, API CPU/memory, PostgreSQL query
   latency, Redis queue depth, and worker throughput.

The harness issues 100 concurrent searches. For the 1,000-document / 10,000-chunk
profile, load fixtures before the run and use at least two workers. Results are
environment-dependent and should be recorded with hardware and container limits;
the repository does not publish invented benchmark numbers.
