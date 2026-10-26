from typing import Literal

from pydantic import BaseModel, Field

Category = Literal["sales", "support", "billing", "spam", "partnership", "other"]


class ClassificationResult(BaseModel):
    """Structured output от LLM для классификации письма."""

    category: Category = Field(description="Primary category of the email")
    confidence: float = Field(ge=0.0, le=1.0, description="Confidence score 0..1")
    tags: list[str] = Field(default_factory=list, description="Up to 5 short tags")
    reason: str = Field(description="One-sentence rationale in the language of the email")


class ClassifyRequest(BaseModel):
    subject: str | None = None
    body: str
    from_address: str | None = None


class LLMMeta(BaseModel):
    model: str
    provider: str
    latency_ms: int
    prompt_tokens: int | None = None
    completion_tokens: int | None = None
    total_tokens: int | None = None
    cost_usd: float | None = None
    fallback_used: bool = False


class ClassifyResponse(BaseModel):
    classification: ClassificationResult
    meta: LLMMeta