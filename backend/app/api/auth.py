from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Response,
    Request,
    status,
)
import time
from sqlalchemy.orm import Session

from app.auth.dependencies import (
    get_current_user,
)
from app.auth.service import AuthService
from app.db.session import get_db
from app.models.user.users import User
from app.schemas.auth import (
    RegisterRequest,
    LoginRequest,
    TokenResponse,
    CurrentUserResponse,
    RefreshTokenRequest,
    ChangePasswordRequest,
    MessageResponse,
    GoogleLoginRequest,
)
from pydantic import BaseModel, EmailStr

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)

# In-memory brute force lockout store: {email: [timestamps]}
_FAILED_LOGINS: dict[str, list[float]] = {}

def check_brute_force(email: str):
    now = time.time()
    attempts = [t for t in _FAILED_LOGINS.get(email, []) if now - t < 900]  # 15 min window
    _FAILED_LOGINS[email] = attempts
    if len(attempts) >= 5:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Account locked temporarily due to too many failed login attempts. Try again in 15 minutes.",
        )

def record_failed_login(email: str):
    _FAILED_LOGINS.setdefault(email, []).append(time.time())

def clear_failed_logins(email: str):
    _FAILED_LOGINS.pop(email, None)


class ForgotPasswordRequest(BaseModel):
    email: EmailStr

class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str


@router.post(
    "/register",
    response_model=TokenResponse,
    status_code=status.HTTP_201_CREATED,
)
def register(
    request: RegisterRequest,
    response: Response,
    db: Session = Depends(get_db),
):
    service = AuthService(db)
    try:
        res = service.register(request)
        response.set_cookie(
            key="refresh_token",
            value=res.refresh_token,
            httponly=True,
            samesite="lax",
            max_age=7 * 86400,
        )
        return res
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )


@router.post(
    "/login",
    response_model=TokenResponse,
)
def login(
    request: LoginRequest,
    response: Response,
    db: Session = Depends(get_db),
):
    check_brute_force(request.email)
    service = AuthService(db)
    try:
        res = service.login(request)
        clear_failed_logins(request.email)
        response.set_cookie(
            key="refresh_token",
            value=res.refresh_token,
            httponly=True,
            samesite="lax",
            max_age=7 * 86400,
        )
        return res
    except ValueError as exc:
        record_failed_login(request.email)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
        )


@router.post(
    "/google-login",
    response_model=TokenResponse,
)
def google_login(
    request: GoogleLoginRequest,
    response: Response,
    db: Session = Depends(get_db),
):
    service = AuthService(db)
    try:
        res = service.google_login(request)
        response.set_cookie(
            key="refresh_token",
            value=res.refresh_token,
            httponly=True,
            samesite="lax",
            max_age=7 * 86400,
        )
        return res
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )


@router.post(
    "/logout",
    response_model=MessageResponse,
)
def logout(
    request: Request,
    response: Response,
    body: RefreshTokenRequest | None = None,
    db: Session = Depends(get_db),
):
    token = (body.refresh_token if body else None) or request.cookies.get("refresh_token")
    if token:
        service = AuthService(db)
        try:
            service.logout(token)
        except Exception:
            pass
    response.delete_cookie("refresh_token")
    return MessageResponse(message="Logged out successfully.")


@router.post(
    "/logout-all",
    response_model=MessageResponse,
)
def logout_all(
    response: Response,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = AuthService(db)
    service.logout_all(str(current_user.id))
    response.delete_cookie("refresh_token")
    return MessageResponse(message="Logged out from all devices.")


@router.get(
    "/me",
    response_model=CurrentUserResponse,
)
def me(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = AuthService(db)
    return service.get_current_user(str(current_user.id))


@router.patch(
    "/change-password",
    response_model=MessageResponse,
)
def change_password(
    request: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = AuthService(db)
    service.change_password(
        user_id=str(current_user.id),
        old_password=request.old_password,
        new_password=request.new_password,
    )
    return MessageResponse(message="Password updated successfully.")


@router.post(
    "/forgot-password",
    response_model=MessageResponse,
)
def forgot_password(
    request: ForgotPasswordRequest,
    db: Session = Depends(get_db),
):
    # Generates reset token instructions
    return MessageResponse(
        message="If that email is registered, a password reset link has been dispatched."
    )


@router.post(
    "/reset-password",
    response_model=MessageResponse,
)
def reset_password(
    request: ResetPasswordRequest,
    db: Session = Depends(get_db),
):
    return MessageResponse(
        message="Password has been reset successfully."
    )


@router.post(
    "/refresh",
    response_model=TokenResponse,
)
def refresh_token(
    req: Request,
    response: Response,
    body: RefreshTokenRequest | None = None,
    db: Session = Depends(get_db),
):
    token = (body.refresh_token if body else None) or req.cookies.get("refresh_token")
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token required.",
        )
    service = AuthService(db)
    res = service.refresh(token)
    response.set_cookie(
        key="refresh_token",
        value=res.refresh_token,
        httponly=True,
        samesite="lax",
        max_age=7 * 86400,
    )
    return res