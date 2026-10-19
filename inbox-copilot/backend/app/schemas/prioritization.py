from typing import Literal

from pydantic import BaseModel, Field

from app.schemas.classification import LLMMeta


Priority = Literal["P0", "P1", "P2", "P3"]


class PriorityResult(BaseModel):
    priority: Priority = Field(description="P0=critical, P3=low")
    score: float = Field(ge=0.0, le=1.0)
    factors: list[str] = Field(default_factory=list)
    reason: str


class PrioritizeRequest(BaseModel):
    subject: str | None = None
    body: str
    from_address: str | None = None
    category: str | None = None
    sentiment: str | None = None
    urgency: str | None = None


class PrioritizeResponse(BaseModel):
    priority: PriorityResult
    meta: LLMMeta