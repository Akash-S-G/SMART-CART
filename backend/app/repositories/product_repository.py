from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.models.products.product import Product
from app.models.products.categories import Category
from app.models.products.inventory import Inventory

class ProductRepository:
    """
    Repository for Product CRUD operations.
    """

    def __init__(self, db: Session):
        self.db = db

    # ==================================================
    # CREATE
    # ==================================================

    def create(
        self,
        product: Product,
    ) -> Product:

        self.db.add(product)
        self.db.commit()
        self.db.refresh(product)

        return product

    # ==================================================
    # READ
    # ==================================================

    def get_by_id(
        self,
        product_id: str,
    ) -> Product | None:

        stmt = (
            select(Product)
            .options(
            joinedload(Product.category),
            joinedload(Product.inventory),
            joinedload(Product.images),
            joinedload(Product.price),
        )
            .where(Product.id == str(product_id))
        )

        return self.db.execute(stmt).unique().scalar_one_or_none()

    def get_by_barcode(
        self,
        barcode: str,
    ) -> Product | None:

        stmt = (
            select(Product)
            .where(Product.barcode == barcode)
        )

        return self.db.scalar(stmt)

    def get_by_sku(
        self,
        sku: str,
    ) -> Product | None:

        stmt = (
            select(Product)
            .where(Product.sku == sku)
        )

        return self.db.scalar(stmt)

    def list_products(
        self,
        skip: int = 0,
        limit: int = 20,
        category_id: str | None = None,
        min_price: float | None = None,
        max_price: float | None = None,
        sort: str | None = None,
    ) -> list[Product]:

        from app.models.products.product_price import ProductPrice

        stmt = (
            select(Product)
            .options(
                joinedload(Product.category),
                joinedload(Product.inventory),
                joinedload(Product.images),
                joinedload(Product.price),
            )
        )

        if category_id:
            stmt = stmt.where(Product.category_id == category_id)

        if min_price is not None or max_price is not None:
            stmt = stmt.join(ProductPrice, ProductPrice.product_id == Product.id)
            if min_price is not None:
                stmt = stmt.where(ProductPrice.price >= min_price)
            if max_price is not None:
                stmt = stmt.where(ProductPrice.price <= max_price)

        if sort == "price_asc":
            stmt = stmt.join(ProductPrice, ProductPrice.product_id == Product.id).order_by(ProductPrice.price.asc())
        elif sort == "price_desc":
            stmt = stmt.join(ProductPrice, ProductPrice.product_id == Product.id).order_by(ProductPrice.price.desc())
        elif sort == "name_asc":
            stmt = stmt.order_by(Product.name.asc())
        elif sort == "rating_desc":
            # rating lives in metadata_ JSON; sort best-effort in Python if many rows,
            # but for pagination we approximate by created_at desc (newest first).
            stmt = stmt.order_by(Product.created_at.desc())

        stmt = stmt.offset(skip).limit(limit)

        return list(self.db.execute(stmt).unique().scalars().all())

    def search(
        self,
        keyword: str,
    ) -> list[Product]:

        stmt = (
            select(Product)
            .options(
                joinedload(Product.category),
                joinedload(Product.inventory),
                joinedload(Product.images),
                joinedload(Product.price),
            )
            .where(Product.name.ilike(f"%{keyword}%"))
        )

        return list(self.db.execute(stmt).unique().scalars().all())

    def get_by_category(
        self,
        category_id: str,
    ) -> list[Product]:

        stmt = (
            select(Product)
            .options(
                joinedload(Product.category),
                joinedload(Product.inventory),
                joinedload(Product.images),
                joinedload(Product.price),
            )
            .where(Product.category_id == category_id)
        )

        return list(self.db.execute(stmt).unique().scalars().all())

    # ==================================================
    # EXISTS
    # ==================================================

    def exists_by_barcode(
        self,
        barcode: str,
    ) -> bool:

        stmt = (
            select(Product.id)
            .where(Product.barcode == barcode)
        )

        return self.db.scalar(stmt) is not None

    def exists_by_sku(
        self,
        sku: str,
    ) -> bool:

        stmt = (
            select(Product.id)
            .where(Product.sku == sku)
        )

        return self.db.scalar(stmt) is not None

    # ==================================================
    # UPDATE
    # ==================================================

    def update(
        self,
        product: Product,
    ) -> Product:

        self.db.commit()
        self.db.refresh(product)

        return product

    # ==================================================
    # DELETE
    # ==================================================

    def delete(
        self,
        product: Product,
    ) -> None:

        self.db.delete(product)
        self.db.commit()

    # ==================================================
    # CATEGORY
    # ==================================================

    def get_category(
        self,
        category_id: str,
    ) -> Category | None:

        return self.db.get(Category, category_id)
    


    def initialize_inventory(
        self,
        product_id: str,
        quantity: int,
    ) -> Inventory:

        inventory = Inventory(
            product_id=product_id,
            quantity=quantity,
        )

        self.db.add(inventory)

        self.db.commit()

        self.db.refresh(inventory)

        return inventory



    def get_inventory(
        self,
        product_id: str,
    ) -> Inventory | None:

        stmt = (
            select(Inventory)
            .where(Inventory.product_id == product_id)
        )

        return self.db.scalar(stmt)

    def update_inventory(
        self,
        inventory: Inventory,
    ) -> Inventory:

        self.db.commit()

        self.db.refresh(inventory)

        return inventory

    def get_by_name(
        self,
        name: str,
    ) -> Product | None:

        stmt = (
            select(Product)
            .where(Product.name == name)
        )

        return self.db.scalar(stmt)

    def search_name(
        self,
        name: str,
    ) -> Product | None:

        stmt = (
            select(Product)
            .where(
                Product.name.ilike(
                    f"%{name}%"
                )
            )
        )

        return self.db.scalar(stmt)
