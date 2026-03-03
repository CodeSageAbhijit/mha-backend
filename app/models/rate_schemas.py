from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

class ConsultationRates(BaseModel):
    videoCallRate: int = Field(..., ge=1, le=500, description="Video call rate per minute (₹1-500)")
    voiceCallRate: int = Field(..., ge=1, le=500, description="Voice call rate per minute (₹1-500)")
    inPerson15Min: int = Field(..., ge=100, description="15 minutes in-person session fee")
    inPerson30Min: int = Field(..., ge=200, description="30 minutes in-person session fee") 
    inPerson60Min: int = Field(..., ge=400, description="60 minutes in-person session fee")

class GetConsultationRatesResponse(BaseModel):
    providerId: str
    providerName: str
    specialization: Optional[List[str]]
    qualification: Optional[str]
    videoCallRate: int
    voiceCallRate: int
    inPerson15Min: int
    inPerson30Min: int
    inPerson60Min: int
    consultationModes: List[str]
    isActive: bool
    experience: Optional[int]
    updatedAt: str
    rating: Optional[float] = None
    totalReviews: Optional[int] = None