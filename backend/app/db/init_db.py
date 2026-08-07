from __future__ import annotations

from sqlalchemy import text

from app.db.database import engine as default_engine
from app.db.base import Base


def init_db() -> None:
    try:
        with default_engine.connect() as conn:
            conn.execute(text("SELECT 1"))

        for table in Base.metadata.sorted_tables:
            table.create(bind=default_engine, checkfirst=True)
    except Exception as e:
        from app.core.logging import logger
        logger.warning(f"Database initialization warning: {e}")


