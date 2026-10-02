# ADR 001: Consent is checked before any processing

**Status:** accepted

## Context
Recording a call is not the same as having the right to process it. Consent may arrive as metadata from
the telephony system, or only as a spoken announcement at the start of the call.

## Decision
- `consent_recorded=false`: the call is blocked immediately. No ASR, no model call, audio is purged.
- `consent_recorded=true`: proceed.
- `consent_recorded=null`: run a **probe**, i.e. the local ASR on the first 60 seconds only, and look for an
  announcement in agent or unlabeled speech (a customer saying it does not count). The probe transcript is
  discarded. No announcement means the call is blocked and the audio purged.

## Consequences
- The rule "no consent, no processing" has one exception that must be named: the short local probe. It is
  the price of supporting recordings without metadata, and it never reaches a model or the database.
- `INV-1` tests assert the ASR is called with `max_seconds=60` only, and the model is not called at all.
- The phrase list and the window live in `policies/default.yml`.
