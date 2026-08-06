from __future__ import annotations

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.auth.jwt import jwt_manager
from app.db.session import get_db

from app.models.user.users import User

from app.repositories.user_repository import UserRepository


oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/auth/login"
)


# ======================================================
# Current User
# ======================================================

def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:

    try:

        payload = jwt_manager.verify_token(token)

        user_id = payload["sub"]

    except Exception:

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials.",
        )

    repository = UserRepository(db)

    user = repository.get_active_user(user_id)

    if user is None:

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found.",
        )

    return user


# ======================================================
# Active User
# ======================================================

def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:

    if not current_user.is_active:

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user.",
        )

    return current_user


# ======================================================
# Admin User
# ======================================================

def get_current_admin(
    current_user: User = Depends(get_current_active_user),
) -> User:

    if current_user.role != "admin":

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required.",
        )

    return current_user


# ======================================================
# Optional User
# ======================================================

def get_optional_user(
    token: str | None = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User | None:

    if not token:
        return None

    try:

        payload = jwt_manager.verify_token(token)

        repository = UserRepository(db)

        return repository.get_active_user(
            payload["sub"]
        )

    except Exception:

        return None