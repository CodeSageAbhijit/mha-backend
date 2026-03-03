from pydantic import BaseModel, Field
from typing import Optional
from datetime import date

class CounselingSession(BaseModel):
    patientName: str
    counsellor: str
    date: date
    time: str
    sessionType: str
    mode: str
    notes: Optional[str] = ""
    status: str = "scheduled"
    payment: str
    rating: Optional[int] = None
