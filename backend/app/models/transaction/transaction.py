import uuid
from enum import Enum

from sqlalchemy import (
    String,
    DateTime,
    Enum as SqlEnum,
    ForeignKey,
    Numeric,
    func,
)

from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class TransactionStatus(str, Enum):
    SUCCESS = "success"
    FAILED = "failed"
    PENDING = "pending"
    CANCELLED = "cancelled"


class Transaction(Base):
    __tablename__ = "transactions"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )

    payment_id: Mapped[str] = mapped_column(
        ForeignKey("payments.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    transaction_reference: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        nullable=False,
        index=True,
    )

    gateway_transaction_id: Mapped[str | None] = mapped_column(
        String(255)
    )

    status: Mapped[TransactionStatus] = mapped_column(
        SqlEnum(TransactionStatus),
        default=TransactionStatus.PENDING,
        nullable=False,
    )

    amount: Mapped[float] = mapped_column(
        Numeric(10,2),
        nullable=False
    )

    currency: Mapped[str] = mapped_column(
        String(3),
        default="INR"
    )

    gateway_response: Mapped[str | None] = mapped_column(
        String(1000)
    )

    processed_at: Mapped[DateTime | None] = mapped_column(
        DateTime(timezone=True)
    )

    created_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now()
    )
