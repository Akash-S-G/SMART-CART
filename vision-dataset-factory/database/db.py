from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from contextlib import contextmanager

Base = declarative_base()

def get_engine(db_path: str):
    """Creates a SQLAlchemy engine for SQLite."""
    # Ensure parent directories exist
    import os
    os.makedirs(os.path.dirname(os.path.abspath(db_path)), exist_ok=True)
    
    # Connect to local SQLite DB
    db_url = f"sqlite:///{db_path}"
    return create_engine(
        db_url,
        connect_args={"check_same_thread": False} # Needed for sqlite in async environment
    )

def init_db(db_path: str):
    """Creates all database tables in the SQLite database if they do not exist."""
    engine = get_engine(db_path)
    # Import models here to ensure they register on Base
    from . import models
    Base.metadata.create_all(bind=engine)

@contextmanager
def get_db_session(db_path: str):
    """Context manager for scoped database sessions."""
    engine = get_engine(db_path)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
