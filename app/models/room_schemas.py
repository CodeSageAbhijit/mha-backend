from pydantic import BaseModel, Field
from datetime import datetime

class RoomCreate(BaseModel):
    name: str
    description: str = ""
    created_by: str = "admin"
    isPrivate: bool = False

class RoomInDB(RoomCreate):
    id: str = Field(..., alias="_id")
    createdAt: datetime