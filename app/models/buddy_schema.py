from pydantic import BaseModel, EmailStr, field_validator, Field
from typing import Optional, List
from datetime import date, datetime
from app.models.enum import GenderEnum

class BuddyBase(BaseModel):
    firstName: str
    lastName: str
    email: EmailStr
    dateOfBirth: str
    phoneNumber: str
    gender: GenderEnum
    language: Optional[List[str]] = Field(default_factory=list)
    shortBio: Optional[str] = Field(None, max_length=1000)
    city: str
    state: str
    country: str
    postalCode: str
    addressLine: Optional[str]
    interests: Optional[List[str]] = Field(default_factory=list, description="Buddy interests/hobbies")
    problemTypes: Optional[List[str]] = Field(default_factory=list, description="Support areas (e.g., loneliness, motivation, social support)")
    profilePhoto: str
    consultationFee: Optional[int] = 200  # Buddies typically charge less
    rating: Optional[float] = 0.0
    reviewCount: Optional[int] = 0
    availability: Optional[str] = "offline"  # online, offline, emergency
    termsAccepted: Optional[bool] = False

    @field_validator(
        "firstName", "lastName", "phoneNumber",
        "state", "country",
        "postalCode", "city", "profilePhoto",
        mode="before"
    )
    def strip_and_required(cls, v, info):
        if v is None or (isinstance(v, str) and not v.strip()):
            raise ValueError(f"{info.field_name} is required")
        if isinstance(v, str):
            return v.strip()
        return v

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
            datetime.strptime(v, "%d/%m/%Y")
            return v
        except Exception:
            raise ValueError("dateOfBirth must be in DD/MM/YYYY format")

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

    @field_validator("interests", mode="before")
    def validate_interests(cls, v):
        if v is None:
            return []
        if isinstance(v, str):
            return [v.strip()]
        if isinstance(v, list):
            return [str(item).strip() for item in v]
        return []

class BuddyCreate(BuddyBase):
    pass

class BuddyUpdate(BaseModel):
    firstName: Optional[str] = None
    lastName: Optional[str] = None
    shortBio: Optional[str] = None
    consultationFee: Optional[int] = None
    availability: Optional[str] = None
    rating: Optional[float] = None
    reviewCount: Optional[int] = None

class BuddyResponse(BuddyBase):
    id: Optional[str] = Field(None, alias="_id")
    createdAt: Optional[datetime] = None
    updatedAt: Optional[datetime] = None

    class Config:
        populate_by_name = True
