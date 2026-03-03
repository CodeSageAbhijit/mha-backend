from pydantic import BaseModel, EmailStr, validator, Field,field_validator
from typing import Optional, List
from datetime import date, datetime
import re
from typing import Literal
from app.models.enum import RoleEnum, GenderEnum, AppointmentStatusEnum
from pydantic import BaseModel, Field
from typing import List, Optional
from pydantic import validator


class DoctorBase(BaseModel):
    firstName: str
    lastName: str
    email: EmailStr
    dateOfBirth: str
    phoneNumber: str
    qualification: str
    designation: str
    department: str
    gender: GenderEnum
    licenseNumber: str
    language: Optional[List[str]]=Field(default_factory=list)
    shortBio: Optional[str] = Field(None, max_length=1000)
    consultationMode:Optional[str]
    city: str
    state: str
    country: str
    postalCode: str
    addressLine : Optional[str]
    specialization: Optional[List[str]] = Field(default_factory=list)
    problemTypes: Optional[List[str]] = Field(default_factory=list, description="Types of problems handled (e.g., relationship, breakup, business, divorce, anxiety, depression, family, career)")
    experienceYears: Optional[int]=0
    joiningDate:str | None= None
    profilePhoto: str
    termsAccepted:Optional[bool] = False


    # Strip strings and check required
    @field_validator(
        "firstName", "lastName", "phoneNumber", "qualification",
        "designation", "department","licenseNumber", "state", "country",
        "postalCode", "city", "profilePhoto","termsAccepted",
        mode="before"
    )
    def strip_and_required(cls, v, info):
        if v is None or (isinstance(v, str) and not v.strip()):
            raise ValueError(f"{info.field_name} is required")
        if isinstance(v, str):
            return v.strip()
        return v

    # Email must be Gmail
    @field_validator("email")
    def validate_gmail(cls, v):
        if not v.endswith("@gmail.com"):
            raise ValueError("Only Gmail addresses are allowed")
        return v


    @field_validator("dateOfBirth", mode="before")
    def parse_date_of_birth(cls, v):
        if isinstance(v, date):
            return v.strftime("%d/%m/%Y")
        if not isinstance(v, str):
            raise ValueError("dateOfBirth must be a string in DD/MM/YYYY format")
        v = v.strip()
        try:
            datetime.strptime(v, "%d/%m/%Y")  # just validate
            return v
        except Exception:
            raise ValueError("dateOfBirth must be in DD/MM/YYYY format")





    # Phone number validation
    @field_validator("phoneNumber")
    def validate_phone_number(cls, v):
        if not v.isdigit():
            raise ValueError("phoneNumber must contain only digits")
        if len(v) != 10:
            raise ValueError("phoneNumber must be exactly 10 digits")
        return v

    # Postal code validation
    @field_validator("postalCode")
    def validate_postal_code(cls, v):
        if not v.isdigit() or len(v) != 6 or v[0] == "0":
            raise ValueError("Invalid Indian postal code")
        return v

    # Specialization: string or list
    @field_validator("specialization", mode="before")
    def validate_specialization(cls, v):
        if v is None:
            return []
        if isinstance(v, str):
            return [v.strip()]
        if isinstance(v, list):
            return [str(i).strip() for i in v if i]
        raise ValueError("specialization must be a string or list of strings")
    

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
    def normalize_specializations(cls, v):
        if not v:
            return []
        if isinstance(v, str):
            # handles both: '"marathi","english","gujarati"' and 'marathi,english,gujarati'
            return [l.strip().strip('"') for l in v.split(",") if l.strip()]
        if isinstance(v, list):
            return [str(l).strip() for l in v if str(l).strip()]
        return []

    
        

    # Experience: ensure int
    @field_validator("experienceYears", mode="before")
    def validate_experience(cls, v):
        if v is None or v == "":
            return 0
        try:
            return int(float(v))
        except Exception:
            return 0

    @field_validator("language", mode="before")
    def validate_language(cls, v):
        if v is None:
            return []
        if isinstance(v, str):  # if frontend sends a single string
            return [v.strip()]
        if isinstance(v, list):  # if frontend sends a list
            return [str(item).strip() for item in v if item]
        raise ValueError("language must be a string or list of strings")
    

    
    @field_validator("dateOfBirth")
    def validate_dob(cls, v):
        try:
            dob = datetime.strptime(v, "%d/%m/%Y").date()  # ✅ expects DD/MM/YYYY
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
class DoctorCreate(DoctorBase):
    pass

class DoctorUpdate(DoctorBase):
    pass