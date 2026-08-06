import uuid
from datetime import datetime

from pydantic import (
    BaseModel,
    ConfigDict,
    EmailStr,
    Field,
    model_validator,
)


# =====================================
# Register
# =====================================

class RegisterRequest(BaseModel):

    username: str = Field(
        min_length=3,
        max_length=30,
    )

    email: EmailStr

    password: str = Field(
        min_length=8,
        max_length=128,
    )


# =====================================
# Login
# =====================================

class LoginRequest(BaseModel):

    email: EmailStr

    password: str


# =====================================
# Refresh Token
# =====================================

class RefreshTokenRequest(BaseModel):

    refresh_token: str


# =====================================
# Change Password
# =====================================

class ChangePasswordRequest(BaseModel):

    old_password: str

    new_password: str = Field(
        min_length=8,
        max_length=128,
    )


# =====================================
# Token Response
# =====================================

class TokenResponse(BaseModel):

    access_token: str

    refresh_token: str

    token_type: str = "bearer"


# =====================================
# User Response
# =====================================

class CurrentUserResponse(BaseModel):

    model_config = ConfigDict(
        from_attributes=True
    )

    id: uuid.UUID
    username: str
    email: EmailStr
    role: str
    is_active: bool
    created_at: datetime
    first_name: str | None = None
    last_name: str | None = None
    profile_image: str | None = None

    @model_validator(mode="before")
    @classmethod
    def flatten_profile(cls, data):
        if isinstance(data, dict):
            return data
        profile = getattr(data, "profile", None)
        return {
            "id": data.id,
            "username": data.username,
            "email": data.email,
            "role": data.role,
            "is_active": data.is_active,
            "created_at": data.created_at,
            "first_name": profile.first_name if profile else None,
            "last_name": profile.last_name if profile else None,
            "profile_image": profile.profile_image if profile else None,
        }


# =====================================
# Message Response
# =====================================

class MessageResponse(BaseModel):

    message: str


class GoogleLoginRequest(BaseModel):
    code: str | None = None
    redirect_uri: str | None = None
    fallback_url: str | None = None
    id_token: str | None = None
    email: EmailStr | None = None
    username: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    profile_image: str | None = None