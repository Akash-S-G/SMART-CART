from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.db.session import get_db

router = APIRouter(tags=["Health"])

@router.get("/healthz")
def healthz():
    """Liveness probe to confirm backend is running."""
    return {"status": "ok", "service": "SmartCart AI Backend"}

@router.get("/readyz")
def readyz(db: Session = Depends(get_db)):
    """Readiness probe to confirm DB connection and app dependencies are ready."""
    try:
        db.execute(text("SELECT 1"))
        return {"status": "ready", "database": "connected"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Database connection error: {str(e)}"
        )
