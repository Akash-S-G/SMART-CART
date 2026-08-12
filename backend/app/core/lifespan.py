from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.core.logging import logger
from app.ai.model_loader import model_loader
from app.core.config import settings
from app.db.init_db import init_db

from sqlalchemy.exc import ProgrammingError

# Ensure all ORM models are imported so Base.metadata knows about all tables
import app.models.products  # noqa: F401
import app.models.user  # noqa: F401
import app.models.payment  # noqa: F401
import app.models.transaction  # noqa: F401
import app.models.cart  # noqa: F401
import app.models.order  # noqa: F401


@asynccontextmanager
async def lifespan(app: FastAPI):


    logger.info("Loading YOLO model...")
    model_loader.load()
    logger.info("YOLO loaded successfully.")

    # Seed a default admin account so the Admin Console is reachable out-of-the-box.
    try:
        from app.db.database import SessionLocal
        from app.core.seed import seed_default_admin

        db = SessionLocal()
        try:
            seed_default_admin(db)
            logger.info("Default admin seeded (if not present).")
        finally:
            db.close()
    except Exception as exc:  # noqa: BLE001
        logger.warning("Default admin seed skipped: %s", exc)

    # Auto-create schema is disabled by default because it requires DB user privileges
    # (e.g., CREATE on schema). Enable only when the DB user is allowed to create tables.
    if settings.ENVIRONMENT == "development" and settings.DB_AUTO_CREATE:
        logger.info("Initializing database schema (create_all)...")
        try:
            init_db()
            logger.info("Database schema initialized.")
        except Exception as exc:
            logger.warning(
                "Database schema initialization warning (continuing server startup): %s",
                exc,
            )
    else:
        logger.info(
            "Skipping database schema auto-create. "
            f"ENVIRONMENT={settings.ENVIRONMENT}, DB_AUTO_CREATE={settings.DB_AUTO_CREATE}"
        )

    yield

    logger.info("Stopping SmartCart...")

