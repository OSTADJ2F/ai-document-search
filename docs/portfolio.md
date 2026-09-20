# Portfolio case study

## Product

Locus turns a private document library into a verifiable question-answering
workspace. It is designed around a simple promise: an answer is useful only when
the reader can inspect the evidence behind it.

The primary demo flow is:

1. Create an account and log in.
2. Upload `docs/demo-risk-report.md`.
3. Watch the document move through uploaded, processing, and ready states.
4. Ask, “What is the primary operational risk?”
5. Expand the returned citation and inspect the exact source passage.
6. Ask an unsupported question and observe the honest, uncited fallback.

## Engineering decisions

- Retrieval combines pgvector cosine similarity with PostgreSQL full-text rank,
  preserving the strengths of semantic and exact-term search.
- Ingestion is isolated in retryable RQ workers so extraction and embedding never
  block API requests.
- Local deterministic providers keep the project runnable without paid services;
  provider interfaces preserve a clean path to managed models.
- UUID storage keys, content-aware validation, owner predicates, owner-scoped
  cache keys, and citation validation make trust boundaries explicit.
- S3-compatible storage lets independently scaled API and worker services share
  immutable sources without relying on container filesystems.
- The quality suite treats retrieval, citation correctness, unsupported answers,
  prompt injection, and cross-user access as measurable regression behavior.

## Verification snapshot

- Backend: 23 Pytest tests passing, Ruff lint and formatting passing, 88% line
  coverage in the final measured run
- Frontend: ESLint, Vitest, TypeScript/Next.js production build, and two
  Playwright Chromium smoke tests passing
- Supply chain: `pip check` clean and `npm audit` reports zero vulnerabilities
- CI: backend and frontend jobs passed on the production-documentation milestone
- Deployment: Compose and Render YAML parse successfully; Alembic reports a
  single `0001_initial` head

Docker Desktop is installed per-user on the development host and its engine and
Compose plugin were verified through the installation's absolute CLI path. That
CLI directory was not present in the Codex PowerShell session's `PATH`, which
caused the initial command lookup to report a false negative.

## Milestone ledger

| Commit | Milestone |
| --- | --- |
| `28c6770` | Repository initialized and pushed |
| `869c520` | FastAPI, Next.js, services, and CI foundation |
| `c1942b0` | Authentication and protected routes |
| `fd17313` | Document upload and ownership management |
| `3e19e25` | Asynchronous extraction/chunking/embedding pipeline |
| `c5d0821` | Hybrid semantic and keyword retrieval |
| `5f2922a` | Grounded answers and inspectable citations |
| `e657aca` | Retrieval and answer-quality evaluation |
| `da42a43` | Security and isolation hardening |
| `db23d61` | Metrics, caching, and load-test harness |
| `89a213f` | Production migrations, deployment, docs, and screenshot |
| `bbcf967` | Current GitHub Actions runtimes |

## Resume bullet

> Built a production-oriented AI document search platform with FastAPI, Next.js,
> PostgreSQL/pgvector, Redis, and Docker; implemented asynchronous ingestion,
> hybrid semantic search, grounded question answering, citation tracking,
> retryable workers, per-user authorization, and automated retrieval-quality
> evaluation.
