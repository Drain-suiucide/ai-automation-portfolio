import uuid

from sqlalchemy import Float, ForeignKey, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin


class Extraction(Base, TimestampMixin):
    __tablename__ = "extractions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    email_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("emails.id", ondelete="CASCADE"),
        unique=True,
        index=True,
    )
    data: Mapped[dict] = mapped_column(JSONB, default=dict)

    contact_name: Mapped[str | None] = mapped_column(String(256), nullable=True, index=True)
    company: Mapped[str | None] = mapped_column(String(256), nullable=True, index=True)
    invoice_id: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    amount: Mapped[float | None] = mapped_column(Float, nullable=True)
    currency: Mapped[str | None] = mapped_column(String(8), nullable=True)
    sentiment: Mapped[str | None] = mapped_column(String(16), nullable=True)
    urgency: Mapped[str | None] = mapped_column(String(16), nullable=True)

    model: Mapped[str] = mapped_column(String(128))
    provider: Mapped[str] = mapped_column(String(32))
    latency_ms: Mapped[int] = mapped_column(default=0)
    fallback_used: Mapped[bool] = mapped_column(default=False)

    email: Mapped["Email"] = relationship(back_populates="extraction")  # noqa: F821