from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import BaseModel, EmailStr, Field, HttpUrl, field_validator, model_validator, ValidationError
from typing import Optional
from datetime import date, datetime
import re
from app.models.enum import RoleEnum, GenderEnum, MaritalStatusEnum, BloodGroupEnum
from fastapi import UploadFile
from fastapi import Form
from pydantic import BaseModel
from typing import Type,List
import inspect
import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)

# app = FastAPI()
def as_form(cls: Type[BaseModel]):
    """
    Adds an `as_form` classmethod to Pydantic models
    so they can be used with Form(...) in FastAPI.
    """
    new_params = []
    for field_name, model_field in cls.model_fields.items():
        default = Form(...) if model_field.is_required() else Form(model_field.default)
        new_params.append(
            inspect.Parameter(
                field_name,
                inspect.Parameter.POSITIONAL_OR_KEYWORD,
                default=default,
                annotation=model_field.annotation,
            )
        )

    async def _as_form(**data):
        return cls(**data)

    sig = inspect.signature(_as_form).replace(parameters=new_params)
    _as_form.__signature__ = sig  # type: ignore
    setattr(cls, "as_form", _as_form)
    return cls




class PatientBase(BaseModel):
    firstName: Optional[str]
    lastName: Optional[str]
    dateOfBirth: Optional[date]=None
    gender: Optional[GenderEnum]=None
    age: Optional[int] = None
    phoneNumber: Optional[str]
    email: Optional[EmailStr]
    addressLine: Optional[str]
    maritalStatus: Optional[MaritalStatusEnum]
    bloodGroup: Optional[BloodGroupEnum]
    language: Optional[List[str]] = Field(default_factory=list)
    city: Optional[str]
    state: Optional[str]
    country: Optional[str]
    postalCode: Optional[str]
    disease: Optional[str]
    diagnosis: Optional[str]
    profilePhoto: Optional[str]


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

    @field_validator("phoneNumber")
    def validate_phone(cls, v: str):
        if v and not re.fullmatch(r"^\d{10}$", v):
            raise ValueError("Phone number must be 10 digits")
        return v

   
    @field_validator("dateOfBirth")
    def parse_date(cls, v):
        if isinstance(v, date):
            dob = v
        elif isinstance(v, str):
            for fmt in ("%Y-%m-%d", "%d-%m-%Y", "%d/%m/%Y"):
                try:
                    dob = datetime.strptime(v, fmt).date()
                    break
                except ValueError:
                    continue
            else:
                raise ValueError("Date of birth must be in format YYYY-MM-DD or DD-MM-YYYY")
        else:
            raise ValueError("Invalid date format")

        # ✅ Check if DOB is in the future
        if dob > date.today():
            raise ValueError("Date of birth cannot be in the future")

        return dob


    @field_validator("postalCode")
    def validate_postal(cls, v: str):
        if v and not re.fullmatch(r"^\d{6}$", v):
            raise ValueError("Postal code must be 6 digits")
        return v

    @field_validator("profilePhoto")
    def validate_profile_photo(cls, v):

        return v

    
   
    # @field_validator("maritalStatus")
    # def marital_status(cls,v:str):
    #     if v!=v.lower():
    #         raise ValidationError("maritalStatus must be in lowercase")
    #     else:
    #         return v

class PatientCreate(PatientBase):
    pass


@as_form
class PatientUpdate(PatientBase):
    pass



class Patient(PatientBase):
    patientId: str


class UserActionInfo(BaseModel):
    userId: Optional[str]  = None
    role: Optional[str]


from datetime import date

class PatientResponse(PatientBase):
    role: str
    id: str
    patientId: str
    createdAt: datetime = Field(default_factory=datetime.utcnow)
    updatedAt: datetime = Field(default_factory=datetime.utcnow)
    createdBy: UserActionInfo
    updatedBy: Optional[UserActionInfo] = None

    @model_validator(mode="after")
    def compute_age(self):
        if self.dateOfBirth:
            today = date.today()
            self.age = today.year - self.dateOfBirth.year - (
                (today.month, today.day) < (self.dateOfBirth.month, self.dateOfBirth.day)
            )
        return self





class PatientRegisterResponse(BaseModel):
    status: int
    message: str
    data: PatientResponse


class PatientResponseWrapper(BaseModel):
    status: int
    message: str
    data: Patient