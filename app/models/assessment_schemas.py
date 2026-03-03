from pydantic import BaseModel, EmailStr, validator, Field
from typing import Optional, List
from datetime import date, datetime
import re
from typing import Literal
from app.models.enum import RoleEnum, GenderEnum, AppointmentStatusEnum
from pydantic import BaseModel, Field
from typing import List, Optional
from pydantic import validator
from typing import Dict, Any


class AssessmentBase(BaseModel):
    disease: str
    category: str
    ageGroup: str
    question: str
    options: List[str]

class AssessmentCreate(AssessmentBase):
    pass
    

class AssessmentUpdate(AssessmentBase):
    pass

class AssessmentResponse(AssessmentBase):
    id: str

class AnswerSchema(BaseModel):
    questionId: str
    answer: str

class UserAssessmentCreate(BaseModel):
    category: str = Field(..., description="Assessment category (e.g., Individual, Corporate)")
    answers: List[AnswerSchema] = Field(..., description="List of question-answer pairs")

# DB schema (for documents stored in Mongo)
class UserAssessmentInDB(UserAssessmentCreate):
    userId: str
    submitted_at: datetime

# Response schema (for sending back to client)
class UserAssessmentResponse(UserAssessmentInDB):
    id: str = Field(..., alias="_id")

