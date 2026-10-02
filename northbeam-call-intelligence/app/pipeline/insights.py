"""Validates LLM output against the transcript. Nothing the model claims is trusted:
every item must cite existing segments and quote them verbatim (<= 15 words), and numbers
must appear in the quote. Ungrounded items are dropped and counted."""

from __future__ import annotations

import json
import re
from collections import Counter
from collections.abc import Sequence
from datetime import date
from typing import Any

from app.domain import (
    SENTIMENTS,
    ActionItem,
    Commitment,
    Insights,
    Objection,
    Segment,
    ValidationReport,
)
from app.pipeline.pii import redact_text
from app.textutil import normalize, numbers_in, word_count

ALLOWED_KEYS = {"summary", "sentiment", "action_items", "objections", "commitments",
                "competitors", "followup_draft"}
OWNERS = ("agent", "customer")
OBJECTION_TYPES = ("price", "timing", "competitor", "security", "other")
COMMIT_KINDS = ("discount", "price", "deadline", "other")
MAX_QUOTE_WORDS = 15


class SchemaError(ValueError):
    """The model's output has the wrong overall shape (the caller may retry)."""


def check_grounding(item: dict[str, Any], by_id: dict[str, Segment]) -> str | None:
    """Return a drop reason, or None if evidence + quote are valid."""
    ev = item.get("evidence")
    if not isinstance(ev, list) or not ev or not all(isinstance(e, str) for e in ev):
        return "missing_evidence"
    if any(e not in by_id for e in ev):
        return "unknown_segment"
    quote = item.get("quote")
    if not isinstance(quote, str) or not quote.strip():
        return "missing_quote"
    if word_count(quote) > MAX_QUOTE_WORDS:
        return "quote_too_long"
    nq = normalize(quote)
    if not nq or not any(nq in normalize(by_id[e].text) for e in ev):
        return "quote_not_in_evidence"
    return None


def _parse(raw: str) -> dict[str, Any]:
    text = raw.strip()
    text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text)  # tolerate a fenced block
    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        raise SchemaError("output is not valid JSON") from exc
    if not isinstance(data, dict):
        raise SchemaError("output must be a JSON object")
    return data


def _list(data: dict[str, Any], key: str) -> list[Any]:
    v = data.get(key, [])
    if not isinstance(v, list):
        raise SchemaError(f"{key} must be a list")
    return v


def build_insights(raw: str, segments: Sequence[Segment]) -> tuple[Insights, ValidationReport]:
    data = _parse(raw)
    by_id = {s.id: s for s in segments}
    transcript_norm = normalize(" ".join(s.text for s in segments))
    dropped: Counter[str] = Counter()
    normalized: list[str] = []
    proposed = 0

    summary = data.get("summary", "")
    if not isinstance(summary, str):
        raise SchemaError("summary must be a string")
    followup = data.get("followup_draft", "")
    if not isinstance(followup, str):
        raise SchemaError("followup_draft must be a string")
    sentiment = data.get("sentiment", "neutral")
    if sentiment not in SENTIMENTS:
        normalized.append("sentiment_reset")
        sentiment = "neutral"

    # defence in depth: the model only saw tokens, but a compromised one could invent PII
    summary, c1 = redact_text(summary[:600])
    followup, c2 = redact_text(followup[:1500])
    if c1 or c2:
        normalized.append("pii_removed_from_free_text")

    actions: list[ActionItem] = []
    for it in _list(data, "action_items"):
        proposed += 1
        if not isinstance(it, dict) or not isinstance(it.get("text"), str) or not it["text"].strip():
            dropped["malformed"] += 1
            continue
        if it.get("owner") not in OWNERS:
            dropped["bad_owner"] += 1
            continue
        reason = check_grounding(it, by_id)
        if reason:
            dropped[reason] += 1
            continue
        due = it.get("due")
        if due is not None:
            try:
                date.fromisoformat(str(due))
                due = str(due)
            except ValueError:
                normalized.append("invalid_due_cleared")
                due = None
        actions.append(ActionItem(it["text"].strip()[:300], it["owner"], due,
                                  tuple(it["evidence"]), it["quote"].strip()))

    objections: list[Objection] = []
    for it in _list(data, "objections"):
        proposed += 1
        if not isinstance(it, dict) or it.get("type") not in OBJECTION_TYPES:
            dropped["malformed"] += 1
            continue
        reason = check_grounding(it, by_id)
        if reason:
            dropped[reason] += 1
            continue
        objections.append(Objection(it["type"], tuple(it["evidence"]), it["quote"].strip()))

    commitments: list[Commitment] = []
    for it in _list(data, "commitments"):
        proposed += 1
        if not isinstance(it, dict) or it.get("kind") not in COMMIT_KINDS or it.get("who") not in OWNERS:
            dropped["malformed"] += 1
            continue
        reason = check_grounding(it, by_id)
        if reason:
            dropped[reason] += 1
            continue
        pct = it.get("value_pct")
        if pct is not None and (isinstance(pct, bool) or not isinstance(pct, int) or not 0 <= pct <= 100):
            dropped["malformed"] += 1
            continue
        if it["kind"] == "discount" and (pct is None or pct not in numbers_in(it["quote"])):
            dropped["numeric_mismatch"] += 1  # the number must be readable in the quote itself
            continue
        speakers = {by_id[e].speaker for e in it["evidence"]}
        if it["who"] not in speakers and "unknown" not in speakers:
            dropped["speaker_mismatch"] += 1  # an agent commitment must be said by the agent
            continue
        commitments.append(Commitment(it["kind"], pct, it["who"], tuple(it["evidence"]),
                                      it["quote"].strip()))

    competitors: list[str] = []
    for name in _list(data, "competitors"):
        proposed += 1
        if isinstance(name, str) and name.strip() and normalize(name) in transcript_norm:
            competitors.append(name.strip())
        else:
            dropped["competitor_not_in_transcript"] += 1

    ignored = tuple(sorted(k for k in data if k not in ALLOWED_KEYS))
    kept = len(actions) + len(objections) + len(commitments) + len(competitors)
    insights = Insights(summary, sentiment, tuple(actions), tuple(objections), tuple(commitments),
                        tuple(competitors), followup)
    return insights, ValidationReport(proposed, kept, dict(dropped), ignored, tuple(normalized))
