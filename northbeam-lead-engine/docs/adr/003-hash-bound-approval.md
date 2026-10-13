# ADR 003 — Hash-bound approval

## Status
Accepted

## Context
If a human approves text A and the system later edits or regenerates to text B, a stale approval must not authorize B.

## Decision
Approval stores `approved_hash = sha256(email|subject|body)`. Any edit clears approval. Send compares the recomputed hash to `approved_hash` (INV-2).

## Consequences
- Dashboard edits invalidate approval automatically.
- Telegram/Slack approve buttons bind to the exact content shown.
- Re-approval is required after every material change.
