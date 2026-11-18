# SAFETY_INTERFACE

**Owner:** Agent 08  
**Module:** `app.modules.safety`  
**Policy:** `docs/SAFETY_POLICY.md`  
**FR/AC:** FR-002, FR-008, FR-013, FR-021, FR-033–034; AC-20–30, AC-25

---

## Purpose

Evaluate user intent (pre) and model output (post) against the Safety Policy. Retrieved chunk text must never disable this module.

---

## Category codes (stable strings)

| Code | Category |
|------|----------|
| `general_nutrition` | 1 |
| `scientific_nutrition` | 2 |
| `dietary_guidelines` | 3 |
| `personalized_nutrition` | 4 |
| `disease_specific_nutrition` | 5 |
| `supplements` | 6 |
| `medication_interactions` | 7 |
| `eating_disorders` | 8 |
| `extreme_weight_loss` | 9 |
| `pregnancy` | 10 |
| `children` | 11 |
| `insufficient_evidence` | 12 (process; rarely from classifier) |
| `emergency` | 13 |

---

## Input: `SafetyCheckRequest`

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `query_id` | UUID | yes | |
| `phase` | `pre` \| `post` | yes | |
| `question_text` | string | yes | |
| `draft_answer_text` | string \| null | yes | required for `post` |
| `draft_claims` | {text: string}[] \| null | no | post |
| `evidence_texts` | string[] \| null | no | optional; treated as untrusted DATA if scanned for injection patterns |

---

## Output: `SafetyCheckResponse` / `SafetyDecision`

| Field | Type | Required |
|-------|------|----------|
| `decision` | `allow` \| `refuse` \| `allow_with_heightened_disclaimer` | yes |
| `risk_level` | `L0` \| `L1` \| `L2` \| `L3` | yes |
| `categories` | string[] | yes | codes above |
| `rationale_code` | string | yes | stable machine code |
| `user_message` | string \| null | yes | safe refusal/redirect text |
| `emergency_redirect` | bool | yes | true for Cat 13 |
| `block_generation` | bool | yes | true when pre-refuse |
| `discard_draft` | bool | yes | true when post-refuse |

### Ambiguity policy

- Ambiguous allow vs refuse → `refuse` (fail closed), except clear educational Cat 1–3 without personalization markers (FR-034).  
- Module exception → orchestrator emits `error` (does not skip safety).

---

## Example — pre refuse (diagnosis)

```json
{
  "decision": "refuse",
  "risk_level": "L3",
  "categories": ["disease_specific_nutrition"],
  "rationale_code": "diagnosis_or_treatment_request",
  "user_message": "I can't provide diagnoses or treatment plans. Please consult a qualified healthcare professional. This tool only offers general educational nutrition information from curated sources.",
  "emergency_redirect": false,
  "block_generation": true,
  "discard_draft": false
}
```

### Example — post refuse (injection persona)

```json
{
  "decision": "refuse",
  "risk_level": "L3",
  "categories": ["medication_interactions"],
  "rationale_code": "output_claims_clinical_authority",
  "user_message": "I can't provide medical advice or act as a clinician. For emergencies, contact local emergency services.",
  "emergency_redirect": false,
  "block_generation": false,
  "discard_draft": true
}
```

---

## Error conditions

| Code | Handling |
|------|----------|
| `safety_engine_unavailable` | Pipeline `error` |
| invalid phase/payload | 422 at API or ValueError internally |

---

## Dependencies

- Safety Policy document (rules tables)  
- Optional LLM assist classifier — must not be sole gate without rules; rules-first MVP  

Does **not** call Retrieval or Generation. Orchestrator calls Safety.
