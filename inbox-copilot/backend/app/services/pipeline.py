import logging
import uuid
from datetime import UTC, datetime

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db.enums import EmailDirection
from app.models.classification import Classification
from app.models.email import Email
from app.models.extraction import Extraction
from app.models.priority import Priority
from app.models.thread import Thread
from app.schemas.pipeline import ProcessMeta, ProcessRequest, ProcessResponse
from app.services.classifier import classify_email
from app.services.extractor import extract_entities
from app.services.prioritizer import prioritize_email

logger = logging.getLogger(__name__)


class DuplicateEmailError(RuntimeError):
    def __init__(self, external_id: str):
        super().__init__(f"Email with external_id={external_id} already exists")
        self.external_id = external_id


def process_email(db: Session, payload: ProcessRequest) -> ProcessResponse:
    external_id = payload.external_id or f"mvp-{uuid.uuid4()}"

    # Дедупликация
    existing = db.query(Email).filter(Email.external_message_id == external_id).first()
    if existing:
        raise DuplicateEmailError(external_id)

    # 1. Classification
    classification, cls_meta = classify_email(
        subject=payload.subject,
        body=payload.body,
        from_address=payload.from_address,
    )

    # 2. Extraction
    extraction, ext_meta = extract_entities(
        subject=payload.subject,
        body=payload.body,
        from_address=payload.from_address,
    )

    # 3. Prioritization (с учётом classification + extraction)
    priority, pri_meta = prioritize_email(
        subject=payload.subject,
        body=payload.body,
        from_address=payload.from_address,
        category=classification.category,
        sentiment=extraction.sentiment,
        urgency=extraction.urgency,
    )

    # 4. Сохранение в БД — одна транзакция
    try:
        thread = Thread(
            mailbox_id=None,
            external_thread_id=f"mvp-thread-{uuid.uuid4()}",
            subject=payload.subject,
            last_message_at=datetime.now(UTC),
        )
        db.add(thread)
        db.flush()

        email = Email(
            thread_id=thread.id,
            mailbox_id=None,
            external_message_id=external_id,
            direction=EmailDirection.inbound,
            from_address=payload.from_address or "unknown@unknown",
            from_name=None,
            to_addresses=[],
            cc_addresses=[],
            bcc_addresses=[],
            subject=payload.subject,
            body_text=payload.body,
            body_html=None,
            raw_headers={},
            received_at=datetime.now(UTC),
            is_read=False,
        )
        db.add(email)
        db.flush()

        db.add(Classification(
            email_id=email.id,
            category=classification.category,
            confidence=classification.confidence,
            tags=classification.tags,
            reason=classification.reason,
            model=cls_meta.model,
            provider=cls_meta.provider,
            latency_ms=cls_meta.latency_ms,
            fallback_used=cls_meta.fallback_used,
        ))

        db.add(Extraction(
            email_id=email.id,
            data=extraction.model_dump(),
            contact_name=extraction.contact_name,
            company=extraction.company,
            invoice_id=extraction.invoice_id,
            amount=extraction.amount,
            currency=extraction.currency,
            sentiment=extraction.sentiment,
            urgency=extraction.urgency,
            model=ext_meta.model,
            provider=ext_meta.provider,
            latency_ms=ext_meta.latency_ms,
            fallback_used=ext_meta.fallback_used,
        ))

        db.add(Priority(
            email_id=email.id,
            priority=priority.priority,
            score=priority.score,
            factors=priority.factors,
            reason=priority.reason,
            model=pri_meta.model,
            provider=pri_meta.provider,
            latency_ms=pri_meta.latency_ms,
            fallback_used=pri_meta.fallback_used,
        ))

        db.commit()
        db.refresh(email)
        email_id = str(email.id)

    except IntegrityError as e:
        db.rollback()
        logger.exception("DB integrity error during pipeline")
        raise RuntimeError(f"Database error: {e}") from e
    except Exception:
        db.rollback()
        logger.exception("Pipeline error")
        raise

    return ProcessResponse(
        email_id=email_id,
        classification=classification,
        extraction=extraction,
        priority=priority,
        meta=ProcessMeta(
            classification=cls_meta,
            extraction=ext_meta,
            priority=pri_meta,
        ),
    )