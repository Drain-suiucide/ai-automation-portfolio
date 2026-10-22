import uuid

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.db.enums import DraftStatus
from app.models.draft import Draft
from app.services.audit import log_action


def _get_draft(db: Session, draft_id: str) -> Draft:
    try:
        uid = uuid.UUID(draft_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid draft id")
    draft = db.query(Draft).filter(Draft.id == uid).first()
    if not draft:
        raise HTTPException(status_code=404, detail="Draft not found")
    return draft


def approve_draft(db: Session, draft_id: str, actor: str = "system") -> Draft:
    draft = _get_draft(db, draft_id)
    if draft.status != DraftStatus.draft:
        raise HTTPException(
            status_code=409,
            detail=f"Cannot approve draft in status '{draft.status.value if hasattr(draft.status, 'value') else draft.status}'",
        )
    draft.status = DraftStatus.approved
    log_action(
        db,
        entity_type="draft",
        entity_id=draft.id,
        action="approved",
        actor=actor,
        payload={"email_id": str(draft.email_id)},
    )
    db.commit()
    db.refresh(draft)
    return draft


def reject_draft(db: Session, draft_id: str, reason: str, actor: str = "system") -> Draft:
    draft = _get_draft(db, draft_id)
    if draft.status != DraftStatus.draft:
        raise HTTPException(status_code=409, detail="Only 'draft' status can be rejected")
    draft.status = DraftStatus.rejected
    log_action(
        db,
        entity_type="draft",
        entity_id=draft.id,
        action="rejected",
        actor=actor,
        payload={"reason": reason, "email_id": str(draft.email_id)},
    )
    db.commit()
    db.refresh(draft)
    return draft


def send_draft(db: Session, draft_id: str, actor: str = "system") -> Draft:
    """Stub: помечаем как sent. Реальной отправки нет (MVP)."""
    draft = _get_draft(db, draft_id)
    if draft.status != DraftStatus.approved:
        raise HTTPException(
            status_code=409, detail="Only 'approved' drafts can be sent"
        )
    draft.status = DraftStatus.sent
    log_action(
        db,
        entity_type="draft",
        entity_id=draft.id,
        action="sent",
        actor=actor,
        payload={"email_id": str(draft.email_id), "channel": "stub"},
    )
    db.commit()
    db.refresh(draft)
    return draft