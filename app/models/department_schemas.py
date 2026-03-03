from pydantic import BaseModel, EmailStr, validator, Field
from typing import Optional, List
from datetime import date, datetime
import re
from typing import Literal
from app.models.enum import RoleEnum, GenderEnum, AppointmentStatusEnum
from pydantic import BaseModel, Field
from typing import List, Optional
from pydantic import validator


class DepartmentBase(BaseModel):
    department: str
    departmentHead: str
    description: str
    status: str  # e.g., "active", "inactive"

class DepartmentCreate(DepartmentBase):
    pass

class DepartmentUpdate(DepartmentBase):
    pass

class DepartmentResponse(DepartmentBase):
    id: str
