from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.enums import DraftStatus
from app.db.session import SessionLocal
from app.models.draft import Draft
from app.models.email import Email
from app.schemas.draft import (
    ActionResponse,
    DraftResponse,
    RegenerateRequest,
    RejectRequest,
)
from app.services.audit import log_action
from app.services.draft_workflow import approve_draft, reject_draft, send_draft
from app.services.drafter import generate_draft
from app.services.llm_client import LLMError

router = APIRouter(tags=["draft-actions"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _status_str(s) -> str:
    return s.value if hasattr(s, "value") else str(s)


@router.post("/drafts/{draft_id}/approve", response_model=ActionResponse)
def approve(draft_id: str, db: Session = Depends(get_db)) -> ActionResponse:
    draft = approve_draft(db, draft_id)
    return ActionResponse(
        draft_id=str(draft.id),
        status=_status_str(draft.status),
        message="Draft approved",
    )


@router.post("/drafts/{draft_id}/reject", response_model=ActionResponse)
def reject(
    draft_id: str, payload: RejectRequest, db: Session = Depends(get_db)
) -> ActionResponse:
    draft = reject_draft(db, draft_id, reason=payload.reason)
    return ActionResponse(
        draft_id=str(draft.id),
        status=_status_str(draft.status),
        message=f"Draft rejected: {payload.reason}",
    )


@router.post("/drafts/{draft_id}/send", response_model=ActionResponse)
def send(draft_id: str, db: Session = Depends(get_db)) -> ActionResponse:
    draft = send_draft(db, draft_id)
    return ActionResponse(
        draft_id=str(draft.id),
        status=_status_str(draft.status),
        message="Draft sent (stub — no real SMTP in MVP)",
    )


@router.post("/drafts/{draft_id}/regenerate", response_model=DraftResponse)
def regenerate(
    draft_id: str,
    payload: RegenerateRequest | None = None,
    db: Session = Depends(get_db),
) -> DraftResponse:
    old = db.query(Draft).filter(Draft.id == draft_id).first()
    if not old:
        raise HTTPException(status_code=404, detail="Draft not found")

    email = db.query(Email).filter(Email.id == old.email_id).first()
    if not email:
        raise HTTPException(status_code=404, detail="Parent email not found")

    category = email.classification.category if email.classification else "other"
    extraction = email.extraction
    ext_data: dict = extraction.data if extraction else {}
    payload = payload or RegenerateRequest()

    try:
        result, meta = generate_draft(
            from_address=email.from_address,
            subject=email.subject,
            body=email.body_text or "",
            category=category,
            contact_name=extraction.contact_name if extraction else None,
            company=extraction.company if extraction else None,
            invoice_id=extraction.invoice_id if extraction else None,
            amount=extraction.amount if extraction else None,
            currency=extraction.currency if extraction else None,
            deadline=ext_data.get("deadline"),
            requested_action=ext_data.get("requested_action"),
            sentiment=extraction.sentiment if extraction else "neutral",
            urgency=extraction.urgency if extraction else "normal",
            tone=payload.tone,
            instructions=payload.instructions,
        )
    except LLMError as e:
        raise HTTPException(status_code=502, detail=str(e)) from e

    new_draft = Draft(
        email_id=email.id,
        status=DraftStatus.draft,
        subject=result.subject,
        body_text=result.body_text,
        tone=result.tone,
        language=result.language,
        confidence=result.confidence,
        warnings=result.warnings,
        cited_kb=result.cited_kb,
        model=meta.model,
        provider=meta.provider,
        latency_ms=meta.latency_ms,
        fallback_used=meta.fallback_used,
        prompt_version="v1",
    )
    db.add(new_draft)
    db.flush()

    log_action(
        db,
        entity_type="draft",
        entity_id=new_draft.id,
        action="regenerated",
        actor="system",
        payload={
            "email_id": str(email.id),
            "previous_draft_id": str(old.id),
            "instructions": payload.instructions,
        },
    )
    db.commit()
    db.refresh(new_draft)

    return DraftResponse(
        draft_id=str(new_draft.id),
        email_id=str(new_draft.email_id),
        status=_status_str(new_draft.status),
        subject=new_draft.subject,
        body_text=new_draft.body_text,
        tone=new_draft.tone,
        language=new_draft.language,
        confidence=new_draft.confidence,
        warnings=new_draft.warnings or [],
        cited_kb=new_draft.cited_kb or [],
        meta=meta,
    )