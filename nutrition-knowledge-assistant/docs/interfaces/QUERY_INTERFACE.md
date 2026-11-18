# QUERY_INTERFACE

**Owner:** Agent 09 (API) + Agent 02 (contract)  
**Module:** `app.api` / `app.modules.query`  
**FR/AC:** FR-001, FR-011–012, FR-020–025, FR-029; AC-01–12, AC-40–42, AC-51

---

## Purpose

Public ask/inspect API for end-user Q&A and citation inspection.

---

## POST /api/v1/queries

### Input schema

| Field | Type | Required | Validation |
|-------|------|----------|------------|
| `question` | string | yes | 1…4000 chars after trim |
| `client_request_id` | string (UUID) | no | If set, echoed for tracing |
| `options` | object | no | See below |

`options`:

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `include_relevance_scores` | bool | no | default false |
| `requested_authorities` | string[] | no | e.g. `["WHO","USDA"]` |

### Output schema (`QueryResponse`)

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `query_id` | string (UUID) | yes | |
| `status` | enum | yes | `answered` \| `answered_with_conflicts` \| `insufficient_evidence` \| `refused_safety` \| `error` |
| `disclaimer` | string | yes | Global informational disclaimer |
| `heightened_disclaimer` | bool | yes | Pregnancy/children educational path |
| `answer_text` | string \| null | yes | null when not answered* |
| `claims` | Claim[] | yes | empty if not answered* |
| `citations` | Citation[] | yes | denormalized for UI; empty if none |
| `conflicts` | Conflict[] | yes | empty unless conflicts |
| `coverage` | Coverage | yes | |
| `safety` | SafetyDecisionPublic | yes | summary safe for client |
| `error` | ErrorObject \| null | yes | set when status=`error` |
| `relevance_scores` | RelevanceScore[] | no | only if requested; `score_type=retrieval_relevance` |

#### Claim

| Field | Type | Required |
|-------|------|----------|
| `claim_id` | string | yes |
| `text` | string | yes |
| `citation_ids` | string[] | yes |

#### Citation (see also EVIDENCE_INTERFACE)

| Field | Type | Required |
|-------|------|----------|
| `citation_id` | string | yes |
| `claim_id` | string | yes |
| `chunk_id` | string | yes |
| `document_version_id` | string | yes |
| `source_name` | string | yes |
| `document_title` | string | yes |
| `authority` | string \| null | no |
| `version_label` | string | yes |
| `is_outdated` | bool | yes |
| `excerpt` | string | yes | short preview |

#### Conflict

| Field | Type | Required |
|-------|------|----------|
| `topic` | string | yes |
| `sides` | ConflictSide[] | yes |

`ConflictSide`: `authority`, `summary`, `citation_ids[]`

#### Coverage

| Field | Type | Required |
|-------|------|----------|
| `requested_authorities` | string[] | yes |
| `found_authorities` | string[] | yes |
| `missing_authorities` | string[] | yes |

#### SafetyDecisionPublic

| Field | Type | Required |
|-------|------|----------|
| `decision` | `allow` \| `refuse` \| `allow_with_heightened_disclaimer` | yes |
| `categories` | string[] | yes | e.g. `["general_nutrition"]` |
| `message` | string \| null | yes | refusal/safe message |

#### ErrorObject

| Field | Type | Required |
|-------|------|----------|
| `code` | string | yes | e.g. `llm_unavailable` |
| `message` | string | yes | client-safe |
| `retriable` | bool | yes |

### Example — answered

```json
{
  "query_id": "11111111-1111-1111-1111-111111111111",
  "status": "answered",
  "disclaimer": "This assistant provides general educational information from curated sources. It is not medical advice, diagnosis, or treatment.",
  "heightened_disclaimer": false,
  "answer_text": "According to the cited dietary guidelines, vegetables are emphasized as part of healthy eating patterns.",
  "claims": [
    {
      "claim_id": "22222222-2222-2222-2222-222222222222",
      "text": "Vegetables are emphasized as part of healthy eating patterns.",
      "citation_ids": ["33333333-3333-3333-3333-333333333333"]
    }
  ],
  "citations": [
    {
      "citation_id": "33333333-3333-3333-3333-333333333333",
      "claim_id": "22222222-2222-2222-2222-222222222222",
      "chunk_id": "44444444-4444-4444-4444-444444444444",
      "document_version_id": "55555555-5555-5555-5555-555555555555",
      "source_name": "Demo Dietary Guidelines",
      "document_title": "Dietary Guidelines (Demo Fixture)",
      "authority": "USDA",
      "version_label": "2020-2025-demo",
      "is_outdated": false,
      "excerpt": "A healthy dietary pattern includes vegetables of all types..."
    }
  ],
  "conflicts": [],
  "coverage": {
    "requested_authorities": [],
    "found_authorities": ["USDA"],
    "missing_authorities": []
  },
  "safety": {
    "decision": "allow",
    "categories": ["dietary_guidelines"],
    "message": null
  },
  "error": null
}
```

### Error conditions

| HTTP | When |
|------|------|
| 422 | Validation failure |
| 200 + `status=error` | Downstream provider/DB failure after accept (preferred for domain errors) |
| 401/403 | Only on operator routes |
| 429 | Rate limited |

Secrets must never appear in `error.message`.

---

## GET /api/v1/chunks/{chunk_id}

### Output

| Field | Type | Required |
|-------|------|----------|
| `chunk_id` | string | yes |
| `text` | string | yes |
| `document_version_id` | string | yes |
| `document_title` | string | yes |
| `source_name` | string | yes |
| `authority` | string \| null | no |
| `version_label` | string | yes |
| `is_outdated` | bool | yes |
| `canonical_url` | string \| null | no |

404 if missing. FR-012, AC-03–04.

---

## POST /api/v1/feedback (Should)

| Field | Type | Required |
|-------|------|----------|
| `query_id` | string | yes |
| `rating` | `helpful` \| `not_helpful` | yes |
| `reason_code` | string | no |

---

## Dependencies

- SAFETY_INTERFACE, RETRIEVAL_INTERFACE, GENERATION_INTERFACE, EVIDENCE_INTERFACE  
- No circular import: API orchestrates one-way calls into modules.
