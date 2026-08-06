from pwdlib import PasswordHash


class PasswordManager:
    """
    Handles password hashing and verification.
    """

    def __init__(self) -> None:
        self.password_hash = PasswordHash.recommended()

    def hash_password(self, password: str) -> str:
        """
        Hash a plain text password.
        """
        return self.password_hash.hash(password)

    def verify_password(
        self,
        plain_password: str,
        hashed_password: str,
    ) -> bool:
        """
        Verify a password against its hash.
        """
        return self.password_hash.verify(
            plain_password,
            hashed_password,
        )

    def needs_rehash(
        self,
        hashed_password: str,
    ) -> bool:
        """
        Returns True if the password should be
        rehashed using newer security parameters.
        """
        return self.password_hash.needs_rehash(
            hashed_password
        )


password_manager = PasswordManager()