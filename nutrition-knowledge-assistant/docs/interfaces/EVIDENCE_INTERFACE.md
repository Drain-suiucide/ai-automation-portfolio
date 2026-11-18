# EVIDENCE_INTERFACE

**Owner:** Agent 06/07 (filter + conflict) / Agent 02 contract  
**Module:** `app.modules.evidence`  
**FR/AC:** FR-007, FR-014–015, FR-026; AC-08, AC-10–11, AC-43

---

## Purpose

Turn retrieval hits into the evidence set used for generation, detect conflicts, and shape citation metadata objects shared with the Query API.

---

## Input: `EvidenceBuildRequest`

| Field | Type | Required |
|-------|------|----------|
| `query_id` | UUID | yes |
| `retrieval_hits` | RetrievalHit[] | yes |
| `requested_authorities` | string[] | no |
| `max_evidence` | int | no | default 6 |
| `min_relevance_score` | number \| null | no | null = disabled until calibrated |

---

## Output: `EvidenceBuildResponse`

| Field | Type | Required |
|-------|------|----------|
| `query_id` | UUID | yes |
| `evidence` | EvidenceItem[] | yes |
| `conflicts` | ConflictReport \| null | yes |
| `coverage` | Coverage | yes |
| `sufficient` | bool | yes | false → orchestrator returns `insufficient_evidence` |
| `sufficiency_reason` | string \| null | yes | e.g. `empty_after_filter` |

### EvidenceItem

| Field | Type | Required |
|-------|------|----------|
| `evidence_id` | string | yes | may equal `chunk_id` in MVP |
| `chunk_id` | UUID | yes |
| `document_version_id` | UUID | yes |
| `authority` | string \| null | no |
| `is_outdated` | bool | yes |
| `relevance_score` | number | yes |
| `score_type` | `"retrieval_relevance"` | yes |
| `text` | string | yes |
| `document_title` | string | yes |
| `source_name` | string | yes |
| `version_label` | string | yes |

### ConflictReport

| Field | Type | Required |
|-------|------|----------|
| `detected` | bool | yes |
| `topic` | string | yes |
| `sides` | { `authority`: string, `evidence_ids`: string[] }[] | yes |

Heuristic MVP: `detected=true` when ≥2 different non-null authorities appear in selected evidence **and** query plan is compare-like **or** opposing stance tags exist. Generation still instructed to avoid false consensus even if heuristic misses.

---

## Citation object (shared)

Used in QueryResponse and generation validation.

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `citation_id` | UUID | yes | |
| `claim_id` | UUID | yes | |
| `chunk_id` | UUID | yes | must exist |
| `document_version_id` | UUID | yes | must own chunk |
| `source_name` | string | yes | |
| `document_title` | string | yes | |
| `authority` | string \| null | no | |
| `version_label` | string | yes | |
| `is_outdated` | bool | yes | |
| `excerpt` | string | yes | |

**Citation validity (runtime):** chunk exists ∧ version matches ∧ chunk was in evidence set for this query.  
**Citation support:** not asserted here; evaluation-only in MVP.

---

## Example

```json
{
  "query_id": "11111111-1111-1111-1111-111111111111",
  "evidence": [
    {
      "evidence_id": "44444444-4444-4444-4444-444444444444",
      "chunk_id": "44444444-4444-4444-4444-444444444444",
      "document_version_id": "55555555-5555-5555-5555-555555555555",
      "authority": "USDA",
      "is_outdated": false,
      "relevance_score": 0.81,
      "score_type": "retrieval_relevance",
      "text": "A healthy dietary pattern includes vegetables...",
      "document_title": "Dietary Guidelines (Demo Fixture)",
      "source_name": "Demo Dietary Guidelines",
      "version_label": "2020-2025-demo"
    }
  ],
  "conflicts": null,
  "coverage": {
    "requested_authorities": ["WHO", "USDA"],
    "found_authorities": ["USDA"],
    "missing_authorities": ["WHO"]
  },
  "sufficient": true,
  "sufficiency_reason": null
}
```

---

## Error conditions

- Empty evidence → `sufficient=false` (not an exception).  
- Downstream DB metadata miss → orchestrator `error`.

---

## Dependencies

- RETRIEVAL_INTERFACE (inputs)  
- DATA_MODEL DocumentVersion/Chunk  

Does not call Generation.
