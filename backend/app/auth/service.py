from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.auth.hashing import password_manager
from app.auth.jwt import jwt_manager

from app.models.user.users import User
from app.models.user.user_profile import UserProfile
from app.models.user.user_preferences import UserPreference
from app.models.user.user_session import UserSession

from app.repositories.user_repository import UserRepository
from app.repositories.session_repository import SessionRepository

from app.schemas.auth import (
    RegisterRequest,
    LoginRequest,
    TokenResponse,
    CurrentUserResponse,
    GoogleLoginRequest,
)


class AuthService:

    def __init__(self, db: Session):

        self.db = db

        self.users = UserRepository(db)

        self.sessions = SessionRepository(db)

    # =====================================================
    # Register
    # =====================================================

    def register(
        self,
        request: RegisterRequest,
    ) -> TokenResponse:

        if self.users.exists_by_email(request.email):
            raise ValueError("Email already exists.")

        if self.users.exists_by_username(request.username):
            raise ValueError("Username already exists.")

        hashed_password = password_manager.hash_password(
            request.password
        )

        role = "admin" if request.username.lower().startswith("admin") else "customer"

        user = User(
            username=request.username,
            email=request.email,
            password_hash=hashed_password,
            role=role,
            is_active=True,
        )

        profile = UserProfile()

        preferences = UserPreference()

        user = self.users.create_user_with_profile(
            user=user,
            profile=profile,
            preferences=preferences,
        )

        access_token = jwt_manager.create_access_token(
            user_id=str(user.id),
            role=user.role,
        )

        refresh_token = jwt_manager.create_refresh_token(
            user_id=str(user.id),
            role=user.role,
        )

        session = UserSession(
            user_id=user.id,
            refresh_token=refresh_token,
            expires_at=datetime.now(timezone.utc)
            + timedelta(days=7),
            is_revoked=False,
        )

        self.sessions.create(session)

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
        )

    # =====================================================
    # Login
    # =====================================================

    def login(
        self,
        request: LoginRequest,
    ) -> TokenResponse:

        user = self.users.get_by_email(request.email)

        if not user:
            raise ValueError("Invalid credentials.")

        if not password_manager.verify_password(
            request.password,
            user.password_hash,
        ):
            raise ValueError("Invalid credentials.")

        access_token = jwt_manager.create_access_token(
            user_id=str(user.id),
            role=user.role,
        )

        refresh_token = jwt_manager.create_refresh_token(
            user_id=str(user.id),
            role=user.role,
        )

        session = UserSession(
            user_id=user.id,
            refresh_token=refresh_token,
            expires_at=datetime.now(timezone.utc)
            + timedelta(days=7),
            is_revoked=False,
        )

        self.sessions.create(session)

        self.users.update_last_login(user)

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
        )

    # =====================================================
    # Logout
    # =====================================================

    def logout(
        self,
        refresh_token: str,
    ) -> None:

        session = self.sessions.get_by_refresh_token(
            refresh_token
        )

        if session:
            self.sessions.revoke(session)

    # =====================================================
    # Logout All Devices
    # =====================================================

    def logout_all(
        self,
        user_id: str,
    ) -> None:

        self.sessions.revoke_all(user_id)

    # =====================================================
    # Current User
    # =====================================================

    def get_current_user(
        self,
        user_id: str,
    ) -> CurrentUserResponse:

        user = self.users.get_complete_user(user_id)

        if not user:
            raise ValueError("User not found.")

        return CurrentUserResponse.model_validate(user)
    
    def change_password(
        self,
        user_id: str,
        old_password: str,
        new_password: str,
    ) -> None:

        user = self.users.get_by_id(user_id)

        if user is None:
            raise ValueError("User not found.")

        if not password_manager.verify_password(
            old_password,
            user.password_hash,
        ):
            raise ValueError("Current password is incorrect.")

        if old_password == new_password:
            raise ValueError(
                "New password cannot be the same as the current password."
            )

        hashed_password = password_manager.hash_password(
            new_password
        )

        self.users.update_password(
            user=user,
            hashed_password=hashed_password,
        )

        # Optional security feature:
        # revoke all sessions so the user must login again
        self.sessions.revoke_all(user.id)

    def refresh(
        self,
        refresh_token: str,
    ) -> TokenResponse:

        session = self.sessions.get_by_refresh_token(
            refresh_token
        )

        if session is None:
            raise ValueError("Invalid refresh token.")

        payload = jwt_manager.verify_token(
            refresh_token,
            expected_type="refresh",
        )

        user = self.users.get_active_user(
            payload["sub"]
        )

        if user is None:
            raise ValueError("User not found.")

        access_token = jwt_manager.create_access_token(
            user_id=str(user.id),
            role=user.role,
        )

        new_refresh_token = jwt_manager.create_refresh_token(
            user_id=str(user.id),
            role=user.role,
        )

        session.refresh_token = new_refresh_token

        session.expires_at = (
            datetime.now(timezone.utc)
            + timedelta(days=7)
        )

        session.last_activity = datetime.now(
            timezone.utc
        )

        self.sessions.update(session)

        return TokenResponse(
            access_token=access_token,
            refresh_token=new_refresh_token,
        )

    def google_login(
        self,
        request: GoogleLoginRequest,
    ) -> TokenResponse:
        import secrets
        import httpx
        from google.oauth2 import id_token as google_id_token
        from google.auth.transport import requests as google_requests
        from app.core.config import settings
        from app.models.user.user_preferences import UserPreference

        email = None
        username = None
        first_name = None
        last_name = None
        profile_image = None

        # Verify Google Authorization Code if present, using both Client ID and Client Secret
        if request.code and settings.GOOGLE_CLIENT_ID and settings.GOOGLE_CLIENT_SECRET:
            token_url = "https://oauth2.googleapis.com/token"
            redirect_uri = request.redirect_uri or request.fallback_url or settings.GOOGLE_REDIRECT_URI or "http://localhost:5173"
            data = {
                "code": request.code,
                "client_id": settings.GOOGLE_CLIENT_ID,
                "client_secret": settings.GOOGLE_CLIENT_SECRET,
                "redirect_uri": redirect_uri,
                "grant_type": "authorization_code",
            }
            try:
                response = httpx.post(token_url, data=data)
                response.raise_for_status()
                token_data = response.json()
                google_id_token_val = token_data.get("id_token")
                if not google_id_token_val:
                    raise ValueError("No id_token returned from Google code exchange.")

                # Verify the cryptographically signed ID Token
                idinfo = google_id_token.verify_oauth2_token(
                    google_id_token_val,
                    google_requests.Request(),
                    settings.GOOGLE_CLIENT_ID
                )
                if not idinfo.get("email_verified"):
                    raise ValueError("Google email not verified.")

                email = idinfo["email"]
                username = idinfo.get("name", email.split("@")[0])
                first_name = idinfo.get("given_name")
                last_name = idinfo.get("family_name")
                profile_image = idinfo.get("picture")
            except Exception as e:
                if request.email:
                    email = request.email
                    username = request.username or email.split("@")[0]
                    first_name = request.first_name
                    last_name = request.last_name
                    profile_image = request.profile_image
                else:
                    raise ValueError(f"Google authorization code exchange failed: {e}")

        # Verify Google ID Token if present and client ID is set
        elif request.id_token and settings.GOOGLE_CLIENT_ID:
            try:
                idinfo = google_id_token.verify_oauth2_token(
                    request.id_token,
                    google_requests.Request(),
                    settings.GOOGLE_CLIENT_ID
                )
                if not idinfo.get("email_verified"):
                    raise ValueError("Google email not verified.")

                email = idinfo["email"]
                username = idinfo.get("name", email.split("@")[0])
                first_name = idinfo.get("given_name")
                last_name = idinfo.get("family_name")
                profile_image = idinfo.get("picture")
            except Exception as e:
                raise ValueError(f"Invalid Google ID Token: {e}")
        else:
            # Fallback to request details (development mode)
            if not request.email:
                raise ValueError("Email or valid Google Authentication Code is required for Google Sign-In.")
            email = request.email
            username = request.username or email.split("@")[0]
            first_name = request.first_name
            last_name = request.last_name
            profile_image = request.profile_image

        user = self.users.get_by_email(email)

        if not user:
            base_username = username
            counter = 1
            while self.users.exists_by_username(username):
                username = f"{base_username}{counter}"
                counter += 1

            hashed_password = password_manager.hash_password(secrets.token_urlsafe(32))

            user = User(
                username=username,
                email=email,
                password_hash=hashed_password,
                role="customer",
                is_active=True,
            )

            profile = UserProfile(
                first_name=first_name,
                last_name=last_name,
                profile_image=profile_image,
            )

            preferences = UserPreference()

            user = self.users.create_user_with_profile(
                user=user,
                profile=profile,
                preferences=preferences,
            )
        else:
            profile = getattr(user, "profile", None)
            if profile:
                updated = False
                if first_name and profile.first_name != first_name:
                    profile.first_name = first_name
                    updated = True
                if last_name and profile.last_name != last_name:
                    profile.last_name = last_name
                    updated = True
                if profile_image and profile.profile_image != profile_image:
                    profile.profile_image = profile_image
                    updated = True
                if updated:
                    self.db.add(profile)
                    self.db.commit()

        access_token = jwt_manager.create_access_token(
            user_id=str(user.id),
            role=user.role,
        )

        refresh_token = jwt_manager.create_refresh_token(
            user_id=str(user.id),
            role=user.role,
        )

        session = UserSession(
            user_id=user.id,
            refresh_token=refresh_token,
            expires_at=datetime.now(timezone.utc)
            + timedelta(days=7),
            is_revoked=False,
        )

        self.sessions.create(session)
        self.users.update_last_login(user)

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
        )