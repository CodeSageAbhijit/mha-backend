from pydantic import BaseModel, Field
from typing import List, Optional, Dict

class TimeSlot(BaseModel):
    start: str = Field(..., example="09:00")  # HH:MM
    end: str = Field(..., example="12:00")    # HH:MM

class DayAvailability(BaseModel):
    day: str = Field(..., example="Monday")
    slots: List[TimeSlot]

class AvailabilityCreate(BaseModel):
    counselorId: str
    timeZone: str = Field(..., example="IST (India)")
    consultationDuration: int = Field(..., example=30)  # minutes
    availability: List[DayAvailability]

class AvailabilityUpdate(BaseModel):
    timeZone: Optional[str]
    consultationDuration: Optional[int]
    availability: Optional[List[DayAvailability]]

class AvailabilityResponse(BaseModel):
    id: str
    counselorId: str
    timeZone: str
    consultationDuration: int
    availability: List[DayAvailability]
