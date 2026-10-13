from __future__ import annotations

import re

from app.models import Draft, Fact, Lead
from app.pipeline.draft import neutral_draft


def _tokenize(text: str) -> set[str]:
    return {t for t in re.findall(r"[a-z0-9]+", text.lower()) if len(t) > 2}


def sentence_supported(sentence_text: str, facts: list[Fact], fact_ids: list[str]) -> bool:
    if not fact_ids:
        return False
    by_id = {f.id: f for f in facts}
    for fid in fact_ids:
        fact = by_id.get(fid)
        if fact is None:
            return False
        sent_toks = _tokenize(sentence_text)
        fact_toks = _tokenize(fact.snippet + " " + fact.value)
        if not sent_toks or not fact_toks:
            return False
        overlap = len(sent_toks & fact_toks) / max(1, len(sent_toks))
        if overlap < 0.25:
            return False
    return True


def validate_grounding(lead: Lead) -> Draft:
    """INV-4: no unsupported personalized claims survive."""
    assert lead.draft is not None
    draft = lead.draft
    fact_ids = {f.id for f in lead.facts}

    for sentence in draft.sentences:
        if not sentence.fact_ids:
            draft.grounding = "failed"
            draft.block_reason = "grounding_failed"
            fallback = neutral_draft(lead)
            lead.draft = fallback
            return fallback
        if any(fid not in fact_ids for fid in sentence.fact_ids):
            draft.grounding = "failed"
            draft.block_reason = "grounding_failed"
            fallback = neutral_draft(lead)
            lead.draft = fallback
            return fallback
        if not sentence_supported(sentence.text, lead.facts, sentence.fact_ids):
            draft.grounding = "failed"
            draft.block_reason = "grounding_failed"
            fallback = neutral_draft(lead)
            lead.draft = fallback
            return fallback

    draft.grounding = "passed" if draft.sentences else "neutral"
    draft.block_reason = None
    return draft
