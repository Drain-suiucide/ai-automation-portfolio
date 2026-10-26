from typing import Literal

from pydantic import BaseModel

from app.schemas.classification import LLMMeta

Sentiment = Literal["positive", "neutral", "negative", "angry"]
Urgency = Literal["low", "normal", "high", "critical"]


class ExtractedEntities(BaseModel):
    contact_name: str | None = None
    company: str | None = None
    email: str | None = None
    phone: str | None = None
    product: str | None = None
    order_id: str | None = None
    invoice_id: str | None = None
    amount: float | None = None
    currency: str | None = None
    deadline: str | None = None
    requested_action: str | None = None
    sentiment: Sentiment = "neutral"
    language: str = "en"
    urgency: Urgency = "normal"


class ExtractRequest(BaseModel):
    subject: str | None = None
    body: str
    from_address: str | None = None


class ExtractResponse(BaseModel):
    entities: ExtractedEntities
    meta: LLMMeta