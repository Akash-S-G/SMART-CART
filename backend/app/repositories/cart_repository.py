from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.models.cart.cart import Cart
from app.models.cart.cart_item import CartItem
from app.repositories.product_repository import ProductRepository
from sqlalchemy import func

class CartRepository:

    def __init__(self, db: Session):

        self.db = db
        self.products = ProductRepository(db)

    # ====================================================
    # CART
    # ====================================================

    def create_cart(
        self,
        cart: Cart,
    ) -> Cart:

        self.db.add(cart)

        self.db.commit()

        self.db.refresh(cart)

        return cart

    def get_active_cart(
        self,
        user_id: str,
    ) -> Cart | None:

        stmt = (
            select(Cart)
            .options(
                joinedload(Cart.items)
            )
            .where(Cart.user_id == user_id)
        )

        return self.db.execute(stmt).unique().scalar_one_or_none()

    def update_cart(
        self,
        cart: Cart,
    ) -> Cart:

        self.db.commit()

        self.db.refresh(cart)

        return cart

    def clear_cart(
        self,
        cart: Cart,
    ) -> None:

        for item in cart.items:

            self.db.delete(item)

        self.db.commit()

    # ====================================================
    # CART ITEM
    # ====================================================

    def add_item(
        self,
        item: CartItem,
    ) -> CartItem:

        self.db.add(item)

        self.db.commit()

        self.db.refresh(item)

        return item

    def get_cart_item(
        self,
        cart_id: str,
        product_id: str,
    ) -> CartItem | None:

        stmt = (
            select(CartItem)
            .where(CartItem.cart_id == str(cart_id))
            .where(CartItem.product_id == str(product_id))
        )

        return self.db.scalar(stmt)

    def update_item(
        self,
        item: CartItem,
    ) -> CartItem:

        self.db.commit()

        self.db.refresh(item)

        return item

    def remove_item(
        self,
        item: CartItem,
    ) -> None:

        self.db.delete(item)

        self.db.commit()

    # ====================================================
    # CALCULATIONS
    # ====================================================

    def calculate_total(
        self,
        cart: Cart,
    ) -> float:

        total = 0.0

        for item in cart.items:

            total += (
                item.quantity *
                item.unit_price
            )

        return total
    
    def get_by_id(
        self,
        cart_id: str,
    ) -> Cart | None:

        stmt = (
            select(Cart)
            .options(
                joinedload(Cart.items)
            )
            .where(Cart.id == cart_id)
        )

        return self.db.execute(stmt).unique().scalar_one_or_none()

    def get_cart(
        self,
        user_id: str,
    ) -> Cart | None:

        return self.get_active_cart(user_id)



    def get_item_count(
        self,
        cart_id: str,
    ) -> int:

        stmt = (
            select(func.count(CartItem.id))
            .where(CartItem.cart_id == cart_id)
        )

        return self.db.scalar(stmt) or 0

    def get_items(
        self,
        cart_id: str,
    ) -> list[CartItem]:

        stmt = (
            select(CartItem)
            .where(CartItem.cart_id == cart_id)
        )

        return list(
            self.db.scalars(stmt).all()
        )

    def checkout_ready(
        self,
        user_id: str,
    ) -> bool:

        cart = self.get_cart(user_id)

        if cart is None:
            return False

        if len(cart.items) == 0:
            return False

        for item in cart.items:

            inventory = self.products.get_inventory(
                item.product_id
            )

            if inventory.quantity < item.quantity:
                return False

        return True

    def get_cart_summary(
        self,
        user_id: str,
    ) -> dict:

        cart = self.get_cart(user_id)

        if cart is None:
            return {
                "items": 0,
                "subtotal": 0,
                "discount": 0,
                "tax": 0,
                "total": 0,
            }

        return {
            "items": len(cart.items),
            "subtotal": cart.subtotal,
            "discount": cart.discount,
            "tax": cart.tax,
            "total": cart.total_amount,
        }
