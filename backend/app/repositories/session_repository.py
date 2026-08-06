from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.models.user.user_session import UserSession


class SessionRepository:

    def __init__(self, db: Session):
        self.db = db

    # -------------------------------------------------
    # Create
    # -------------------------------------------------

    def create(
        self,
        session: UserSession,
    ) -> UserSession:

        self.db.add(session)
        self.db.commit()
        self.db.refresh(session)

        return session

    # -------------------------------------------------
    # Read
    # -------------------------------------------------

    def get_by_id(
        self,
        session_id: str,
    ) -> UserSession | None:

        return self.db.get(UserSession, session_id)

    def get_by_refresh_token(
        self,
        refresh_token: str,
    ) -> UserSession | None:

        statement = (
            select(UserSession)
            .where(UserSession.refresh_token == refresh_token)
            .where(UserSession.is_revoked.is_(False))
        )

        return self.db.scalar(statement)

    def get_active_user_sessions(
        self,
        user_id: str,
    ) -> list[UserSession]:

        statement = (
            select(UserSession)
            .where(UserSession.user_id == user_id)
            .where(UserSession.is_revoked.is_(False))
        )

        return list(self.db.scalars(statement).all())

    # -------------------------------------------------
    # Update
    # -------------------------------------------------

    def update_last_activity(
        self,
        session: UserSession,
    ) -> None:

        session.last_activity = datetime.now(timezone.utc)

        self.db.commit()

    def revoke(
        self,
        session: UserSession,
    ) -> None:

        session.is_revoked = True

        self.db.commit()

    def revoke_all(
        self,
        user_id: str,
    ) -> None:

        statement = (
            select(UserSession)
            .where(UserSession.user_id == user_id)
            .where(UserSession.is_revoked.is_(False))
        )

        sessions = self.db.scalars(statement).all()

        for session in sessions:
            session.is_revoked = True

        self.db.commit()

    # -------------------------------------------------
    # Delete
    # -------------------------------------------------

    def delete(
        self,
        session: UserSession,
    ) -> None:

        self.db.delete(session)

        self.db.commit()

    def delete_expired_sessions(
        self,
    ) -> int:

        statement = (
            delete(UserSession)
            .where(
                UserSession.expires_at <
                datetime.now(timezone.utc)
            )
        )

        result = self.db.execute(statement)

        self.db.commit()

        return result.rowcount
    
    def update(
        self,
        session: UserSession,
    ) -> UserSession:

        self.db.commit()

        self.db.refresh(session)

        return session
    
def update(
    self,
    session: UserSession,
) -> UserSession:

    self.db.commit()
    self.db.refresh(session)

    return session


