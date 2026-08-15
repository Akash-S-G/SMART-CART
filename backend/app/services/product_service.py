from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.products.product import Product
from app.models.products.inventory import Inventory

from app.repositories.product_repository import ProductRepository

from app.schemas.product import (
    ProductCreate,
    ProductUpdate,
)


class ProductService:

    def __init__(self, db: Session):

        self.db = db

        self.products = ProductRepository(db)

    # =====================================================
    # CREATE PRODUCT
    # =====================================================

    def create_product(
        self,
        request: ProductCreate,
    ) -> Product:

        if self.products.exists_by_sku(request.sku):
            raise ValueError(
                "SKU already exists."
            )

        if request.barcode and self.products.exists_by_barcode(
            request.barcode
        ):
            raise ValueError(
                "Barcode already exists."
            )

        category = self.products.get_category(
            request.category_id
        )

        if category is None:
            raise ValueError(
                "Category not found."
            )

        product = Product(
            name=request.name,
            sku=request.sku,
            barcode=request.barcode,
            description=request.description,
            brand=request.brand,
            category_id=request.category_id,
            is_active=True,
        )

        product = self.products.create(product)

        inventory = Inventory(
            product_id=product.id,
            quantity=request.initial_stock,
        )
        self.db.add(inventory)

        from app.models.products.product_price import ProductPrice
        from app.models.products.product_image import ProductImage
        from app.services.cloudinary_service import cloudinary_service

        price_row = ProductPrice(
            product_id=product.id,
            price=request.price,
        )
        self.db.add(price_row)

        if request.image_url:
            image_url = request.image_url
            if cloudinary_service.is_configured:
                cloud_url = cloudinary_service.upload_url(image_url, folder=f"products/{product.sku}")
                if cloud_url:
                    image_url = cloud_url

            image_row = ProductImage(
                product_id=product.id,
                image_url=image_url
            )
            self.db.add(image_row)

        self.db.commit()
        self.db.refresh(product)

        return product

    # =====================================================
    # GET PRODUCT
    # =====================================================

    def get_product(
        self,
        product_id: str,
    ) -> Product:

        product = self.products.get_by_id(
            product_id
        )

        if product is None:
            raise ValueError(
                "Product not found."
            )

        return product

    # =====================================================
    # LIST PRODUCTS
    # =====================================================

    def list_products(
        self,
        skip: int = 0,
        limit: int = 20,
        category_id: str | None = None,
        min_price: float | None = None,
        max_price: float | None = None,
        sort: str | None = None,
    ):

        return self.products.list_products(
            skip=skip,
            limit=limit,
            category_id=category_id,
            min_price=min_price,
            max_price=max_price,
            sort=sort,
        )

    # =====================================================
    # SEARCH
    # =====================================================

    def search_products(
        self,
        keyword: str,
    ):

        return self.products.search(keyword)

    # =====================================================
    # UPDATE
    # =====================================================

    def update_product(
        self,
        product_id: str,
        request: ProductUpdate,
    ) -> Product:

        product = self.products.get_by_id(
            product_id
        )

        if product is None:
            raise ValueError(
                "Product not found."
            )

        if request.name is not None:
            product.name = request.name

        if request.description is not None:
            product.description = request.description

        if request.brand is not None:
            product.brand = request.brand

        if request.barcode is not None:
            if request.barcode and self.products.exists_by_barcode(request.barcode):
                existing = self.products.get_by_barcode(request.barcode)
                if existing and existing.id != product.id:
                    raise ValueError("Barcode already exists.")
            product.barcode = request.barcode or None

        if request.is_active is not None:
            product.is_active = request.is_active

        if request.category_id is not None:

            category = self.products.get_category(
                request.category_id
            )

            if category is None:
                raise ValueError(
                    "Category not found."
                )

            product.category_id = request.category_id

        # Price
        if request.price is not None:
            from app.models.products.product_price import ProductPrice
            price_row = self.db.query(ProductPrice).filter(
                ProductPrice.product_id == product.id
            ).first()
            if price_row is None:
                price_row = ProductPrice(product_id=product.id, price=request.price, currency="INR")
                self.db.add(price_row)
            else:
                price_row.price = request.price

        # Stock (inventory)
        if request.stock is not None:
            from app.models.products.inventory import Inventory
            inv = self.db.query(Inventory).filter(
                Inventory.product_id == product.id
            ).first()
            if inv is None:
                inv = Inventory(product_id=product.id, quantity=request.stock)
                self.db.add(inv)
            else:
                inv.quantity = request.stock

        # Image replacement — client sends an already-uploaded URL
        # (via POST /products/upload-image), keeps the existing one, or sends "" to delete.
        if request.image_url is not None:
            from app.models.products.product_image import ProductImage
            if not request.image_url.strip():
                self.db.query(ProductImage).filter(
                    ProductImage.product_id == product.id
                ).delete()
                if product.metadata_ and "images" in product.metadata_:
                    meta = dict(product.metadata_)
                    meta.pop("images", None)
                    product.metadata_ = meta
            else:
                img_row = self.db.query(ProductImage).filter(
                    ProductImage.product_id == product.id
                ).first()
                if img_row is None:
                    img_row = ProductImage(product_id=product.id, image_url=request.image_url.strip())
                    self.db.add(img_row)
                else:
                    img_row.image_url = request.image_url.strip()

        self.db.commit()
        self.db.refresh(product)

        return product

    # =====================================================
    # DELETE
    # =====================================================

    def delete_product(
        self,
        product_id: str,
    ) -> None:

        product = self.products.get_by_id(
            product_id
        )

        if product is None:
            raise ValueError(
                "Product not found."
            )

        self.products.delete(product)