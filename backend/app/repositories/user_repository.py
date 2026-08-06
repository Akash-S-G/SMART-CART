from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.models.user.users import User
from app.models.user.user_profile import UserProfile
from app.models.user.user_preferences import UserPreference
from app.models.user.user_address import UserAddress


class UserRepository:
    """
    Repository responsible for User aggregate.

    Handles:
        - User
        - UserProfile
        - UserPreference
        - UserAddress

    Authentication session operations belong
    to SessionRepository.
    """

    def __init__(self, db: Session):
        self.db = db

    # ==================================================
    # USER
    # ==================================================

    def create_user(
        self,
        user: User,
    ) -> User:

        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)

        return user

    def create_user_with_profile(
        self,
        user: User,
        profile: UserProfile | None = None,
        preferences: UserPreference | None = None,
    ) -> User:
        """
        Creates the complete user aggregate in a single transaction.
        """

        try:
            self.db.add(user)
            self.db.flush()

            if profile:
                profile.user_id = user.id
                self.db.add(profile)

            if preferences:
                preferences.user_id = user.id
                self.db.add(preferences)

            self.db.commit()
            self.db.refresh(user)

            return user

        except Exception:
            self.db.rollback()
            raise

    def get_by_id(
        self,
        user_id: str,
    ) -> User | None:

        return self.db.get(User, user_id)

    def get_by_email(
        self,
        email: str,
    ) -> User | None:

        stmt = (
            select(User)
            .where(User.email == email)
        )

        return self.db.scalar(stmt)

    def get_by_username(
        self,
        username: str,
    ) -> User | None:

        stmt = (
            select(User)
            .where(User.username == username)
        )

        return self.db.scalar(stmt)

    def get_active_user(
        self,
        user_id: str,
    ) -> User | None:

        stmt = (
            select(User)
            .where(User.id == user_id)
            .where(User.is_active.is_(True))
        )

        return self.db.scalar(stmt)

    def exists_by_email(
        self,
        email: str,
    ) -> bool:

        stmt = (
            select(User.id)
            .where(User.email == email)
        )

        return self.db.scalar(stmt) is not None

    def exists_by_username(
        self,
        username: str,
    ) -> bool:

        stmt = (
            select(User.id)
            .where(User.username == username)
        )

        return self.db.scalar(stmt) is not None

    def update_user(
        self,
        user: User,
    ) -> User:

        self.db.commit()
        self.db.refresh(user)

        return user

    def delete_user(
        self,
        user: User,
    ) -> None:

        self.db.delete(user)
        self.db.commit()

    def update_password(
        self,
        user: User,
        hashed_password: str,
    ) -> None:

        user.password_hash = hashed_password

        self.db.commit()

    def update_last_login(
        self,
        user: User,
    ) -> None:

        user.last_login = datetime.now(timezone.utc)

        self.db.commit()

    # ==================================================
    # PROFILE
    # ==================================================

    def create_profile(
        self,
        profile: UserProfile,
    ) -> UserProfile:

        self.db.add(profile)
        self.db.commit()
        self.db.refresh(profile)

        return profile

    def get_profile(
        self,
        user_id: str,
    ) -> UserProfile | None:

        stmt = (
            select(UserProfile)
            .where(UserProfile.user_id == user_id)
        )

        return self.db.scalar(stmt)

    def update_profile(
        self,
        profile: UserProfile,
    ) -> UserProfile:

        self.db.commit()
        self.db.refresh(profile)

        return profile

    # ==================================================
    # PREFERENCES
    # ==================================================

    def create_preferences(
        self,
        preferences: UserPreference,
    ) -> UserPreference:

        self.db.add(preferences)
        self.db.commit()
        self.db.refresh(preferences)

        return preferences

    def get_preferences(
        self,
        user_id: str,
    ) -> UserPreference | None:

        stmt = (
            select(UserPreference)
            .where(UserPreference.user_id == user_id)
        )

        return self.db.scalar(stmt)

    def update_preferences(
        self,
        preferences: UserPreference,
    ) -> UserPreference:

        self.db.commit()
        self.db.refresh(preferences)

        return preferences

    # ==================================================
    # ADDRESS
    # ==================================================

    def add_address(
        self,
        address: UserAddress,
    ) -> UserAddress:

        self.db.add(address)
        self.db.commit()
        self.db.refresh(address)

        return address

    def get_addresses(
        self,
        user_id: str,
    ) -> list[UserAddress]:

        stmt = (
            select(UserAddress)
            .where(UserAddress.user_id == user_id)
        )

        return list(self.db.scalars(stmt).all())

    def delete_address(
        self,
        address: UserAddress,
    ) -> None:

        self.db.delete(address)
        self.db.commit()

    # ==================================================
    # AGGREGATE
    # ==================================================

    def get_complete_user(
        self,
        user_id: str,
    ) -> User | None:

        stmt = (
            select(User)
            .options(
                joinedload(User.profile),
                joinedload(User.preferences),
                joinedload(User.addresses),
            )
            .where(User.id == user_id)
        )

        return self.db.execute(stmt).unique().scalar_one_or_none()

    def update_user_and_profile(
        self,
        user: User,
        profile: UserProfile,
    ) -> User:

        try:
            self.db.commit()

            self.db.refresh(user)
            self.db.refresh(profile)

            return user

        except Exception:
            self.db.rollback()
            raise
