from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from app.models.payment.payment import Payment
from enum import Enum


class PaymentStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    PAID = "paid"
    FAILED = "failed"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"




class PaymentMethod(str, Enum):
    CASH = "cash"
    CARD = "card"
    UPI = "upi"
    NET_BANKING = "net_banking"
    WALLET = "wallet"
    RAZORPAY = "razorpay"
    STRIPE = "stripe"

class PaymentRepository:
    """
    Repository responsible for Payment persistence.
    """

    def __init__(self, db: Session):
        self.db = db

    # =====================================================
    # CREATE
    # =====================================================

    def create(
        self,
        payment: Payment,
    ) -> Payment:

        self.db.add(payment)
        self.db.commit()
        self.db.refresh(payment)

        return payment

    # =====================================================
    # READ
    # =====================================================

    def get_by_id(
        self,
        payment_id: str,
    ) -> Payment | None:

        return self.db.get(Payment, payment_id)

    def get_by_order(
        self,
        order_id: str,
    ) -> Payment | None:

        stmt = (
            select(Payment)
            .where(Payment.order_id == order_id)
        )

        return self.db.scalar(stmt)

    def get_by_transaction_id(
        self,
        transaction_id: str,
    ) -> Payment | None:

        stmt = (
            select(Payment)
            .where(
                Payment.transaction_id ==
                transaction_id
            )
        )

        return self.db.scalar(stmt)

    def list_user_payments(
        self,
        user_id: str,
        skip: int = 0,
        limit: int = 20,
    ) -> list[Payment]:

        stmt = (
            select(Payment)
            .options(
                joinedload(Payment.order)
            )
            .where(Payment.user_id == user_id)
            .order_by(Payment.created_at.desc())
            .offset(skip)
            .limit(limit)
        )

        return list(
            self.db.scalars(stmt).all()
        )

    # =====================================================
    # UPDATE
    # =====================================================

    def update(
        self,
        payment: Payment,
    ) -> Payment:

        self.db.commit()

        self.db.refresh(payment)

        return payment

    def update_status(
        self,
        payment: Payment,
        status: PaymentStatus,
    ) -> Payment:

        payment.status = status.value if hasattr(status, "value") else status

        self.db.commit()

        self.db.refresh(payment)

        return payment

    # =====================================================
    # DELETE
    # =====================================================

    def delete(
        self,
        payment: Payment,
    ) -> None:

        self.db.delete(payment)

        self.db.commit()

    # =====================================================
    # EXISTS
    # =====================================================

    def exists_transaction(
        self,
        transaction_id: str,
    ) -> bool:

        stmt = (
            select(Payment.id)
            .where(
                Payment.transaction_id ==
                transaction_id
            )
        )

        return self.db.scalar(stmt) is not None

    # =====================================================
    # STATISTICS
    # =====================================================

    def count_user_payments(
        self,
        user_id: str,
    ) -> int:

        stmt = (
            select(func.count(Payment.id))
            .where(
                Payment.user_id == user_id
            )
        )

        return self.db.scalar(stmt) or 0

    def total_paid(
        self,
        user_id: str,
    ):

        stmt = (
            select(func.sum(Payment.amount))
            .where(
                Payment.user_id == user_id,
                Payment.status == "paid",
            )
        )

        return self.db.scalar(stmt) or 0
