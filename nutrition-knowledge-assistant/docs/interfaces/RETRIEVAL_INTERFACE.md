# RETRIEVAL_INTERFACE

**Owner:** Agent 06  
**Module:** `app.modules.retrieval`  
**FR/AC:** FR-003, FR-019, FR-029; AC-08, AC-12, AC-43

---

## Purpose

Embed a query and return ranked chunk candidates from pgvector with metadata needed for evidence selection and citation.

---

## Input: `RetrievalRequest`

| Field | Type | Required | Validation |
|-------|------|----------|------------|
| `query_id` | UUID | yes | |
| `question_text` | string | yes | non-empty |
| `requested_authorities` | string[] | no | |
| `top_k` | int | no | default 12; 1…50 |
| `include_inactive` | bool | no | default false (ops only) |

---

## Output: `RetrievalResponse`

| Field | Type | Required |
|-------|------|----------|
| `query_id` | UUID | yes |
| `embedding_model_id` | string | yes |
| `results` | RetrievalHit[] | yes |
| `error` | ErrorObject \| null | yes |

### RetrievalHit

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `chunk_id` | UUID | yes | |
| `document_version_id` | UUID | yes | |
| `document_id` | UUID | yes | |
| `source_id` | UUID | yes | |
| `authority` | string \| null | no | |
| `is_outdated` | bool | yes | |
| `is_active` | bool | yes | |
| `relevance_score` | number | yes | higher = more similar (normalize in adapter) |
| `score_type` | string | yes | always `"retrieval_relevance"` |
| `rank` | int | yes | 1-based |
| `text` | string | yes | chunk text |
| `document_title` | string | yes | |
| `version_label` | string | yes | |

**Normative:** `relevance_score` must not be documented or labeled as probability of factual correctness.

---

## Example

```json
{
  "query_id": "11111111-1111-1111-1111-111111111111",
  "embedding_model_id": "text-embedding-3-small",
  "results": [
    {
      "chunk_id": "44444444-4444-4444-4444-444444444444",
      "document_version_id": "55555555-5555-5555-5555-555555555555",
      "document_id": "66666666-6666-6666-6666-666666666666",
      "source_id": "77777777-7777-7777-7777-777777777777",
      "authority": "USDA",
      "is_outdated": false,
      "is_active": true,
      "relevance_score": 0.81,
      "score_type": "retrieval_relevance",
      "rank": 1,
      "text": "A healthy dietary pattern includes vegetables of all types...",
      "document_title": "Dietary Guidelines (Demo Fixture)",
      "version_label": "2020-2025-demo"
    }
  ],
  "error": null
}
```

---

## Error conditions

| Code | Meaning |
|------|---------|
| `embedding_unavailable` | OpenAI embed failure → pipeline `error` |
| `vector_store_unavailable` | DB/pgvector failure → pipeline `error` |

---

## Dependencies

- Embeddings adapter (OpenAI)  
- Vector storage (Postgres)  
- Document metadata tables  

Does **not** depend on Generation or Safety (Safety runs before/after at orchestration layer).
