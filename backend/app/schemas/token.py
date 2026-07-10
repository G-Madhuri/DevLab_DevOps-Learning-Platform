from pydantic import BaseModel
from typing import Optional
from app.schemas.user import UserSimpleResponse


class TokenRequest(BaseModel):
    username: str
    password: str


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: UserSimpleResponse


class RefreshTokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class LogoutRequest(BaseModel):
    refresh_token: str


class GoogleTokenRequest(BaseModel):
    token: str
    email: Optional[str] = None
    name: Optional[str] = None
