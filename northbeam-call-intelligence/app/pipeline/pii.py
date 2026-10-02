"""PII redaction. Runs BEFORE any LLM call, log line or database write.

Detected: email (written and spoken), IBAN, payment card (Luhn), phone numbers, long digit
runs, and digits dictated word by word. Names are NOT detected (a NER model is the
documented production seam). The token map lives only inside one Redactor instance and is
never persisted: the LLM, the logs and the database only ever see [EMAIL_1]-style tokens.
"""

from __future__ import annotations

import re
from collections import Counter
from collections.abc import Sequence
from dataclasses import replace

from app.domain import Segment

_EMAIL = re.compile(r"[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}")
_SPOKEN_EMAIL = re.compile(r"\b\w+(?:\s+dot\s+\w+)*\s+at\s+\w+(?:\s+dot\s+\w+)+\b", re.I)
_IBAN = re.compile(r"\b[A-Z]{2}\d{2}(?: ?[A-Z0-9]{4}){2,7}(?: ?[A-Z0-9]{1,3})?\b")
_CARD_LIKE = re.compile(r"(?<!\d)(?:\d[ \-]?){12,18}\d(?!\d)")
_SPOKEN_DIGITS = re.compile(
    r"\b(?:(?:zero|oh|one|two|three|four|five|six|seven|eight|nine)(?:[\s,.\-]+|\b)){7,}", re.I)
_PHONE_INTL = re.compile(r"(?<!\w)\+\d[\d\s().\-]{6,16}\d")
_PHONE_GROUPED = re.compile(r"(?<!\d)\(?\d{2,4}\)?[\s.\-]\d{3,4}[\s.\-]\d{3,4}(?!\d)")
_LONG_DIGITS = re.compile(r"(?<!\d)\d{9,15}(?!\d)")
_WORD_DIGIT = {"zero": "0", "oh": "0", "one": "1", "two": "2", "three": "3", "four": "4",
               "five": "5", "six": "6", "seven": "7", "eight": "8", "nine": "9"}


def luhn_ok(digits: str) -> bool:
    total, alt = 0, False
    for ch in reversed(digits):
        d = int(ch)
        if alt:
            d *= 2
            if d > 9:
                d -= 9
        total += d
        alt = not alt
    return total % 10 == 0


class Redactor:
    """Replaces PII with stable per-call tokens, e.g. [EMAIL_1]."""

    def __init__(self) -> None:
        self._map: dict[tuple[str, str], str] = {}
        self.counts: Counter[str] = Counter()

    def _token(self, kind: str, value: str) -> str:
        key = (kind, value)
        if key not in self._map:
            n = sum(1 for k, _ in self._map if k == kind) + 1
            self._map[key] = f"[{kind}_{n}]"
        self.counts[kind] += 1
        return self._map[key]

    def _digits_token(self, digits: str, raw: str) -> str:
        if 13 <= len(digits) <= 19 and luhn_ok(digits):
            return self._token("CARD", digits)
        if len(digits) >= 16:
            return self._token("NUMBER", digits)
        return self._token("PHONE", digits)

    def redact(self, text: str) -> str:
        text = _EMAIL.sub(lambda m: self._token("EMAIL", m.group(0).lower()), text)
        text = _SPOKEN_EMAIL.sub(lambda m: self._token("EMAIL", m.group(0).lower()), text)
        text = _IBAN.sub(lambda m: self._token("IBAN", re.sub(r"\s", "", m.group(0))), text)

        def card_like(m: re.Match[str]) -> str:
            digits = re.sub(r"\D", "", m.group(0))
            return self._digits_token(digits, m.group(0)) if len(digits) >= 13 else m.group(0)

        text = _CARD_LIKE.sub(card_like, text)

        def spoken(m: re.Match[str]) -> str:
            digits = "".join(_WORD_DIGIT[w] for w in re.findall(r"[a-z]+", m.group(0).lower()))
            return self._digits_token(digits, m.group(0)) + " "

        text = _SPOKEN_DIGITS.sub(spoken, text)
        for pat in (_PHONE_INTL, _PHONE_GROUPED, _LONG_DIGITS):
            text = pat.sub(lambda m: self._token("PHONE", re.sub(r"\D", "", m.group(0))), text)
        return text


def redact_text(text: str) -> tuple[str, dict[str, int]]:
    r = Redactor()
    out = r.redact(text)
    return out, dict(r.counts)


def redact_segments(segments: Sequence[Segment]) -> tuple[list[Segment], dict[str, int]]:
    r = Redactor()
    out = [replace(s, text=r.redact(s.text)) for s in segments]
    return out, dict(r.counts)
