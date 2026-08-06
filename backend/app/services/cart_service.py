from __future__ import annotations

from decimal import Decimal

from sqlalchemy.orm import Session

from app.models.cart.cart import Cart
from app.models.cart.cart_item import CartItem

from app.repositories.cart_repository import CartRepository
from app.repositories.product_repository import ProductRepository


class CartService:

    def __init__(self, db: Session):

        self.db = db

        self.carts = CartRepository(db)

        self.products = ProductRepository(db)

    # ==========================================================
    # GET OR CREATE CART
    # ==========================================================

    def get_or_create_cart(
        self,
        user_id: str,
    ) -> Cart:

        cart = self.carts.get_active_cart(user_id)

        if cart:

            return cart

        cart = Cart(
            user_id=user_id,
        )

        return self.carts.create_cart(cart)

    # ==========================================================
    # ADD PRODUCT
    # ==========================================================

    def add_product(
        self,
        user_id: str,
        product_id: str,
        quantity: int = 1,
    ) -> Cart:

        if quantity <= 0:
            raise ValueError(
                "Quantity must be greater than zero."
            )

        cart = self.get_or_create_cart(user_id)

        product = self.products.get_by_id(product_id)

        if product is None:
            raise ValueError(
                "Product not found."
            )

        if not product.is_active:
            raise ValueError(
                "Product is inactive."
            )

        if product.price is None:
            raise ValueError(
                "Product price not found."
            )

        # Inventory validation

        if product.inventory.quantity < quantity:
            raise ValueError(
                "Insufficient inventory."
            )

        item = self.carts.get_cart_item(
            cart.id,
            product.id,
        )

        if item:

            if (
                item.quantity + quantity >
                product.inventory.quantity
            ):
                raise ValueError(
                    "Insufficient inventory."
                )

            item.quantity += quantity

            self.carts.update_item(item)

        else:

            total_price = product.price.price * quantity

            item = CartItem(
                cart_id=cart.id,
                product_id=product.id,
                quantity=quantity,
                unit_price=product.price.price,
                total_price=total_price,
            )

            self.carts.add_item(item)

        return self.recalculate(cart.id)

    # ==========================================================
    # REMOVE PRODUCT
    # ==========================================================

    def remove_product(
        self,
        user_id: str,
        product_id: str,
    ) -> Cart:

        cart = self.get_or_create_cart(user_id)

        item = self.carts.get_cart_item(
            cart.id,
            product_id,
        )

        if item is None:
            raise ValueError(
                "Product not in cart."
            )

        self.carts.remove_item(item)

        return self.recalculate(cart.id)

    # ==========================================================
    # UPDATE QUANTITY
    # ==========================================================

    def update_quantity(
        self,
        user_id: str,
        product_id: str,
        quantity: int,
    ) -> Cart:

        if quantity <= 0:
            raise ValueError(
                "Quantity must be positive."
            )

        cart = self.get_or_create_cart(user_id)

        item = self.carts.get_cart_item(
            cart.id,
            product_id,
        )

        if item is None:
            raise ValueError(
                "Item not found."
            )

        product = self.products.get_by_id(product_id)

        if quantity > product.inventory.quantity:
            raise ValueError(
                "Insufficient inventory."
            )

        item.quantity = quantity

        self.carts.update_item(item)

        return self.recalculate(cart.id)

    # ==========================================================
    # CLEAR CART
    # ==========================================================

    def clear_cart(
        self,
        user_id: str,
    ) -> None:

        cart = self.get_or_create_cart(user_id)

        self.carts.clear_cart(cart)

    # ==========================================================
    # GET CART
    # ==========================================================

    def get_cart(
        self,
        user_id: str,
    ) -> Cart:

        cart = self.get_or_create_cart(user_id)

        return self.recalculate(cart.id)

    # ==========================================================
    # RECALCULATE
    # ==========================================================

    def recalculate(
        self,
        cart_id: str,
    ) -> Cart:

        cart = self.carts.get_by_id(cart_id)

        subtotal = Decimal("0.00")

        for item in cart.items:

            item.total_price = (
                Decimal(item.unit_price)
                * item.quantity
            )

            subtotal += item.total_price

        cart.subtotal = subtotal

        cart.discount = Decimal("0.00")

        cart.tax = Decimal("0.00")

        cart.total_amount = (
            subtotal
            - cart.discount
            + cart.tax
        )

        self.carts.update_cart(cart)

        return cart
