"""Consent gate. A call is processed only if recording consent is established."""

from __future__ import annotations

from collections.abc import Sequence

from app.config import Policy
from app.domain import Segment
from app.textutil import normalize


def phrase_present(segments: Sequence[Segment], policy: Policy) -> bool:
    """True if an agent (or unlabeled) segment in the probe window announces the recording."""
    phrases = [normalize(p) for p in policy.consent_phrases]
    for s in segments:
        if s.start >= policy.consent_probe_seconds or s.speaker == "customer":
            continue
        text = normalize(s.text)
        if any(p and p in text for p in phrases):
            return True
    return False
