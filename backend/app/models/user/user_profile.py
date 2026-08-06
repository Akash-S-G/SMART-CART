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

class UserProfile(Base):
    __tablename__ = "user_profiles"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True
    )

    first_name: Mapped[str | None] = mapped_column(String(100))
    last_name: Mapped[str | None] = mapped_column(String(100))

    phone_number: Mapped[str | None] = mapped_column(String(20))

    profile_image: Mapped[str | None] = mapped_column(Text)

    date_of_birth: Mapped[datetime | None] = mapped_column(DateTime)

    loyalty_points: Mapped[int] = mapped_column(Integer, default=0)

    total_orders: Mapped[int] = mapped_column(Integer, default=0)

    total_spent: Mapped[int] = mapped_column(Integer, default=0)

    user = relationship("User", back_populates="profile")