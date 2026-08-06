from app.auth.hashing import password_manager


def test_password_hashing():
    password = "SmartCart@123"

    hashed = password_manager.hash_password(password)

    assert password != hashed

    assert password_manager.verify_password(
        password,
        hashed,
    )

    assert not password_manager.verify_password(
        "WrongPassword",
        hashed,
    )