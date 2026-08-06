from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.payment.payment import Payment
from app.models.payment.payment import PaymentStatus

from app.repositories.order_repository import OrderRepository
from app.repositories.payment_repository import PaymentRepository


class PaymentService:

    def __init__(self, db: Session):

        self.db = db

        self.orders = OrderRepository(db)

        self.payments = PaymentRepository(db)

    # =====================================================
    # CREATE PAYMENT
    # =====================================================

    def create_payment(
        self,
        order_id: str,
        payment_method: str,
    ) -> Payment:

        order = self.orders.get_by_id(order_id)

        if order is None:
            raise ValueError(
                "Order not found."
            )

        existing = self.payments.get_by_order(
            order_id
        )

        if existing:
            raise ValueError(
                "Payment already exists."
            )

        payment = Payment(

            order_id=order.id,

            user_id=order.user_id,

            transaction_id=str(uuid.uuid4()),

            gateway_reference=None,

            amount=order.total_amount,

            payment_method=payment_method,

            status=PaymentStatus.PENDING,

            created_at=datetime.now(
                timezone.utc
            ),
        )

        return self.payments.create(
            payment
        )

    # =====================================================
    # VERIFY PAYMENT
    # =====================================================

    def verify_payment(
        self,
        transaction_id: str,
    ) -> Payment:

        payment = self.payments.get_by_transaction_id(
            transaction_id
        )

        if payment is None:

            raise ValueError(
                "Payment not found."
            )

        payment.status = PaymentStatus.PAID

        self.payments.update(payment)

        order = self.orders.get_by_id(
            payment.order_id
        )

        if order is None:
            raise ValueError("Order not found.")

        order.status = "paid"

        self.orders.update_order(order)

        return payment

    # =====================================================
    # FAIL PAYMENT
    # =====================================================

    def fail_payment(
        self,
        transaction_id: str,
    ) -> Payment:

        payment = self.payments.get_by_transaction_id(
            transaction_id
        )

        if payment is None:

            raise ValueError(
                "Payment not found."
            )

        payment.status = PaymentStatus.FAILED

        return self.payments.update(
            payment
        )

    # =====================================================
    # REFUND
    # =====================================================

    def refund(
        self,
        payment_id: str,
    ) -> Payment:

        payment = self.payments.get_by_id(
            payment_id
        )

        if payment is None:

            raise ValueError(
                "Payment not found."
            )

        payment.status = PaymentStatus.REFUNDED

        self.payments.update(
            payment
        )

        order = self.orders.get_by_id(
            payment.order_id
        )

        if order is None:
            raise ValueError("Order not found.")

        order.status = "refunded"

        self.orders.update_order(
            order
        )

        return payment

    # =====================================================
    # GET PAYMENT
    # =====================================================

    def get_payment(
        self,
        payment_id: str,
    ) -> Payment:

        payment = self.payments.get_by_id(
            payment_id
        )

        if payment is None:

            raise ValueError(
                "Payment not found."
            )

        return payment

    # =====================================================
    # USER PAYMENTS
    # =====================================================

    def list_user_payments(
        self,
        user_id: str,
        page: int = 1,
        page_size: int = 20,
    ):

        skip = (page - 1) * page_size

        payments = self.payments.list_user_payments(
            user_id=user_id,
            skip=skip,
            limit=page_size,
        )

        total = self.payments.count_user_payments(
            user_id
        )

        total_pages = (
            total + page_size - 1
        ) // page_size

        return {
            "items": payments,
            "page": page,
            "page_size": page_size,
            "total_items": total,
            "total_pages": total_pages,
        }
