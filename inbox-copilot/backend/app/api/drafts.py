from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.enums import DraftStatus
from app.db.session import SessionLocal
from app.models.draft import Draft
from app.models.email import Email
from app.schemas.classification import LLMMeta
from app.schemas.draft import DraftRequest, DraftResponse
from app.services.drafter import generate_draft
from app.services.llm_client import LLMError

router = APIRouter(tags=["drafts"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _status_value(status) -> str:
    return status.value if hasattr(status, "value") else str(status)


@router.post("/emails/{email_id}/draft", response_model=DraftResponse)
def create_draft(
    email_id: str,
    payload: DraftRequest | None = None,
    db: Session = Depends(get_db),
) -> DraftResponse:
    email = db.query(Email).filter(Email.id == email_id).first()
    if not email:
        raise HTTPException(status_code=404, detail="Email not found")

    # ⚠️ Эти три строки критичны — без них будет UnboundLocalError
    category = email.classification.category if email.classification else "other"
    extraction = email.extraction
    ext_data: dict = extraction.data if extraction else {}
    payload = payload or DraftRequest()

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

    draft = Draft(
        email_id=email.id,
        status=DraftStatus.draft,
        subject=result.subject,
        body_text=result.body_text,
        body_html=None,
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
    db.add(draft)
    db.commit()
    db.refresh(draft)

    return DraftResponse(
        draft_id=str(draft.id),
        email_id=str(email.id),
        status=_status_value(draft.status),
        subject=draft.subject,
        body_text=draft.body_text,
        tone=draft.tone,
        language=draft.language,
        confidence=draft.confidence,
        warnings=draft.warnings or [],
        cited_kb=draft.cited_kb or [],
        meta=meta,
    )


@router.get("/drafts/{draft_id}", response_model=DraftResponse)
def get_draft(draft_id: str, db: Session = Depends(get_db)) -> DraftResponse:
    draft = db.query(Draft).filter(Draft.id == draft_id).first()
    if not draft:
        raise HTTPException(status_code=404, detail="Draft not found")

    meta = LLMMeta(
        model=draft.model,
        provider=draft.provider,
        latency_ms=draft.latency_ms,
        fallback_used=draft.fallback_used,
    )
    return DraftResponse(
        draft_id=str(draft.id),
        email_id=str(draft.email_id),
        status=_status_value(draft.status),
        subject=draft.subject,
        body_text=draft.body_text,
        tone=draft.tone,
        language=draft.language,
        confidence=draft.confidence,
        warnings=draft.warnings or [],
        cited_kb=draft.cited_kb or [],
        meta=meta,
    )
@router.get("/emails/{email_id}/drafts", response_model=list[DraftResponse])
def list_drafts_for_email(
    email_id: str, db: Session = Depends(get_db)
) -> list[DraftResponse]:
    drafts = (
        db.query(Draft)
        .filter(Draft.email_id == email_id)
        .order_by(Draft.created_at.desc())
        .all()
    )
    result = []
    for draft in drafts:
        meta = LLMMeta(
            model=draft.model,
            provider=draft.provider,
            latency_ms=draft.latency_ms,
            fallback_used=draft.fallback_used,
        )
        result.append(
            DraftResponse(
                draft_id=str(draft.id),
                email_id=str(draft.email_id),
                status=_status_value(draft.status),
                subject=draft.subject,
                body_text=draft.body_text,
                tone=draft.tone,
                language=draft.language,
                confidence=draft.confidence,
                warnings=draft.warnings or [],
                cited_kb=draft.cited_kb or [],
                meta=meta,
            )
        )
    return result