import os
import uuid
from pathlib import Path

from sqlalchemy.orm import Session
from tqdm import tqdm

# Adjust import paths as needed based on project structure
from app.db.session import SessionLocal
from app.models.products.product import Product
from app.models.products.categories import Category
from app.models.user.users import User
from app.auth.hashing import password_manager

# Configuration
NUM_PRODUCTS = 20000
NUM_USERS = 2000
DEFAULT_PASSWORD = "Password123!"

def create_categories(session: Session):
    categories = ["Produce", "Dairy", "Bakery", "Snacks", "Beverages", "Household", "Personal Care"]
    session.query(Category).delete()
    cat_objs = []
        cat = Category(name=name, description=f"Category for {name.lower()}")
        session.add(cat)
        cat_objs.append(cat)
    session.commit()
    return cat_objs

def seed_products(session: Session, categories):
    for i in tqdm(range(NUM_PRODUCTS), desc="Seeding products"):
        cat = categories[i % len(categories)]
        product = Product(
            name=f"Product {uuid.uuid4().hex[:8]}",
            sku=uuid.uuid4().hex[:12].upper(),
            barcode=None,
            description="Auto‑generated product for load testing",
            brand="TestBrand",
            category_id=cat.id,
            price=round(1.0 + 99.0 * (os.urandom(1)[0] / 255), 2),
            image_url=None,
            is_active=True,
            initial_stock=100,
        )
        session.add(product)
        if i % 1000 == 0:
            session.flush()
    session.commit()

def seed_users(session: Session):
    admin = User(
        email="admin@example.com",
        hashed_password=password_manager.hash_password(DEFAULT_PASSWORD),
        is_active=True,
        is_superuser=True,
        full_name="Admin User",
    )
    session.add(admin)
    for i in tqdm(range(1, NUM_USERS + 1), desc="Seeding users"):
        user = User(
            email=f"user{i}@example.com",
            hashed_password=get_password_hash(DEFAULT_PASSWORD),
            is_active=True,
            is_superuser=False,
            full_name=f"Test User {i}",
        )
        session.add(user)
        if i % 500 == 0:
            session.flush()
    session.commit()

def main():
    db: Session = SessionLocal()
    try:
        categories = create_categories(db)
        seed_products(db, categories)
        seed_users(db)
        print("✅ Integration test data seeded successfully.")
    finally:
        db.close()

if __name__ == "__main__":
    main()
