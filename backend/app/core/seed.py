"""Ensure the default admin account is reachable out-of-the-box.

The known credentials are read from settings:
  DEFAULT_ADMIN_USERNAME / DEFAULT_ADMIN_EMAIL / DEFAULT_ADMIN_PASSWORD

Idempotent: if a user already owns the default username or email, it is
promoted to admin and its password/email are aligned to the defaults so the
documented login always works.
"""
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth.hashing import password_manager
from app.core.config import settings
from app.models.user.users import User
from app.models.user.user_profile import UserProfile
from app.models.user.user_preferences import UserPreference


def seed_default_admin(db: Session) -> None:
    existing = db.execute(
        select(User).where(
            (User.username == settings.DEFAULT_ADMIN_USERNAME)
            | (User.email == settings.DEFAULT_ADMIN_EMAIL)
        )
    ).scalar_one_or_none()

    if existing is not None:
        changed = False
        if existing.role != "admin":
            existing.role = "admin"
            changed = True
        if existing.email != settings.DEFAULT_ADMIN_EMAIL:
            existing.email = settings.DEFAULT_ADMIN_EMAIL
            changed = True
        # Align password so the documented default credentials always work.
        if not password_manager.verify_password(
            settings.DEFAULT_ADMIN_PASSWORD, existing.password_hash
        ):
            existing.password_hash = password_manager.hash_password(
                settings.DEFAULT_ADMIN_PASSWORD
            )
            changed = True
        if changed:
            db.commit()
        return

    admin = User(
        username=settings.DEFAULT_ADMIN_USERNAME,
        email=settings.DEFAULT_ADMIN_EMAIL,
        password_hash=password_manager.hash_password(settings.DEFAULT_ADMIN_PASSWORD),
        role="admin",
        is_active=True,
    )
    db.add(admin)
    db.flush()
    db.add(UserProfile(user_id=admin.id))
    db.add(UserPreference(user_id=admin.id))
    db.commit()
