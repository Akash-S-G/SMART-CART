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
class UserPreference(Base):
    __tablename__ = "user_preferences"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True
    )

    theme: Mapped[str] = mapped_column(String(20), default="light")

    language: Mapped[str] = mapped_column(String(20), default="en")

    notifications_enabled: Mapped[bool] = mapped_column(Boolean, default=True)

    preferences: Mapped[dict | None] = mapped_column(JSONB)

    user = relationship("User", back_populates="preferences")