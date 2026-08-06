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

class UserAddress(Base):
    __tablename__ = "user_addresses"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE")
    )

    address_type: Mapped[str] = mapped_column(
        String(20),
        default="home"
    )

    line1: Mapped[str] = mapped_column(String(255))

    line2: Mapped[str | None] = mapped_column(String(255))

    city: Mapped[str] = mapped_column(String(100))

    state: Mapped[str] = mapped_column(String(100))

    country: Mapped[str] = mapped_column(String(100))

    postal_code: Mapped[str] = mapped_column(String(20))

    is_default: Mapped[bool] = mapped_column(Boolean, default=False)

    user = relationship("User", back_populates="addresses")