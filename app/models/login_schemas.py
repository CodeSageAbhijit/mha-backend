from pydantic import BaseModel, EmailStr, validator, Field
from typing import Optional, List
from datetime import date, datetime
import re
from typing import Literal
from app.models.enum import RoleEnum, GenderEnum, AppointmentStatusEnum
from pydantic import BaseModel, Field
from typing import List, Optional
from pydantic import validator

class LoginUser(BaseModel):
    username: str
    role: RoleEnum
    password: str
    


class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class LoginResponse(BaseModel):
    status: int
    message: str
    data: dict

class LogoutResponse(BaseModel):
    status: int
    message: str
    error: Optional[str] = None

class LogoutRequest(BaseModel):
    refresh_token: str
    role: RoleEnum   


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str
    confirm_password: str

class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class OTPRequest(BaseModel):
    """Request OTP for login"""
    username: str
    role: RoleEnum
    password: str


class OTPVerifyRequest(BaseModel):
    """Verify OTP and get tokens"""
    username: str
    role: RoleEnum
    otp: str


class OTPResponse(BaseModel):
    """Response after OTP sent"""
    status: int
    message: str
    data: Optional[dict] = None
    error: Optional[str] = None