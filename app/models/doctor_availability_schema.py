from pydantic import BaseModel, Field
from typing import List, Optional, Dict

class TimeSlot(BaseModel):
    start: str = Field(..., example="09:00")  # HH:MM
    end: str = Field(..., example="12:00")    # HH:MM

class DayAvailability(BaseModel):
    day: str = Field(..., example="Monday")
    slots: List[TimeSlot]

class AvailabilityCreate(BaseModel):
    doctor_id: str
    timezone: str = Field(..., example="IST (India)")
    consultation_duration: int = Field(..., example=30)  # minutes
    availability: List[DayAvailability]

class AvailabilityUpdate(BaseModel):
    timezone: Optional[str]
    consultation_duration: Optional[int]
    availability: Optional[List[DayAvailability]]

class AvailabilityResponse(BaseModel):
    id: str
    doctor_id: str
    timezone: str
    consultation_duration: int
    availability: List[DayAvailability]
