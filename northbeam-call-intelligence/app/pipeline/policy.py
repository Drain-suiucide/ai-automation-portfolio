"""Deterministic policy engine. It re-reads the transcript itself: model output can ADD
flags (e.g. a negative sentiment) but can never remove one (INV-6)."""

from __future__ import annotations

import re
from collections.abc import Sequence

from app.config import Policy
from app.domain import Flag, Insights, Segment, ValidationReport
from app.pipeline.discounts import discount_hits
from app.textutil import normalize


def _has(text: str, phrase: str) -> bool:
    return re.search(rf"(?<!\w){re.escape(phrase.lower())}(?!\w)", text.lower()) is not None


def evaluate(segments: Sequence[Segment], insights: Insights, avg_confidence: float | None,
             report: ValidationReport, policy: Policy) -> list[Flag]:
    flags: list[Flag] = []
    by_id = {s.id: s for s in segments}
    speaker_text = lambda who: [s for s in segments if s.speaker in who]  # noqa: E731

    # 1. discounts: transcript scan (agent or unlabeled speech) + validated commitments
    over: dict[int, set[str]] = {}
    for h in discount_hits(segments):
        if h.speaker != "customer" and h.pct > policy.max_discount_pct:
            over.setdefault(h.pct, set()).add(h.segment_id)
    for c in insights.commitments:
        if c.kind == "discount" and c.value_pct and c.value_pct > policy.max_discount_pct:
            over.setdefault(c.value_pct, set()).update(c.evidence)
    if over:
        top = max(over)
        flags.append(Flag("discount_over_policy",
                          f"discount {top}% > policy max {policy.max_discount_pct}%",
                          "review", tuple(sorted(over[top]))))

    # 2. churn: explicit cancellation, or a competitor mention combined with negative tone
    cust = speaker_text(("customer", "unknown"))
    cancel = [s.id for s in cust if any(_has(s.text, k) for k in policy.churn_keywords)]
    comp = [s.id for s in cust if any(_has(s.text, k) for k in policy.competitors)]
    neg_hits = sum(_has(s.text, w) for s in cust for w in policy.negative_words)
    negative = neg_hits >= policy.negative_hits_threshold or insights.sentiment == "negative"
    if cancel or (comp and negative):
        flags.append(Flag("churn_risk", "customer signals cancellation or a competitor switch",
                          "review", tuple(cancel or comp)))

    # 3. compliance / legal topics anywhere in the call
    legal = [s.id for s in segments if any(_has(s.text, k) for k in policy.compliance_keywords)]
    if legal:
        flags.append(Flag("compliance_review", "legal or data-protection topic mentioned",
                          "review", tuple(legal)))

    # 4. text that tries to instruct the assistant
    pats = [re.compile(p, re.I) for p in policy.injection_patterns]
    inj = [s.id for s in segments if any(p.search(s.text) for p in pats)]
    if inj:
        flags.append(Flag("prompt_injection_suspected",
                          "speech contains instruction-like text; treated as data only",
                          "review", tuple(inj)))

    # 5. ASR quality
    if avg_confidence is not None and avg_confidence < policy.min_asr_confidence:
        flags.append(Flag("low_asr_confidence",
                          f"average ASR confidence {avg_confidence:.2f} < {policy.min_asr_confidence}",
                          "review"))

    # 6. role-dependent findings from unlabeled speakers
    unknown_ids = {s.id for s in segments if s.speaker == "unknown"}
    role_ids = sorted({e for f in flags if f.code == "discount_over_policy" for e in f.evidence}
                      & unknown_ids)
    role_ids += sorted({e for c in insights.commitments for e in c.evidence} & unknown_ids)
    if role_ids:
        flags.append(Flag("unknown_speaker_role",
                          "a commitment or price statement comes from an unlabeled speaker",
                          "review", tuple(dict.fromkeys(role_ids))))

    # 7. visibility only
    if report.dropped_total:
        flags.append(Flag("ungrounded_items_dropped",
                          f"{report.dropped_total} model claim(s) without valid evidence were dropped",
                          "info"))
    _ = (by_id, normalize)  # keep helpers referenced for readers extending the policy
    return flags


def requires_review(flags: Sequence[Flag]) -> bool:
    return any(f.severity == "review" for f in flags)
