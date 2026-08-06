from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.models.order.order import Order
from app.models.order.order_item import OrderItem
from sqlalchemy import func

class OrderRepository:

    def __init__(self, db: Session):
        self.db = db

    # =====================================================
    # ORDER
    # ======================================def count_user_orders(
    

    def count_user_orders(
            self,
            user_id: str,
        ) -> int:

            stmt = (
                select(func.count(Order.id))
                .where(Order.user_id == user_id)
            )

            return self.db.scalar(stmt) or 0

    def create_order(
        self,
        order: Order,
    ) -> Order:

        self.db.add(order)
        self.db.commit()
        self.db.refresh(order)

        return order

    def get_by_id(
        self,
        order_id: str,
    ) -> Order | None:

        stmt = (
            select(Order)
            .options(
                joinedload(Order.items)
            )
            .where(Order.id == order_id)
        )

        return self.db.execute(stmt).unique().scalar_one_or_none()

    def get_by_order_number(
        self,
        order_number: str,
    ) -> Order | None:

        stmt = (
            select(Order)
            .where(
                Order.order_number == order_number
            )
        )

        return self.db.scalar(stmt)

    def list_user_orders(
        self,
        user_id: str,
        skip: int = 0,
        limit: int = 20,
    ) -> list[Order]:

        stmt = (
            select(Order)
            .where(Order.user_id == user_id)
            .order_by(Order.created_at.desc())
            .offset(skip)
            .limit(limit)
        )

        return list(
            self.db.scalars(stmt).all()
        )

    def update_order(
        self,
        order: Order,
    ) -> Order:

        self.db.commit()

        self.db.refresh(order)

        return order

    def delete_order(
        self,
        order: Order,
    ) -> None:

        self.db.delete(order)

        self.db.commit()

    # =====================================================
    # ORDER ITEMS
    # =====================================================

    def create_order_item(
        self,
        item: OrderItem,
    ) -> OrderItem:

        self.db.add(item)

        self.db.commit()

        self.db.refresh(item)

        return item

    def get_order_items(
        self,
        order_id: str,
    ) -> list[OrderItem]:

        stmt = (
            select(OrderItem)
            .where(
                OrderItem.order_id == order_id
            )
        )

        return list(
            self.db.scalars(stmt).all()
        )

    # =====================================================
    # STATUS
    # =====================================================

    def update_status(
        self,
        order: Order,
        status: str,
    ) -> Order:

        order.status = status

        self.db.commit()

        self.db.refresh(order)

        return order

    # =====================================================
    # EXISTENCE
    # =====================================================

    def exists(
        self,
        order_id: str,
    ) -> bool:

        stmt = (
            select(Order.id)
            .where(Order.id == order_id)
        )

        return self.db.scalar(stmt) is not None

    # =====================================================
    # STATISTICS
    # =====================================================

    # def count_user_orders(
    #     self,
    #     user_id: str,
    # ) -> int:

    #     stmt = (
    #         select(Order.id)
    #         .where(Order.user_id == user_id)
    #     )

    #     return len(
    #         list(
    #             self.db.scalars(stmt).all()
    #         )
    #     )
    
    def count_user_orders(
        self,
        user_id: str,
    ) -> int:

        stmt = (
            select(func.count(Order.id))
            .where(Order.user_id == user_id)
        )

        return self.db.scalar(stmt) or 0
