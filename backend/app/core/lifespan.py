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

    # Auto-create schema is disabled by default because it requires DB user privileges
    # (e.g., CREATE on schema). Enable only when the DB user is allowed to create tables.
    if settings.ENVIRONMENT == "development" and settings.DB_AUTO_CREATE:
        logger.info("Initializing database schema (create_all)...")
        try:
            init_db()
            logger.info("Database schema initialized.")
        except ProgrammingError as exc:
            # If the DB user doesn't have privileges to create tables, keep the app running.
            logger.error(
                "Database schema auto-create failed due to insufficient privileges. "
                "Continuing startup. Error=%s",
                exc,
            )
    else:
        logger.info(
            "Skipping database schema auto-create. "
            f"ENVIRONMENT={settings.ENVIRONMENT}, DB_AUTO_CREATE={settings.DB_AUTO_CREATE}"
        )

    yield

    logger.info("Stopping SmartCart...")

