from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime


class Medicine(BaseModel):
    medicineName: str = Field(..., example="Paracetamol")
    dosage: str = Field(..., example="1 tab twice a day")
    notes: Optional[str] = Field(None, example="Take after meals")


class UserRef(BaseModel): 
    userId: str = Field(..., example="DOC1001")
    role: str = Field(..., example="psychiatrist")


class PrescriptionBase(BaseModel):
    patientId: str = Field(..., example="PAT001")   
    prescribedBy: UserRef
    date: str = Field(..., example="2025-04-30")  
    medicines: List[Medicine]


class PrescriptionCreate(PrescriptionBase):
    pass


class PrescriptionUpdate(BaseModel):
    medicines: Optional[List[Medicine]] = None
    


class PrescriptionResponse(PrescriptionBase):
    id: str = Field(..., example="PR001")
    createdBy: UserRef
    updatedBy: Optional[UserRef] = None
    createdAt: datetime = Field(default_factory=datetime.utcnow)
    updatedAt: datetime = Field(default_factory=datetime.utcnow)