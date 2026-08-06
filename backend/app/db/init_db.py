from __future__ import annotations

from sqlalchemy import text

from app.db.database import engine as default_engine
from app.db.base import Base


def init_db() -> None:
    # Basic connectivity check (fails fast if DATABASE_URL is wrong)
    with default_engine.connect() as conn:
        conn.execute(text("SELECT 1"))

    # Create tables individually to avoid bulk DDL issues.
    # Requires DB user privileges for the target schema, but is idempotent via checkfirst=True.
    for table in Base.metadata.sorted_tables:
        table.create(bind=default_engine, checkfirst=True)


