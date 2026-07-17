from datetime import datetime

from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    email: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserOut(BaseModel):
    id: int
    email: str
    full_name: str | None = None
    initials: str
    role: str
    is_active: bool
    tos_accepted_at: datetime | None = None

    class Config:
        from_attributes = True


class UserCreate(BaseModel):
    email: str
    password: str = Field(min_length=8)
    full_name: str | None = None
    role: str = "member"


class UserUpdate(BaseModel):
    full_name: str | None = None
    role: str | None = None
    is_active: bool | None = None


class MeUpdate(BaseModel):
    full_name: str | None = None


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str = Field(min_length=8)
