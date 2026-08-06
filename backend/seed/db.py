"""Database access: engine/session, category upserts, and table guard.

Uses the project's own models so seeded rows are 100% compatible with the
FastAPI app (products, product_prices, product_weights, inventory,
product_images) and the extra catalog attributes live in the products.metadata
JSON column.
"""

from __future__ import annotations

import os
from contextlib import contextmanager

from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

import config as cfg

# Make the project packages importable regardless of CWD.
import sys
BACKEND = cfg.BACKEND_ROOT
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

# Import every model package so the full SQLAlchemy mapper registry resolves
# (Product has relationships to CartItem/OrderItem referring to Cart/Order).
import app.models.products  # noqa: E402,F401
import app.models.user  # noqa: E402,F401
import app.models.payment  # noqa: E402,F401
import app.models.transaction  # noqa: E402,F401
import app.models.cart.cart_item  # noqa: E402,F401
import app.models.order.order_item  # noqa: E402,F401
import app.models.cart.cart  # noqa: E402,F401
import app.models.order.order  # noqa: E402,F401

from app.db.base import Base  # noqa: E402
from app.models.products.categories import Category  # noqa: E402
from app.models.products.product import Product  # noqa: E402
from app.models.products.product_image import ProductImage  # noqa: E402
from app.models.products.product_price import ProductPrice  # noqa: E402
from app.models.products.product_weight import ProductWeight  # noqa: E402
from app.models.products.inventory import Inventory  # noqa: E402


def _resolve_url() -> str:
    # Prefer the project's .env DATABASE_URL if present.
    url = cfg.ENV_DATABASE_URL
    if not url:
        # read .env ourselves (defensive)
        env_path = cfg.BACKEND_ROOT / ".env"
        if env_path.exists():
            for line in env_path.read_text().splitlines():
                line = line.strip()
                if line.startswith("DATABASE_URL"):
                    url = line.split("=", 1)[1].strip().strip('"').strip("'")
                    break
    if not url:
        raise RuntimeError("DATABASE_URL not found in env or .env")
    if url.startswith("postgresql://"):
        url = url.replace("postgresql://", "postgresql+psycopg://", 1)
    return url


ENGINE = create_engine(_resolve_url(), pool_pre_ping=True, future=True)
SessionLocal = sessionmaker(bind=ENGINE, autoflush=False, autocommit=False)


@contextmanager
def session_scope():
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def ensure_tables() -> None:
    """Create tables if they don't exist (mirrors DB_AUTO_CREATE behaviour)."""
    Base.metadata.create_all(ENGINE)


def get_or_create_category(db, name: str, description: str = "") -> Category:
    cat = db.execute(
        select(Category).where(Category.name == name)
    ).scalar_one_or_none()
    if cat is None:
        cat = Category(name=name, description=description or None)
        db.add(cat)
        db.flush()
    elif description and not cat.description:
        cat.description = description
    return cat


def existing_sku_set(db) -> set[str]:
    return set(db.execute(select(Product.sku)).scalars().all())


def existing_barcode_set(db) -> set[str]:
    rows = db.execute(select(Product.barcode)).scalars().all()
    return {b for b in rows if b}


def get_product_by_sku(db, sku: str) -> Product | None:
    return db.execute(
        select(Product).where(Product.sku == sku)
    ).scalar_one_or_none()


def get_product_by_barcode(db, barcode: str) -> Product | None:
    return db.execute(
        select(Product).where(Product.barcode == barcode)
    ).scalar_one_or_none()


def get_product_by_name(db, name: str) -> Product | None:
    return db.execute(
        select(Product).where(Product.name == name)
    ).scalars().first()


def count_products(db) -> int:
    return db.execute(select(Product.id)).scalars().all().__len__()


def reset_seeded(db) -> int:
    """Delete products seeded by this tool (provenance.seeded_by) and their
    child rows, plus any categories that become empty. Returns rows removed."""
    from app.models.products.product import Product
    from app.models.products.categories import Category
    from app.models.products.product_image import ProductImage
    from app.models.products.product_price import ProductPrice
    from app.models.products.product_weight import ProductWeight
    from app.models.products.inventory import Inventory
    from sqlalchemy import func, select

    prods = db.execute(select(Product)).scalars().all()
    to_delete = [p for p in prods
                 if isinstance(p.metadata_, dict)
                 and (p.metadata_ or {}).get("provenance", {}).get("seeded_by") == cfg.SEED_SOURCE_LABEL]
    ids = [p.id for p in to_delete]
    n = len(ids)
    if ids:
        # Remove child rows first (FK + unique constraints; no cascade defined).
        for Child in (ProductImage, ProductPrice, ProductWeight, Inventory):
            db.execute(
                Child.__table__.delete().where(Child.product_id.in_(ids))
            )
        for p in to_delete:
            db.delete(p)
        db.flush()
    # Sweep any orphaned child rows (product_id not present in products at all),
    # e.g. left behind by a pre-cascade-cleanup run.
    for Child in (ProductImage, ProductPrice, ProductWeight, Inventory):
        db.execute(
            Child.__table__.delete()
            .where(Child.product_id.notin_(select(Product.id)))
        )
    db.flush()
    # Remove now-empty seeder categories
    rows = db.execute(
        select(Category.id, func.count(Product.id))
        .join(Product, Product.category_id == Category.id, isouter=True)
        .group_by(Category.id)
    ).all()
    for cat_id, cnt in rows:
        if cnt == 0:
            cat = db.get(Category, cat_id)
            if cat:
                db.delete(cat)
    db.commit()
    return n


def category_counts(db) -> dict[str, int]:
    from sqlalchemy import func
    rows = db.execute(
        select(Category.name, func.count(Product.id))
        .join(Product, Product.category_id == Category.id)
        .group_by(Category.name)
    ).all()
    return {name: cnt for name, cnt in rows}
