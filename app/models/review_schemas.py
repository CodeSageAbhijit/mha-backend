from pydantic import BaseModel, Field, constr, conint
from typing import Optional
from datetime import datetime

class ReviewCreate(BaseModel):
    reviewer: str = Field(..., description="Patient custom id (reviewer)")
    reviewed: str = Field(..., description="ID of the person reviewed (doctorId or counselorId)")
    rating: int = Field(..., description="Rating from 1 to 5")
    comment: Optional[str] = Field("", description="Optional comment")

    class Config:
        schema_extra = {
            "example": {
                "reviewer": "PAT-12345",
                "reviewed": "DOC-123",
                "rating": 5,
                "comment": "Very helpful."
            }
        }

class ReviewUpdate(BaseModel):
    rating: Optional[int] = None
    comment: Optional[str] = None

class ReviewResponse(BaseModel):
    id: str
    reviewer: str
    reviewedId: str
    rating: int
    comment: Optional[str] = ""
    createdAt: datetime
