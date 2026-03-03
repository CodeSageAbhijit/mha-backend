# ...existing code...
from pydantic import BaseModel, EmailStr, Field, field_validator, ConfigDict
from typing import List, Optional, Literal
from datetime import date, datetime
from app.models.enum import GenderEnum
import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)


# StatusType = Literal["active", "inactive"]
class CounselorBase(BaseModel):
    role: Optional[str] = "counselor"
    firstName: str
    lastName: str
    email: EmailStr
    phoneNumber: Optional[str] = None
    gender: Optional[GenderEnum] = None
    dateOfBirth: Optional[str] 
    qualification: Optional[str] = None
    specialization: Optional[list[str]] = Field(default_factory=list)
    problemTypes: Optional[List[str]] = Field(default_factory=list, description="Types of problems handled (e.g., relationship, breakup, business, divorce, anxiety, depression, family, career)")
    experienceYears: Optional[int] = Field(
        0, ge=0, description="Experience years must be >= 0"
    )
    licenseNumber: Optional[str] = None
    shortBio: Optional[str] = Field(None, max_length=1000)
    consultationMode: Optional[str] = None
    language: Optional[List[str]] = Field(default_factory=list)
    termsAccepted: Optional[bool] = False
    profilePhoto: Optional[str] = None
    department: Optional[str] = None
    designation: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    postalCode: Optional[str] = None
    city: Optional[str] = None
    addressLine: Optional[str]
    joiningDate:str | None= None
    # status: Optional[StatusType] = "active"

    # Pydantic V2 config
    model_config = ConfigDict(str_strip_whitespace=True, from_attributes=True)

   
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

    # V2: validate/strip many string fields before parsing
    @field_validator(
        "firstName", "lastName", "phoneNumber", "qualification",
        "specialization", "shortBio", "consultationMode","gender",
        "department", "designation", "state", "country", "postalCode", "city", "profilePhoto",
        mode="before"
    )
    def strip_string_fields(cls, v, info):
        if v is None:
            return v
        if isinstance(v, str):
            if not v.strip():
                raise ValueError(f"{info.field_name} is required")
            return v.strip()
        return v

    @field_validator("consultationMode")
    def validate_consultation_mode(cls, v):
        if v is None:
            return v
        allowed = {"both", "online", "in-person"}
        if v not in allowed:
            raise ValueError("consultationMode must be one of: both, online, in-person")
        return v

    @field_validator("phoneNumber")
    def validate_phone_number(cls, v):
        if not v.isdigit():
            raise ValueError("phoneNumber must contain only digits")
        if len(v) != 10:
            raise ValueError("phoneNumber must be exactly 10 digits")
        return v

    

    @field_validator("postalCode")
    def validate_postal_code(cls, v):
        if not v.isdigit() or len(v) != 6 or v[0] == "0":
            raise ValueError("Invalid Indian postal code")
        return v

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

    @field_validator("email")
    def validate_gmail(cls, v):
        if not v.endswith("@gmail.com"):
            raise ValueError("Only Gmail addresses are allowed")
        return v

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

# ...existing code...
class CounselorCreate(CounselorBase):
    password: Optional[str] = None  # Optional for auto-generated passwords


class CounselorUpdate(CounselorBase):
    updated_by: Optional[str] = None


class CounselorOut(CounselorBase):
    id: str = Field(..., alias="_id")
    createdAt: datetime
    updatedAt: Optional[datetime]

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)
# ...existing code...
