# Architecture and flow

```mermaid
flowchart TD
  A[POST /lead-capture] --> B[Normalize Input]
  B --> C[Validate Required Fields]
  C --> D[Validate Email]
  D --> E{Is Valid?}
  E -- no --> F[HTTP 400]
  E -- yes --> G[Generate Lead ID]
  G --> H[Generate Idempotency Key]
  H --> I[Google Sheets: look up key]
  I --> J{Duplicate?}
  J -- yes --> K[Log duplicate]
  K --> L[HTTP 409]
  J -- no --> M[Append lead to Leads]
  M --> N[Log lead_saved]
  N --> O[OpenRouter: structured score]
  O --> P[Parse and validate AI output]
  P --> Q[Update AI fields in Leads]
  Q --> R{score >= 70?}
  R -- yes --> S[High route]
  R -- no --> T{score >= 30?}
  T -- yes --> U[Medium route]
  T -- no --> V[Low route]
  S --> W[Update route; Telegram; email]
  U --> X[Update route; Telegram; email]
  V --> Y[Update route; email]
  W --> Z[Webhook response]
  X --> Z
  Y --> Z
```

## Data contracts

The request accepts `name`, `email`, `company`, `employees`, `service`, and `message`. `name`, `email`, `company`, and `message` are required by the workflow validation. Input email is trimmed and converted to lowercase.

The OpenRouter request asks for a structured object with:

- `lead_score`: numeric score from 0 to 100
- `category`: `high_value`, `medium_value`, or `low_value`
- `priority`: `urgent`, `high`, `normal`, or `low`
- `reason`: qualification rationale
- `summary`: short summary
- `confidence`: numeric confidence from 0 to 1

The parse node validates score, allowed category/priority values, confidence range, and the presence of reason and summary before writing results to the CRM.
