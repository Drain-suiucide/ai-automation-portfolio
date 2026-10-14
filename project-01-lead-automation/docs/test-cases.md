# Test cases

Use a test webhook and a mailbox/Telegram chat that you control. The workflow may send real notifications once credentials are configured.

| ID | Scenario | Expected result |
|---|---|---|
| TC-01 | Missing required field | `400` with status `invalid`; no CRM lead should be created |
| TC-02 | Invalid email format | `400` with status `invalid` |
| TC-03 | New unique lead | One row appended to `Leads`; qualification fields are added after AI returns |
| TC-04 | High score (>=70) | `route=high_value`, assigned to sales, Telegram and email steps execute |
| TC-05 | Medium score (30–69) | `route=medium_value`, assigned to sales, Telegram and email steps execute |
| TC-06 | Low score (<30) | `route=low_value`, assigned to nurturing, email step executes |
| TC-07 | Exact duplicate submission | First request creates a lead; second returns `409` and logs duplicate event |
| TC-08 | OpenRouter failure or invalid AI JSON | Execution fails at qualification/parsing; inspect execution log and consider adding error handling |
| TC-09 | Google Sheets permission revoked | Google Sheets node fails; workflow error should be visible in execution details |

## Manual duplicate test

The idempotency key is derived deterministically from normalized `email`, `company`, and `message`. Send the same three values twice; do not change capitalization or whitespace unless testing normalization. The second request should be treated as a duplicate.

## Route boundaries

The IF nodes use numeric thresholds: High if `lead_score >= 70`; otherwise Medium if `lead_score >= 30`; otherwise Low. The LLM-generated category is also validated, but the route path is selected using `lead_score`.
