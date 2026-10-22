from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.models.audit_log import AuditLog
from app.schemas.audit import AuditListResponse, AuditLogEntry

router = APIRouter(prefix="/audit", tags=["audit"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("", response_model=AuditListResponse)
def list_audit(
    entity_type: str | None = Query(None),
    entity_id: str | None = Query(None),
    action: str | None = Query(None),
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
) -> AuditListResponse:
    q = db.query(AuditLog).order_by(AuditLog.created_at.desc())
    if entity_type:
        q = q.filter(AuditLog.entity_type == entity_type)
    if entity_id:
        q = q.filter(AuditLog.entity_id == entity_id)
    if action:
        q = q.filter(AuditLog.action == action)

    total = q.count()
    rows = q.limit(limit).offset(offset).all()

    items = [
        AuditLogEntry(
            id=str(r.id),
            entity_type=r.entity_type,
            entity_id=str(r.entity_id),
            action=r.action,
            actor=r.actor,
            payload=r.payload or {},
            created_at=r.created_at,
        )
        for r in rows
    ]
    return AuditListResponse(items=items, total=total, limit=limit, offset=offset)