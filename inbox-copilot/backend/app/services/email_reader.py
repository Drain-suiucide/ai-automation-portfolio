from sqlalchemy.orm import Session, joinedload

from app.models.email import Email
from app.schemas.classification import ClassificationResult
from app.schemas.email import EmailDetail, EmailListItem, EmailListResponse
from app.schemas.extraction import ExtractedEntities
from app.schemas.prioritization import PriorityResult


def list_emails(
    db: Session,
    *,
    category: str | None = None,
    priority: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> EmailListResponse:
    q = (
        db.query(Email)
        .options(
            joinedload(Email.classification),
            joinedload(Email.priority),
            joinedload(Email.extraction),
        )
        .order_by(Email.received_at.desc())
    )

    if category:
        q = q.join(Email.classification).filter(
            Email.classification.has(category=category)
        )
    if priority:
        q = q.join(Email.priority).filter(Email.priority.has(priority=priority))

    total = q.count()
    rows = q.limit(limit).offset(offset).all()

    items = [
        EmailListItem(
            id=str(e.id),
            external_message_id=e.external_message_id,
            from_address=e.from_address,
            subject=e.subject,
            received_at=e.received_at,
            category=e.classification.category if e.classification else None,
            confidence=e.classification.confidence if e.classification else None,
            priority=e.priority.priority if e.priority else None,
            score=e.priority.score if e.priority else None,
            sentiment=e.extraction.sentiment if e.extraction else None,
            urgency=e.extraction.urgency if e.extraction else None,
        )
        for e in rows
    ]
    return EmailListResponse(items=items, total=total, limit=limit, offset=offset)


def get_email(db: Session, email_id: str) -> EmailDetail | None:
    e = (
        db.query(Email)
        .options(
            joinedload(Email.classification),
            joinedload(Email.extraction),
            joinedload(Email.priority),
        )
        .filter(Email.id == email_id)
        .first()
    )
    if not e:
        return None

    classification = None
    if e.classification:
        classification = ClassificationResult(
            category=e.classification.category,
            confidence=e.classification.confidence,
            tags=e.classification.tags,
            reason=e.classification.reason or "",
        )

    extraction = None
    if e.extraction:
        extraction = ExtractedEntities(**e.extraction.data)

    priority = None
    if e.priority:
        priority = PriorityResult(
            priority=e.priority.priority,
            score=e.priority.score,
            factors=e.priority.factors,
            reason=e.priority.reason or "",
        )

    meta = {}
    if e.classification:
        meta["classification"] = {
            "model": e.classification.model,
            "provider": e.classification.provider,
            "latency_ms": e.classification.latency_ms,
            "fallback_used": e.classification.fallback_used,
        }
    if e.extraction:
        meta["extraction"] = {
            "model": e.extraction.model,
            "provider": e.extraction.provider,
            "latency_ms": e.extraction.latency_ms,
            "fallback_used": e.extraction.fallback_used,
        }
    if e.priority:
        meta["priority"] = {
            "model": e.priority.model,
            "provider": e.priority.provider,
            "latency_ms": e.priority.latency_ms,
            "fallback_used": e.priority.fallback_used,
        }

    return EmailDetail(
        id=str(e.id),
        external_message_id=e.external_message_id,
        from_address=e.from_address,
        to_addresses=e.to_addresses or [],
        subject=e.subject,
        body_text=e.body_text,
        received_at=e.received_at,
        classification=classification,
        extraction=extraction,
        priority=priority,
        meta=meta,
    )