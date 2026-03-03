from pydantic import BaseModel, EmailStr, validator, Field
from typing import Optional, List
from datetime import date, datetime
import re
from typing import Literal
from app.models.enum import RoleEnum, GenderEnum, AppointmentStatusEnum
from pydantic import BaseModel, Field
from typing import List, Optional
from pydantic import validator


class PaymentBase(BaseModel):
    patinetId: str
    sessionType: str
    patient: str
    counsellor: str
    status: str
    tax: float
    discount: float
    amount: float
    date: date

class PaymentCreate(PaymentBase):
    pass

class PaymentUpdate(BaseModel):
    patinetId: Optional[str]
    sessionType: Optional[str]
    patient: Optional[str]
    counsellor: Optional[str]
    status: Optional[str]
    tax: Optional[float]
    discount: Optional[float]
    amount: Optional[float]
    date: Optional[date]

class Payment(PaymentBase):
    id: str

class PaymentCreate(BaseModel):
    patinetId: str
    sessionType: str
    patient: str
    counsellor: str
    status: Literal["paid", "pending"]
    tax: float
    discount: float
    amount: int
    date: datetime