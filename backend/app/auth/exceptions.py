class AuthenticationError(Exception):
    """
    Base authentication exception.
    """
    pass


# =====================================================
# Registration
# =====================================================

class EmailAlreadyExistsError(AuthenticationError):
    pass


class UsernameAlreadyExistsError(AuthenticationError):
    pass


# =====================================================
# Login
# =====================================================

class InvalidCredentialsError(AuthenticationError):
    pass


class UserNotFoundError(AuthenticationError):
    pass


class InactiveUserError(AuthenticationError):
    pass


# =====================================================
# Password
# =====================================================

class InvalidPasswordError(AuthenticationError):
    pass


class PasswordMismatchError(AuthenticationError):
    pass


class PasswordReuseError(AuthenticationError):
    pass


# =====================================================
# Token
# =====================================================

class InvalidTokenError(AuthenticationError):
    pass


class ExpiredTokenError(AuthenticationError):
    pass


class InvalidRefreshTokenError(AuthenticationError):
    pass


class RevokedSessionError(AuthenticationError):
    pass


# =====================================================
# Authorization
# =====================================================

class PermissionDeniedError(AuthenticationError):
    pass


class AdminRequiredError(AuthenticationError):
    pass