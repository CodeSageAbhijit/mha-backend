from pydantic import BaseModel, EmailStr
from typing import Optional

class TokenResponse(BaseModel):
    accessToken: str
    refreshToken: str
    userId: str
    role: str
    tokenType: str = "bearer"

class RefreshTokenRequest(BaseModel):
    refreshToken: str

class TokenData(BaseModel):
    accessToken: str
    refreshToken: str
    userId: str
    role: str
    roleUserId: Optional[str] = None   # ✅ make optional
    tokenType: str = "bearer"

class LoginResponse(BaseModel):
    success: bool
    status: int
    message: str
    data: TokenData | None
    error: str | None
    errors: list[str]
