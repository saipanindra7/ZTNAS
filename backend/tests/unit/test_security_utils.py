"""Unit tests for security utilities."""

from datetime import timedelta

from utils.security import (
    create_access_token,
    create_refresh_token,
    hash_password,
    verify_access_token,
    verify_password,
    verify_refresh_token,
)


def test_hash_password_not_plaintext():
    plain = "UnitTest@123"
    hashed = hash_password(plain)
    assert hashed != plain
    assert hashed.startswith("pbkdf2_sha256$")


def test_verify_password_success_and_failure():
    plain = "UnitTest@123"
    hashed = hash_password(plain)
    assert verify_password(plain, hashed) is True
    assert verify_password("WrongPassword@123", hashed) is False


def test_access_token_type_and_validation():
    token = create_access_token({"sub": "42", "username": "unit_user"})
    payload = verify_access_token(token)
    assert payload is not None
    assert payload.get("sub") == "42"
    assert payload.get("type") == "access"


def test_refresh_token_type_and_validation():
    token = create_refresh_token({"sub": "42", "username": "unit_user"})
    payload = verify_refresh_token(token)
    assert payload is not None
    assert payload.get("sub") == "42"
    assert payload.get("type") == "refresh"


def test_refresh_token_not_valid_as_access_token():
    refresh_token = create_refresh_token({"sub": "42"})
    assert verify_access_token(refresh_token) is None


def test_access_token_explicit_expiry():
    token = create_access_token({"sub": "42"}, expires_delta=timedelta(minutes=5))
    payload = verify_access_token(token)
    assert payload is not None
    assert payload.get("type") == "access"
