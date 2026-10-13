# ADR 002 — Send-time guards

## Status
Accepted

## Context
Approving a draft hours before SMTP send creates a TOCTOU gap: suppression lists, country policy, and caps can change after approval.

## Decision
All send guards run again in `check_send_guards` at the moment of send (`POST /v1/send/batch`), not only when the draft is created. Block reasons are audited.

## Consequences
- Late unsubscribe wins (INV-3).
- Approval alone is never sufficient (INV-1).
- Slightly more compute per send; acceptable for SDR volumes.
