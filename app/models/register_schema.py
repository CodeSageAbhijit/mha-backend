from pydantic import BaseModel, EmailStr, validator,field_validator,Field
from typing import Optional, List
from datetime import date
import re
from app.models.enum import RoleEnum, GenderEnum
from datetime import datetime


class RegisterUser(BaseModel):
    customId: Optional[str] = None
    role: RoleEnum
    firstName: Optional[str]
    lastName: Optional[str]
    username: Optional[str]
    email: Optional[EmailStr]
    password: Optional[str]
    phoneNumber: Optional[str]
    gender: Optional[GenderEnum]
    maritalStatus: Optional[str]
    dateOfBirth: Optional[date]
    joiningDate:str | None= None
    bloodGroup: Optional[str]
    qualification: Optional[str]
    specialization: Optional[list[str]] = Field(default_factory=list)
    experienceYears: Optional[int]
    licenseNumber: Optional[str]
    shortBio: Optional[str]
    consultationMode: Optional[str] = None
    profilePhoto: Optional[str]
    termsAccepted: bool
    language: Optional[List[str]] = Field(default_factory=list)
   

    # ✅ FIXED: Accept all valid email formats (EmailStr validator from pydantic handles validation)

    @field_validator("dateOfBirth", mode="before")
    def validate_dob(cls, v):
        if v is None:
            return v
        if not isinstance(v, str):
            raise ValueError("dateOfBirth must be a string in DD/MM/YYYY format")
        v = v.strip()
        try:
            dob = datetime.strptime(v, "%d/%m/%Y").date()
        except Exception:
            raise ValueError("dateOfBirth must be in DD/MM/YYYY format")
        if dob > date.today():
            raise ValueError("Date of birth cannot be in the future")
        return v


    @field_validator("joiningDate")
    def validate_joining_date(cls, v):
        if v is None:
            return v
        try:
            datetime.strptime(v, "%d/%m/%Y").date()  # ✅ also expects DD/MM/YYYY
        except Exception:
            raise ValueError("joiningDate must be in DD/MM/YYYY format")
        return v

    @validator("termsAccepted")
    def check_terms(cls, v):
        if not v:
            raise ValueError("You must accept the terms and conditions.")
        return v

    @validator("password")
    def validate_password_strength(cls, v):
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long.")
        if not re.search(r"[A-Z]", v):
            raise ValueError("Password must contain at least one uppercase letter.")
        if not re.search(r"[a-z]", v):
            raise ValueError("Password must contain at least one lowercase letter.")
        if not re.search(r"\d", v):
            raise ValueError("Password must contain at least one number.")
        if not re.search(r"[@$!%*?&]", v):
            raise ValueError("Password must contain at least one special character (@, $, !, %, *, ?, &).")
        return v
    @field_validator("language", mode="before")
    def normalize_languages(cls, v):
        if not v:
            return []
        if isinstance(v, str):
            # handles both: '"marathi","english","gujarati"' and 'marathi,english,gujarati'
            return [l.strip().strip('"') for l in v.split(",") if l.strip()]
        if isinstance(v, list):
            return [str(l).strip() for l in v if str(l).strip()]
        return []
    @field_validator("specialization", mode="before")
    def validate_specialization(cls, v):
        if not v:
            return []
        if isinstance(v, str):
            # handles both: '"marathi","english","gujarati"' and 'marathi,english,gujarati'
            return [l.strip().strip('"') for l in v.split(",") if l.strip()]
        if isinstance(v, list):
            return [str(l).strip() for l in v if str(l).strip()]
        return []



class RegisterResponse(BaseModel):
    status: int
    message: str
    data: dict