from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class ReceiverInfo(BaseModel):
    username: str
    email: str
    phoneNumber: str
    role: str
    gender: str


class ChatMessageCreate(BaseModel):
    """
    Schema for sending a new chat message.
    """
    receiver_id: str
    content: str
    


class ChatMessage(BaseModel):
    content: str
    receiver_id: str

class ChatResponse(BaseModel):
    """
    Schema for returning chat messages from history.
    """
    id: str
    room_id: str
    sender_id: str
    receiver_id: str
    message: str
    timestamp: datetime
    delivered: Optional[bool] = False
    read: Optional[bool] = False
    deleted: Optional[bool] = False

    class Config:
        orm_mode = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }



class ChatConversation(BaseModel):
    room_id: str
    latest_message: ChatResponse
    unread_count: int


class UserStatus(BaseModel):
    user_id: str
    status: str  # 'online' or 'offline'