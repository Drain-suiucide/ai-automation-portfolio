"""Small text helpers shared by the pipeline (stdlib only)."""

from __future__ import annotations

import hashlib
import re

_NORM = re.compile(r"[^\w%$€£]+", re.UNICODE)
_UNITS = {
    "zero": 0, "one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6,
    "seven": 7, "eight": 8, "nine": 9, "ten": 10, "eleven": 11, "twelve": 12,
    "thirteen": 13, "fourteen": 14, "fifteen": 15, "sixteen": 16, "seventeen": 17,
    "eighteen": 18, "nineteen": 19,
}
_TENS = {
    "twenty": 20, "thirty": 30, "forty": 40, "fifty": 50, "sixty": 60,
    "seventy": 70, "eighty": 80, "ninety": 90,
}


def normalize(text: str) -> str:
    """Lowercase, drop punctuation, collapse whitespace (used for quote matching)."""
    return _NORM.sub(" ", text.lower()).strip()


def word_count(text: str) -> int:
    return len(text.split())


def sha256_hex(data: bytes | str) -> str:
    if isinstance(data, str):
        data = data.encode("utf-8")
    return hashlib.sha256(data).hexdigest()


def numbers_in(text: str) -> set[int]:
    """All integers mentioned in text, as digits or English number words (<= 100)."""
    nums = {int(m) for m in re.findall(r"\d{1,9}", text)}
    toks = re.findall(r"[a-z]+", text.lower().replace("-", " "))
    i = 0
    while i < len(toks):
        t = toks[i]
        if t in _TENS:
            val = _TENS[t]
            if i + 1 < len(toks) and 1 <= _UNITS.get(toks[i + 1], 0) <= 9:
                val += _UNITS[toks[i + 1]]
                i += 1
            nums.add(val)
        elif t in _UNITS:
            nums.add(_UNITS[t])
        elif t == "hundred":
            nums.add(100)
        i += 1
    return nums


def quote_around(text: str, start: int, end: int, before: int = 3, after: int = 4,
                 max_words: int = 15) -> str:
    """Verbatim word-aligned window of `text` around [start, end), at most max_words words."""
    toks = [(m.start(), m.end()) for m in re.finditer(r"\S+", text)]
    if not toks:
        return ""
    first = next((i for i, (_, e) in enumerate(toks) if e > start), len(toks) - 1)
    last = next((i for i, (s, _) in enumerate(toks) if s >= end), len(toks)) - 1
    last = max(last, first)
    a = max(0, first - before)
    b = min(len(toks) - 1, last + after)
    if b - a + 1 > max_words:
        b = a + max_words - 1
        if b < last:  # keep the matched span inside the window
            a = max(0, last - max_words + 1)
            b = last
    return text[toks[a][0]:toks[b][1]]
