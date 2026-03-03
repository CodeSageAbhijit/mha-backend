from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from app.models.enum import RoleEnum

class LoginHistory(BaseModel):
    userId: str
    role: RoleEnum
    loginTime: datetime
    logoutTime: Optional[datetime] = None
    sessionId: Optional[str] = None
    ipAddress: Optional[str] = None

# This schema can be used for storing and retrieving login/logout events for users.
