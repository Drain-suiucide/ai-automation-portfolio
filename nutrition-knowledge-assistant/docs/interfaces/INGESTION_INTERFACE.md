# INGESTION_INTERFACE

**Owner:** Agent 05 (+ Agent 03 metadata, Agent 04 persistence)
**Module:** `app.modules.ingestion` / `app.modules.sources`
**FR/AC:** FR-016–019, FR-026, FR-028, FR-031; AC-43–44

---

## Purpose

Register sources and ingest approved document versions into versioned chunks + embeddings with idempotency and provenance.

---

## A. Register source — `POST /api/v1/sources` (operator)

### Input

| Field | Type | Required | Validation |
|-------|------|----------|------------|
| `name` | string | yes | |
| `authority` | string \| null | no | |
| `jurisdiction` | string \| null | no | |
| `canonical_url` | string \| null | no | URI |
| `license_spdx` | string \| null | no | |
| `license_status` | enum | yes | `approved_for_kb` \| `forbidden` \| `unknown` |
| `license_notes` | string \| null | no | |

Rejects ingest later if `license_status != approved_for_kb`.

### Output

`{ "source_id": UUID, ...echo fields }`

---

## B. Start ingestion job — `POST /api/v1/ingestion/jobs` (operator)

### Input

| Field | Type | Required | Validation |
|-------|------|----------|------------|
| `source_id` | UUID | yes | must exist + approved license |
| `document_title` | string | yes | |
| `version_label` | string | yes | |
| `doc_type` | enum | yes | `guideline` \| `publication` \| `fixture` |
| `input_uri` | string | yes | path under `data/` or allowed URI scheme |
| `version_url` | string \| null | no | |
| `published_at` | string \| null | no | ISO date |
| `is_outdated` | bool | no | default false |
| `population_tags` | string[] | no | |
| `approval_status` | enum | no | default `approved` for operator-submitted MVP |

Auth: `Authorization: Bearer <OPERATOR_API_TOKEN>` (D-014).

### Output: `IngestionJob`

| Field | Type | Required |
|-------|------|----------|
| `ingestion_job_id` | UUID | yes |
| `status` | `queued` \| `running` \| `succeeded` \| `failed` | yes |
| `stage` | string \| null | yes | `fetch`\|`extract`\|`normalize`\|`validate`\|`version`\|`chunk`\|`embed`\|`store` |
| `document_version_id` | UUID \| null | yes | |
| `content_hash` | string \| null | yes | |
| `chunk_count` | int \| null | yes | |
| `error` | ErrorObject \| null | yes | sanitized |

### Example

```json
{
  "ingestion_job_id": "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
  "status": "succeeded",
  "stage": "store",
  "document_version_id": "55555555-5555-5555-5555-555555555555",
  "content_hash": "sha256:0123456789abcdef",
  "chunk_count": 42,
  "error": null
}
```

---

## C. Pipeline semantics (module API)

`run_ingestion(job_id) -> IngestionJob`

| Stage | Behavior |
|-------|----------|
| fetch/load | Read bytes from `input_uri` |
| extract | PDF/HTML/Markdown → text (format support phased) |
| normalize | Unicode, whitespace; compute `content_hash` |
| validate | License + non-empty + size limits |
| version | Insert DocumentVersion; idempotent on hash |
| chunk | Split to chunks with ordinals |
| embed | OpenAI embeddings batch |
| store | Transactional persist chunks+vectors; mark job succeeded |

**Idempotency:** same `(document_id, content_hash)` → succeed no-op, return existing version.
**Partial failure:** do not activate half-written version; prior active version untouched.
**Deactivate:** `PATCH /api/v1/document-versions/{id}` with `{ "is_active": false }` (Could/Should).

---

## D. List documents — `GET /api/v1/documents` (operator, Should)

Returns documents with versions: ids, titles, version_label, is_outdated, is_active, chunk_count.

---

## Error conditions

| Code | Meaning |
|------|---------|
| `license_not_approved` | Block ingest |
| `duplicate_version` | Idempotent success or conflict on label mismatch |
| `extract_failed` | Unsupported/corrupt file |
| `embed_failed` | Provider error |

---

## Dependencies

- DATA_MODEL entities
- OpenAI embeddings
- Postgres

Does not depend on Query/Generation. Safety of *content quality* is editorial (Agent 03), not Safety Pre-check.
