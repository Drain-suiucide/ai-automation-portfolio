import uuid

from sqlalchemy.orm import Session

from app.models.audit_log import AuditLog


def log_action(
    db: Session,
    *,
    entity_type: str,
    entity_id: uuid.UUID,
    action: str,
    actor: str = "system",
    payload: dict | None = None,
) -> AuditLog:
    entry = AuditLog(
        entity_type=entity_type,
        entity_id=entity_id,
        action=action,
        actor=actor,
        payload=payload or {},
    )
    db.add(entry)
    return entry