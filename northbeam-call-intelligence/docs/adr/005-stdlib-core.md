# ADR 005: A framework-free core, SQLite and local blobs

**Status:** accepted

## Context
The rules that matter (consent, redaction, grounding, policy, approvals, erasure) should be testable in
milliseconds without a web server or a database container.

## Decision
- `app/service.py` and `app/pipeline/*` use dataclasses and the standard library (plus PyYAML).
  FastAPI and Pydantic appear only in `app/main.py`, where they validate HTTP input.
- Model output is validated by a hand-written validator (`insights.py`), because the interesting checks
  (quote in segment, number in quote) are not expressible as a schema anyway.
- State lives in SQLite. `audit` is append-only (triggers) and hash-chained. Audio lives on the local
  filesystem behind a four-method blob interface.
- PostgreSQL in `docker-compose.yml` serves n8n's own state, not this service.

## Consequences
- The whole invariant suite runs in about a second.
- Moving to PostgreSQL and S3/MinIO means implementing `Store` and the blob interface again.
  This is named in the README as the production boundary.
- One connection per operation is fine for a demo and wrong for high throughput.
