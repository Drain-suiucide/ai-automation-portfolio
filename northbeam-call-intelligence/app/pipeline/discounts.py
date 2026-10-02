"""Finds percentage statements near discount context. Shared by the fake extractor and the
policy engine (the policy re-scans the transcript itself, so it never trusts the model)."""

from __future__ import annotations

import re
from collections.abc import Sequence
from dataclasses import dataclass

from app.domain import Segment
from app.textutil import numbers_in, quote_around

_PCT_DIGITS = re.compile(r"(\d{1,3})\s*(?:%|per\s?cent\b|percent\b)", re.I)
_PCT_WORDS = re.compile(r"((?:[a-z]+[\s-]){0,2}[a-z]+)\s+(?:per\s?cent|percent)\b", re.I)
_CONTEXT = re.compile(r"\b(discount\w*|off|deal|reduc\w*|cheaper|rebate|price|pricing|offer)\b", re.I)


@dataclass(frozen=True)
class DiscountHit:
    segment_id: str
    speaker: str
    pct: int
    quote: str


def discount_hits(segments: Sequence[Segment]) -> list[DiscountHit]:
    """Percentages stated in a segment whose own text or the two previous segments talk about
    price/discounts. Customer requests are returned too; callers filter by speaker."""
    hits: list[DiscountHit] = []
    for i, seg in enumerate(segments):
        window = " ".join(s.text for s in segments[max(0, i - 2): i + 1])
        if not _CONTEXT.search(window):
            continue
        found: list[tuple[int, int, int]] = []  # (pct, start, end)
        for m in _PCT_DIGITS.finditer(seg.text):
            found.append((int(m.group(1)), m.start(), m.end()))
        for m in _PCT_WORDS.finditer(seg.text):
            nums = [n for n in numbers_in(m.group(1)) if 0 < n <= 100]
            if nums:
                found.append((max(nums), m.start(), m.end()))
        for pct, start, end in found:
            hits.append(DiscountHit(seg.id, seg.speaker, pct,
                                    quote_around(seg.text, start, end, before=3, after=4)))
    return hits
