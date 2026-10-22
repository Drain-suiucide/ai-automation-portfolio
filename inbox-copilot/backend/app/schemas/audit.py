from datetime import datetime

from pydantic import BaseModel


class AuditLogEntry(BaseModel):
    id: str
    entity_type: str
    entity_id: str
    action: str
    actor: str
    payload: dict
    created_at: datetime


class AuditListResponse(BaseModel):
    items: list[AuditLogEntry]
    total: int
    limit: int
    offset: int