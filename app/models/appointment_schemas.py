from pydantic import BaseModel
from typing import Optional
from datetime import date, datetime

from app.models.enum import  AppointmentStatusEnum
from pydantic import BaseModel
from typing import Optional
# from pydantic import validator
from enum import Enum

class ConsultationModeEnum(str, Enum):
    ONLINE = "online"
    OFFLINE = "in-person"
    # VIDEO_CALL = "VIDEO_CALL"
    # PHONE_CALL = "PHONE_CALL"


class RescheduleRequest(BaseModel):
    newDate: date
    #newTimeSlot: str
    newStartTime: str
    newEndTime: str

# class AppointmentStatusEnum(str, Enum):
#     PENDING = "PENDING"
#     CONFIRMED = "CONFIRMED"
#     CANCELLED = "CANCELLED"

class AppointmentCreation(BaseModel):
    patientId: str
    doctorId: str
    #timeSlot: str
    startTime: str
    endTime: str
    date: datetime
    reasonForVisit: Optional[str] = None
    status: str
    consultationMode: ConsultationModeEnum 
    

class AppointmentCreationCounsolor(BaseModel):
    patientId: str
    counselorId: str
    #timeSlot: str
    startTime: str
    endTIme:str
    date: datetime
    reasonForVisit: Optional[str] = None
    status: str

class AppointmentRequest(BaseModel):
    patientName: str
    doctorName: str
    #timeSlot: str
    startTime: str
    endTIme:str
    date: datetime

class ConfirmationRequest(BaseModel):
    appointmentId: str
    status: str
    
class AppointmentCreationCounsolor(BaseModel):
    patientId: str
    counselorId: str
    #timeSlot: str
    startTime: str
    endTime:str
    date: datetime
    reasonForVisit: Optional[str] = None
    status: str
    consultationMode: ConsultationModeEnum
    