from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import (
    String,
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    Text,
    Enum,
    func,
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

class UserSession(Base):
    __tablename__ = "user_sessions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE")
    )

    refresh_token: Mapped[str] = mapped_column(Text)

    ip_address: Mapped[str | None] = mapped_column(String(50))

    user_agent: Mapped[str | None] = mapped_column(Text)

    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))

    last_activity: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    is_revoked: Mapped[bool] = mapped_column(Boolean, default=False)

    user = relationship("User", back_populates="sessions")