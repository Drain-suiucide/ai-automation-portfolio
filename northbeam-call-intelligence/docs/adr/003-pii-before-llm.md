# ADR 003: Personal data is replaced before it can be sent, stored or logged

**Status:** accepted

## Context
Transcripts contain e-mail addresses, phone numbers and card numbers that customers read aloud.

## Decision
Redaction runs right after transcription, before the first database write, log line or model call.
It detects e-mail (written and spoken), IBAN, cards (Luhn-checked), phone numbers, long digit runs and
digits dictated word by word. Tokens such as `[EMAIL_1]` replace the values; the token map exists only in
memory for one call and is never persisted. The raw text therefore never exists in storage.
Free text returned by the model is redacted again as defence in depth.

## Consequences
- Follow-up drafts contain tokens (`body_redacted`); a person fills in real contact data.
- Names are not detected. A NER model (for example Presidio) is the documented production seam.
- `INV-2` uses canary values and searches prompts, the whole database dump and log lines.
