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


class UserDevice(Base):
    __tablename__ = "user_devices"

    id = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    user_id = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE")
    )

    device_name = mapped_column(String(100))

    device_type = mapped_column(String(50))

    operating_system = mapped_column(String(50))

    browser = mapped_column(String(50))

    device_identifier = mapped_column(
        String(255),
        unique=True
    )

    trusted = mapped_column(Boolean, default=False)

    last_seen = mapped_column(DateTime(timezone=True))

    user = relationship("User", back_populates="devices")