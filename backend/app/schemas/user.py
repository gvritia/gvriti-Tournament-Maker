from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr

from app.core.constants import UserRole


class UserBase(BaseModel):
    nickname: str
    email: EmailStr
    role: UserRole = UserRole.ORGANIZER


class UserCreate(UserBase):
    password: str


class UserUpdate(BaseModel):
    nickname: str | None = None
    email: EmailStr | None = None
    password: str | None = None
    role: UserRole | None = None


class UserRead(UserBase):
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
