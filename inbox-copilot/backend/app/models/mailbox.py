import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String
from sqlalchemy import Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin
from app.db.enums import MailboxProvider


class Mailbox(Base, TimestampMixin):
    __tablename__ = "mailboxes"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    provider: Mapped[MailboxProvider] = mapped_column(
        SAEnum(MailboxProvider, name="mailbox_provider"), nullable=False
    )
    email_address: Mapped[str] = mapped_column(String(320), index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    last_synced_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    # OAuth tokens — позже зашифруем, пока как текст
    oauth_access_token: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    oauth_refresh_token: Mapped[str | None] = mapped_column(String(2048), nullable=True)

    owner: Mapped["User"] = relationship(back_populates="mailboxes")  # noqa: F821
    threads: Mapped[list["Thread"]] = relationship(  # noqa: F821
        back_populates="mailbox", cascade="all, delete-orphan"
    )