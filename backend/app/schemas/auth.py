from pydantic import BaseModel, EmailStr, Field, field_validator

from app.core.security import BCRYPT_MAX_PASSWORD_BYTES


def validate_password_length(value: str) -> str:
    if len(value.encode("utf-8")) > BCRYPT_MAX_PASSWORD_BYTES:
        raise ValueError("Password must not exceed 72 bytes for bcrypt.")
    return value


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)

    @field_validator("password")
    @classmethod
    def validate_password(cls, value: str) -> str:
        return validate_password_length(value)


class RegisterRequest(BaseModel):
    nickname: str = Field(min_length=3, max_length=80)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)

    @field_validator("nickname")
    @classmethod
    def validate_nickname(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Nickname must not be blank.")
        return value

    @field_validator("password")
    @classmethod
    def validate_password(cls, value: str) -> str:
        return validate_password_length(value)


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenPayload(BaseModel):
    sub: str | None = None
