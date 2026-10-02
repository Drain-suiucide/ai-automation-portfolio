"""Metric helpers shared by scripts/evaluate.py and the tests."""

from __future__ import annotations

from collections.abc import Sequence

from app.textutil import normalize


def wer(reference: str, hypothesis: str) -> float:
    """Word error rate via Levenshtein distance over normalized words."""
    ref, hyp = normalize(reference).split(), normalize(hypothesis).split()
    if not ref:
        return 0.0 if not hyp else 1.0
    prev = list(range(len(hyp) + 1))
    for i, r in enumerate(ref, start=1):
        cur = [i] + [0] * len(hyp)
        for j, w in enumerate(hyp, start=1):
            cur[j] = min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (r != w))
        prev = cur
    return prev[-1] / len(ref)


def jaccard(a: str, b: str) -> float:
    sa, sb = set(normalize(a).split()), set(normalize(b).split())
    if not sa and not sb:
        return 1.0
    return len(sa & sb) / len(sa | sb)


def match_items(gold: Sequence[dict[str, str]], pred: Sequence[dict[str, str]],
                threshold: float = 0.8) -> tuple[int, int, int]:
    """Greedy one-to-one match on (owner, text similarity). Returns (tp, fp, fn)."""
    used: set[int] = set()
    tp = 0
    for g in gold:
        best, best_score = None, 0.0
        for i, p in enumerate(pred):
            if i in used or p["owner"] != g["owner"]:
                continue
            s = jaccard(g["text"], p["text"])
            if s >= threshold and s > best_score:
                best, best_score = i, s
        if best is not None:
            used.add(best)
            tp += 1
    return tp, len(pred) - tp, len(gold) - tp


def prf(tp: int, fp: int, fn: int) -> dict[str, float]:
    p = tp / (tp + fp) if tp + fp else 1.0
    r = tp / (tp + fn) if tp + fn else 1.0
    f = 2 * p * r / (p + r) if p + r else 0.0
    return {"precision": round(p, 3), "recall": round(r, 3), "f1": round(f, 3)}
