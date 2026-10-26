from datetime import datetime

from pydantic import BaseModel

from app.schemas.classification import ClassificationResult
from app.schemas.extraction import ExtractedEntities
from app.schemas.prioritization import PriorityResult


class EmailListItem(BaseModel):
    id: str
    external_message_id: str
    from_address: str
    subject: str | None
    received_at: datetime
    category: str | None
    confidence: float | None
    priority: str | None
    score: float | None
    sentiment: str | None
    urgency: str | None


class EmailDetail(BaseModel):
    id: str
    external_message_id: str
    from_address: str
    to_addresses: list[str]
    subject: str | None
    body_text: str | None
    received_at: datetime

    classification: ClassificationResult | None
    extraction: ExtractedEntities | None
    priority: PriorityResult | None

    meta: dict


class EmailListResponse(BaseModel):
    items: list[EmailListItem]
    total: int
    limit: int
    offset: int