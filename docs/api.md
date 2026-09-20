# API reference

Interactive OpenAPI documentation is available at `/docs` and the schema at
`/openapi.json`.

| Method | Path | Authentication | Purpose |
| --- | --- | --- | --- |
| `GET` | `/health` | No | Database and Redis readiness |
| `GET` | `/ready` | No | 200 only when database and Redis are ready |
| `GET` | `/metrics` | No | Prometheus metrics |
| `POST` | `/auth/register` | No | Register and receive a bearer token |
| `POST` | `/auth/login` | No | Log in and receive a bearer token |
| `GET` | `/auth/me` | Bearer | Current account |
| `POST` | `/auth/logout` | Bearer | Audit logout; client discards token |
| `POST` | `/documents` | Bearer | Multipart upload in field `file` |
| `GET` | `/documents` | Bearer | Paginated owned documents |
| `GET` | `/documents/{id}` | Bearer | Owned document metadata/status |
| `DELETE` | `/documents/{id}` | Bearer | Delete stored source and hide record |
| `POST` | `/search` | Bearer | Hybrid passage retrieval |
| `POST` | `/ask` | Bearer | Grounded answer and citations |

Search body:

```json
{
  "query": "What were the main risks?",
  "document_ids": [],
  "file_type": "pdf",
  "uploaded_after": "2026-01-01T00:00:00Z",
  "limit": 8
}
```

Ask response:

```json
{
  "answer": "Supply chain disruption is the primary operational risk.",
  "citations": [
    {
      "document_id": "00000000-0000-0000-0000-000000000000",
      "document_name": "annual-report.pdf",
      "page": 14,
      "section": null,
      "snippet": "Supply chain disruption is the primary operational risk."
    }
  ],
  "retrieved_chunks": 5,
  "supported": true
}
```

Validation errors use FastAPI's structured 422 response. Authentication errors
are 401, foreign/missing resources are 404, duplicates are 409, oversized uploads
are 413, invalid file content is 415, rate limits are 429, and generation-provider
failures are sanitized 503 responses.
