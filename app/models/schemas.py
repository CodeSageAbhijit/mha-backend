# from pydantic import BaseModel, EmailStr
# from typing import List, Optional
# from datetime import date

# class RegisterUser(BaseModel):
#     role: str
#     fullName: str
#     email: EmailStr
#     password: str
#     monbileNumber: str
#     gender: str


# from pydantic import BaseModel, EmailStr, validator, Field
# from fastapi import UploadFile,File
# from typing import Optional, List
# from datetime import date, datetime
# import re
# from app.models.enum import RoleEnum, GenderEnum, AppointmentStatusEnum
# from pydantic import BaseModel, Field
# from typing import List, Optional
# from pydantic import validator



# class RegisterUser(BaseModel):
#     role: RoleEnum
#     fullName: str
#     username: str
#     email: EmailStr
#     password: str
#     phoneNumber: str
#     gender: GenderEnum

#     dateOfBirth: date
#     qualification: Optional[str]
#     specialization: Optional[str]
#     experienceYears: Optional[int]
#     licenseNumber: Optional[str]
#     shortBio: Optional[str]

#     consultationMode: Optional[List[str]] = []
#     profilePhoto: Optional[str]
#     termsAccepted: bool
#     language: Optional[List[str]] = []

#     consultationMode: Optional[List[str]]
#     profilePhoto: Optional[str]
#     termsAccepted: bool
#     language: Optional[List[str]]

#     @validator("phoneNumber")
#     def validate_phone(cls, v):
#         digits = re.sub(r"\D", "", v)  # Remove non-digit characters
#         if not re.fullmatch(r"[6-9]\d{9}", digits):
#             raise ValueError("Phone number must be exactly 10 digits and start with 6, 7, 8, or 9.")
#         return digits

#     @validator("email")
#     def validate_gmail(cls, v):
#         if not v.endswith("@gmail.com"):
#             raise ValueError("Only Gmail addresses are allowed.")
#         return v

#     @validator("dateOfBirth")
#     def validate_dob(cls, v):
#         if v > date.today():
#             raise ValueError("Date of birth cannot be in the future.")
#         return v

#     @validator("termsAccepted")
#     def check_terms(cls, v):
#         if not v:
#             raise ValueError("You must accept the terms and conditions.")
#         return v

#     @validator("password")
#     def validate_password_strength(cls, v):
#         if len(v) < 8:
#             raise ValueError("Password must be at least 8 characters long.")
#         if not re.search(r"[A-Z]", v):
#             raise ValueError("Password must contain at least one uppercase letter.")
#         if not re.search(r"[a-z]", v):
#             raise ValueError("Password must contain at least one lowercase letter.")
#         if not re.search(r"\d", v):
#             raise ValueError("Password must contain at least one number.")
#         if not re.search(r"[@$!%*?&]", v):
#             raise ValueError("Password must contain at least one special character (@, $, !, %, *, ?, &).")
#         return v

    

# class LoginUser(BaseModel):
#     username: str
#     role: RoleEnum
#     password: str



# class RegisterResponse(BaseModel):
#     status: int
#     message: str
#     data: dict

# class LoginRequest(BaseModel):
#     email: EmailStr
#     password: str

# class LoginResponse(BaseModel):
#     status: int
#     message: str

#     data: dict

#     data: dict
    
# class AppointmentRequest(BaseModel):
#     patientName: str
#     doctorName: str
#     timeSlot: str
#     date: datetime

# class ConfirmationRequest(BaseModel):
#     appointmentId: str
#     status: AppointmentStatusEnum

# class AssessmentBase(BaseModel):
#     disease: str
#     age_group: str
#     question: str
#     options: List[str]

# class AssessmentCreate(AssessmentBase):
#     pass
    

# class AssessmentUpdate(AssessmentBase):
#     pass

# class AssessmentResponse(AssessmentBase):
#     id: str



# class DoctorBase(BaseModel):
#     firstName: str
#     lastName: str
#     username: str
#     email: EmailStr
#     dob: date
#     mobileNumber: str
#     education: str
#     designation: str
#     department: str
#     gender: str
#     city: str
#     state: str
#     country: str
#     postalCode: str
#     specialization: List[str]
#     experience: str
#     joiningDate: date
#     picture: Optional[str] = ""

# class DoctorCreate(DoctorBase):
#     pass

# class DoctorUpdate(DoctorBase):
#     pass