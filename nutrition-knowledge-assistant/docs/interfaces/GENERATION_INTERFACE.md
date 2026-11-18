# GENERATION_INTERFACE

**Owner:** Agent 07  
**Module:** `app.modules.generation` + `app.modules.citations`  
**FR/AC:** FR-004–010, FR-014, FR-023; AC-02, AC-05–07, AC-10, AC-41

---

## Purpose

Assemble untrusted evidence context, generate a structured draft answer constrained to evidence, and validate citation identifiers before response assembly.

---

## A. Context assembly — `BuildContextRequest`

| Field | Type | Required |
|-------|------|----------|
| `query_id` | UUID | yes |
| `question_text` | string | yes |
| `evidence` | EvidenceItem[] | yes |
| `conflicts` | ConflictReport \| null | yes |
| `heightened_disclaimer` | bool | yes |
| `safety_categories` | string[] | yes |

### `GenerationContext` (output)

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `system_instructions` | string | yes | safety + grounding rules; not from KB |
| `evidence_blocks` | EvidenceBlock[] | yes | clearly delimited DATA |
| `allowed_chunk_ids` | UUID[] | yes | hard allow-list for cites |
| `conflict_instructions` | string \| null | no | |

`EvidenceBlock`: `{ chunk_id, document_version_id, authority, is_outdated, text }`

Normative: chunk text is **data**, never merged as system instructions (FR-013, AC-30).

---

## B. Generate — `GenerateRequest` / `GenerateResponse`

### Request

| Field | Type | Required |
|-------|------|----------|
| `query_id` | UUID | yes |
| `context` | GenerationContext | yes |
| `chat_model_id` | string | yes | from config |

### Response

| Field | Type | Required |
|-------|------|----------|
| `draft_status` | enum | yes | `draft_answer` \| `abstain_insufficient` \| `provider_error` |
| `answer_text` | string \| null | yes | |
| `claims` | DraftClaim[] | yes | |
| `token_usage` | {`prompt_tokens`: int, `completion_tokens`: int} \| null | yes | |
| `raw_error_code` | string \| null | yes | never includes secrets |

### DraftClaim

| Field | Type | Required |
|-------|------|----------|
| `ordinal` | int | yes |
| `text` | string | yes |
| `cited_chunk_ids` | UUID[] | yes | must be subset of allow-list after validation |

### Example draft

```json
{
  "draft_status": "draft_answer",
  "answer_text": "Vegetables are emphasized in the cited guidelines as part of a healthy dietary pattern.",
  "claims": [
    {
      "ordinal": 1,
      "text": "Vegetables are emphasized as part of a healthy dietary pattern.",
      "cited_chunk_ids": ["44444444-4444-4444-4444-444444444444"]
    }
  ],
  "token_usage": {"prompt_tokens": 1200, "completion_tokens": 180},
  "raw_error_code": null
}
```

---

## C. Citation validation — `ValidateCitationsRequest`

| Field | Type | Required |
|-------|------|----------|
| `query_id` | UUID | yes |
| `claims` | DraftClaim[] | yes |
| `allowed_chunk_ids` | UUID[] | yes |
| `evidence` | EvidenceItem[] | yes |

### `ValidateCitationsResponse`

| Field | Type | Required |
|-------|------|----------|
| `passed` | bool | yes |
| `validated_claims` | ValidatedClaim[] | yes |
| `citations` | Citation[] | yes | see EVIDENCE_INTERFACE |
| `rejected_chunk_ids` | UUID[] | yes | |
| `failure_reason` | string \| null | yes | e.g. `unknown_chunk_id` |

**Hard gate rules:**

1. Every cited chunk_id ∈ `allowed_chunk_ids`.  
2. Chunk exists in DB.  
3. `document_version_id` on citation matches chunk’s version.  
4. No citations invented outside evidence.

On failure: orchestrator may retry generate once with stricter allow-list reminder; then `insufficient_evidence` if still failing (unless DB error → `error`).

**Citation support (semantic entailment) is NOT part of this interface’s pass/fail in MVP.**

---

## Error conditions

| draft_status / code | Pipeline outcome |
|---------------------|------------------|
| `provider_error` | `error` |
| `abstain_insufficient` | `insufficient_evidence` |
| validation fail after retry | `insufficient_evidence` |

---

## Dependencies

- EVIDENCE_INTERFACE  
- OpenAI chat adapter  
- Chunk repository for validation  

Must not depend on Safety module internals (receives safety flags from orchestrator).
