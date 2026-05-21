from datetime import UTC, datetime, timedelta
from typing import Any

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings

BCRYPT_MAX_PASSWORD_BYTES = 72
password_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def validate_bcrypt_password(password: str) -> None:
    if len(password.encode("utf-8")) > BCRYPT_MAX_PASSWORD_BYTES:
        raise ValueError("Password must not exceed 72 bytes for bcrypt.")


def verify_password(plain_password: str, password_hash: str) -> bool:
    try:
        validate_bcrypt_password(plain_password)
    except ValueError:
        return False
    return password_context.verify(plain_password, password_hash)


def get_password_hash(password: str) -> str:
    validate_bcrypt_password(password)
    return password_context.hash(password)


def create_access_token(
    subject: str | int,
    expires_delta: timedelta | None = None,
    extra_claims: dict[str, Any] | None = None,
) -> str:
    expire = datetime.now(UTC) + (
        expires_delta or timedelta(minutes=settings.access_token_expire_minutes)
    )
    payload: dict[str, Any] = {"sub": str(subject), "exp": expire}
    if extra_claims:
        payload.update(extra_claims)
    return jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)


def decode_access_token(token: str) -> dict[str, Any] | None:
    try:
        return jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
    except JWTError:
        return None
