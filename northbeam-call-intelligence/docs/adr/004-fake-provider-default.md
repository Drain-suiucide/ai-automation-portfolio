# ADR 004: A deterministic fake provider is the default

**Status:** accepted

## Context
A portfolio demo must run without keys, cost nothing and give the same answer every time, but it should
still exercise the parts that matter: validation, policies, approvals.

## Decision
`ASRProvider` and `LLMProvider` are interfaces. Defaults are `fixture` (replays prepared transcripts) and
`fake` (a rule-based extractor). Real providers (`faster_whisper`, `anthropic`, `openai`, `ollama`,
`gateway`) are opt-in through environment variables and use only the standard library for HTTP.
The fake extractor sits behind exactly the same validator and policy engine as a real model.

## Consequences
- CI is fast and deterministic; quality numbers measure the pipeline, not a model.
- Real-model behavior (paraphrased quotes, refusals, latency, cost) must be evaluated separately.
- The `gateway` provider assumes an OpenAI-compatible endpoint.
