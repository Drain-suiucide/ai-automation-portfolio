from __future__ import annotations

from app.models import ALLOWED_TRANSITIONS, Lead, LeadState


class InvalidTransitionError(ValueError):
    pass


def can_transition(current: LeadState, new: LeadState) -> bool:
    if current == new:
        return True
    return new in ALLOWED_TRANSITIONS.get(current, set())


def transition(lead: Lead, new_state: LeadState) -> Lead:
    if not can_transition(lead.state, new_state):
        raise InvalidTransitionError(
            f"invalid transition {lead.state.value} -> {new_state.value}"
        )
    lead.state = new_state
    lead.touch()
    return lead
