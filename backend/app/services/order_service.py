from __future__ import annotations

from datetime import datetime
import uuid

from sqlalchemy.orm import Session

from app.models.order.order import Order
from app.models.order.order_item import OrderItem

from app.repositories.cart_repository import CartRepository
from app.repositories.inventory_repository import InventoryRepository
from app.repositories.order_repository import OrderRepository
from app.repositories.product_repository import ProductRepository
from app.schemas.order import OrderStatus

class OrderService:

    def __init__(self, db: Session):

        self.db = db

        self.orders = OrderRepository(db)

        self.carts = CartRepository(db)

        self.inventory = InventoryRepository(db)

        self.products = ProductRepository(db)



    def checkout(
        self,
        user_id: str,
    ) -> Order:

        cart = self.carts.get_active_cart(user_id)

        if cart is None:
            raise ValueError(
                "Cart not found."
            )

        if len(cart.items) == 0:
            raise ValueError(
                "Cart is empty."
            )

        subtotal = 0

        for item in cart.items:

            if not self.inventory.has_stock(
                item.product_id,
                item.quantity,
            ):
                raise ValueError(
                    "Insufficient inventory."
                )

            subtotal += item.total_price

        
        order = Order(

            user_id=user_id,

            order_number=str(uuid.uuid4())[:12],

            subtotal=subtotal,

            discount=0,

            tax=0,

            total_amount=subtotal,

            status="pending",

            created_at=datetime.utcnow(),
        )

        order = self.orders.create_order(order)

        for item in cart.items:

            order_item = OrderItem(

                order_id=order.id,

                product_id=item.product_id,

                product_name=item.product.name,

                sku=item.product.sku,

                quantity=item.quantity,

                unit_price=item.unit_price,

                total_price=item.total_price,
            )

            self.orders.create_order_item(
                order_item
            )

        for item in cart.items:

            self.inventory.reduce_stock(

                product_id=item.product_id,

                quantity=item.quantity,
            )

        self.carts.clear_cart(cart)

        return order

    def get_order(
        self,
        user_id: str,
        order_id: str,
        is_admin: bool = False,
    ) -> Order:

        if is_admin:
            order = self.orders.get_by_id(order_id)
        else:
            order = self.orders.get_user_order(
                user_id,
                order_id,
            )

        if order is None:
            raise ValueError(
                "Order not found."
            )

        return order
        
    def cancel_order(
        self,
        user_id: str,
        order_id: str,
        is_admin: bool = False,
    ):

        order = self.get_order(
            user_id=user_id,
            order_id=order_id,
            is_admin=is_admin,
        )

        if order.status != "pending":
            raise ValueError(
                "Only pending orders can be cancelled."
            )

        for item in order.items:

            self.inventory.increase_stock(
                item.product_id,
                item.quantity,
            )

        order.status = "cancelled"

        return self.orders.update_order(order)


    def update_status(
        self,
        order_id: str,
        status: OrderStatus,
    ):

        order = self.orders.get_by_id(
            order_id
        )

        if order is None:
            raise ValueError(
                "Order not found."
            )

        return self.orders.update_status(
            order,
            status.value,
        )

    def list_orders(
        self,
        user_id: str,
        page: int = 1,
        page_size: int = 20,
    ):

        skip = (page - 1) * page_size

        orders = self.orders.list_user_orders(
            user_id,
            skip,
            page_size,
        )

        total = self.orders.count_user_orders(user_id)

        total_pages = (total + page_size - 1) // page_size

        return {
            "items": orders,
            "page": page,
            "page_size": page_size,
            "total_items": total,
            "total_pages": total_pages,
        }
