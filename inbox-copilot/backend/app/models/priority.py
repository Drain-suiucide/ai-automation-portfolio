import uuid

from sqlalchemy import Float, ForeignKey, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin


class Priority(Base, TimestampMixin):
    __tablename__ = "priorities"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    email_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("emails.id", ondelete="CASCADE"),
        unique=True,
        index=True,
    )
    priority: Mapped[str] = mapped_column(String(4), index=True)
    score: Mapped[float] = mapped_column(Float, default=0.0, index=True)
    factors: Mapped[list] = mapped_column(JSONB, default=list)
    reason: Mapped[str | None] = mapped_column(String(1024), nullable=True)

    model: Mapped[str] = mapped_column(String(128))
    provider: Mapped[str] = mapped_column(String(32))
    latency_ms: Mapped[int] = mapped_column(default=0)
    fallback_used: Mapped[bool] = mapped_column(default=False)

    email: Mapped["Email"] = relationship(back_populates="priority")  # noqa: F821