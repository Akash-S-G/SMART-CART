from datetime import datetime, timedelta, timezone
from typing import Any

from jose import JWTError, jwt

from app.core.config import settings


class JWTManager:
    """
    Handles JWT creation and validation.
    """

    def __init__(self):
        self.secret_key = settings.SECRET_KEY
        self.algorithm = settings.ALGORITHM

    def _create_token(
        self,
        user_id: str,
        role: str,
        token_type: str,
        expires_delta: timedelta,
    ) -> str:

        now = datetime.now(timezone.utc)

        payload = {
            "sub": user_id,
            "role": role,
            "type": token_type,
            "iat": now,
            "exp": now + expires_delta,
        }

        return jwt.encode(
            payload,
            self.secret_key,
            algorithm=self.algorithm,
        )

    def create_access_token(
        self,
        user_id: str,
        role: str,
    ) -> str:

        expires = timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )

        return self._create_token(
            user_id=user_id,
            role=role,
            token_type="access",
            expires_delta=expires,
        )

    def create_refresh_token(
        self,
        user_id: str,
        role: str,
    ) -> str:

        expires = timedelta(
            days=settings.REFRESH_TOKEN_EXPIRE_DAYS
        )

        return self._create_token(
            user_id=user_id,
            role=role,
            token_type="refresh",
            expires_delta=expires,
        )

    def decode_token(
        self,
        token: str,
    ) -> dict[str, Any]:

        return jwt.decode(
            token,
            self.secret_key,
            algorithms=[self.algorithm],
        )

    def verify_token(
        self,
        token: str,
        expected_type: str = "access",
    ) -> dict[str, Any]:

        try:

            payload = self.decode_token(token)

            if payload.get("type") != expected_type:
                raise ValueError(
                    "Invalid token type."
                )

            return payload

        except JWTError as exc:
            raise ValueError(
                "Invalid or expired token."
            ) from exc


jwt_manager = JWTManager()