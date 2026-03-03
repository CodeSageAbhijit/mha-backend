from pydantic import BaseModel, Field, validator
from typing import Optional
from datetime import datetime

class ReviewBase(BaseModel):
    reviewer_id: str = Field(..., description="Patient ID who is reviewing")
    target_id: str = Field(..., description="Doctor or Counselor ID being reviewed")
    role: str = Field(..., description="Type: 'psychiatrist' or 'counselor'")
    rating: int = Field(..., ge=1, le=5, description="Rating from 1 to 5")
    comment: Optional[str] = Field(None, max_length=1000, description="Review comment")
    date: Optional[datetime] = Field(default_factory=datetime.utcnow)

    @validator('role')
    def validate_role(cls, v):
        if v not in ['psychiatrist', 'counselor']:
            raise ValueError("role must be 'psychiatrist' or 'counselor'")
        return v

class ReviewCreate(ReviewBase):
    pass

class ReviewOut(ReviewBase):
    id: str

    class Config:
        orm_mode = True