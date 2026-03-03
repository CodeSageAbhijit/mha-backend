from typing import Literal, Optional
from pydantic import BaseModel, Field
from app.database.mongo import db


class CallInitiatePayload(BaseModel):
    callerId: str
    callerRole: Literal["user", "psychiatrist", "counselor"]
    calleeId: str
    calleeRole: Literal["user", "psychiatrist", "counselor"]
    callType: Literal["audio", "video"]
    appointmentId: Optional[str] = None


class CallSessionPayload(BaseModel):
    sessionId: str


class CallEndPayload(BaseModel):
    sessionId: str
    durationSec: Optional[int] = None


class CallHistoryPayload(BaseModel):
    userId: str
    page: int = Field(default=1, ge=1)
    limit: int = Field(default=50, ge=1, le=100)


# =========================
# Call Events
# =========================
calls_collection = db["calls"]


class CallInitiatePayload(BaseModel):
    callerId: str
    callerRole: Literal["user", "psychiatrist", "counselor"]
    calleeId: str
    calleeRole: Literal["user", "psychiatrist", "counselor"]
    callType: Literal["audio", "video"]
    appointmentId: Optional[str] = None


class CallSessionPayload(BaseModel):
    sessionId: str


class CallEndPayload(BaseModel):
    sessionId: str
    durationSec: Optional[int] = None


class CallHistoryPayload(BaseModel):
    userId: str
    page: int = Field(default=1, ge=1)
    limit: int = Field(default=50, ge=1, le=100)