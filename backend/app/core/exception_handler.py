from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from app.auth.exceptions import (
    AdminRequiredError,
    EmailAlreadyExistsError,
    InactiveUserError,
    InvalidCredentialsError,
    InvalidPasswordError,
    InvalidRefreshTokenError,
    InvalidTokenError,
    PasswordReuseError,
    PermissionDeniedError,
    UserNotFoundError,
    UsernameAlreadyExistsError,
)

from app.core.logging import logger


def register_exception_handlers(app: FastAPI) -> None:

    @app.exception_handler(EmailAlreadyExistsError)
    async def email_exists_handler(
        request: Request,
        exc: EmailAlreadyExistsError,
    ):
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={"detail": "Email already exists."},
        )

    @app.exception_handler(UsernameAlreadyExistsError)
    async def username_exists_handler(
        request: Request,
        exc: UsernameAlreadyExistsError,
    ):
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={"detail": "Username already exists."},
        )

    @app.exception_handler(InvalidCredentialsError)
    async def invalid_credentials_handler(
        request: Request,
        exc: InvalidCredentialsError,
    ):
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"detail": "Invalid email or password."},
        )

    @app.exception_handler(UserNotFoundError)
    async def user_not_found_handler(
        request: Request,
        exc: UserNotFoundError,
    ):
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"detail": "User not found."},
        )

    @app.exception_handler(InactiveUserError)
    async def inactive_user_handler(
        request: Request,
        exc: InactiveUserError,
    ):
        return JSONResponse(
            status_code=status.HTTP_403_FORBIDDEN,
            content={"detail": "User account is inactive."},
        )

    @app.exception_handler(InvalidPasswordError)
    async def invalid_password_handler(
        request: Request,
        exc: InvalidPasswordError,
    ):
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"detail": "Current password is incorrect."},
        )

    @app.exception_handler(PasswordReuseError)
    async def password_reuse_handler(
        request: Request,
        exc: PasswordReuseError,
    ):
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"detail": "New password cannot match the current password."},
        )

    @app.exception_handler(InvalidTokenError)
    @app.exception_handler(InvalidRefreshTokenError)
    async def token_handler(
        request: Request,
        exc: Exception,
    ):
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"detail": "Invalid or expired token."},
        )

    @app.exception_handler(PermissionDeniedError)
    @app.exception_handler(AdminRequiredError)
    async def permission_handler(
        request: Request,
        exc: Exception,
    ):
        return JSONResponse(
            status_code=status.HTTP_403_FORBIDDEN,
            content={"detail": "Permission denied."},
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(
        request: Request,
        exc: Exception,
    ):
        logger.exception(
            "Unhandled exception for %s %s",
            request.method,
            request.url.path,
        )
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": "Internal server error"},
        )
