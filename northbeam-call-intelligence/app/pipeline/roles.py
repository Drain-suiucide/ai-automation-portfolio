"""Speaker roles. Stereo channels give roles for free; otherwise a small cue heuristic."""

from __future__ import annotations

import re
from collections.abc import Sequence
from dataclasses import replace

from app.domain import Segment

_AGENT_CUES = re.compile(
    r"thank you for calling|this is \w+ (?:from|at) northbeam|northbeam (?:sales|support)"
    r"|this call (?:is|may be) (?:being )?recorded|i'?ll send you|let me send you", re.I)


def assign_roles(segments: Sequence[Segment]) -> list[Segment]:
    """Keep known roles; label unlabeled segments 'agent' only on strong cues, else 'unknown'."""
    out = []
    for s in segments:
        if s.speaker == "unknown" and _AGENT_CUES.search(s.text):
            s = replace(s, speaker="agent")
        out.append(s)
    return out
