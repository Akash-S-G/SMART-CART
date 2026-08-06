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


class UserNotification(Base):
    __tablename__ = "user_notifications"

    id = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    user_id = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE")
    )

    title = mapped_column(String(255))

    message = mapped_column(Text)

    notification_type = mapped_column(String(50))

    is_read = mapped_column(Boolean, default=False)

    created_at = mapped_column(
        DateTime(timezone=True),
        server_default=func.now()
    )

    user = relationship(
        "User",
        back_populates="notifications"
    )