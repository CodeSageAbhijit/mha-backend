from enum import Enum
from typing import Any
from pydantic import BaseModel
from typing import Literal


class CaseInsensitiveEnum(str, Enum):
    @classmethod
    def _missing_(cls, value: Any):
        """Allows case-insensitive matching for Enum values."""
        if isinstance(value, str):
            value_lower = value.lower()
            for member in cls:
                if member.value == value_lower:
                    return member
        raise ValueError(f"Invalid value '{value}' for enum {cls.__name__}")


class RoleEnum(CaseInsensitiveEnum):
    psychiatrist = "psychiatrist"
    counselor = "counselor"
    mentor = "mentor"
    business_coach = "business_coach"
    buddy = "buddy"
    user = "user"
    admin = "admin"


# class GenderEnum(CaseInsensitiveEnum):
#     male = "male"
#     female = "female"
#     other = "other"


class AppointmentStatusEnum(CaseInsensitiveEnum):
    pending = "pending"
    confirmed = "confirmed"
    rejected = "rejected"
    completed = "completed"


class ConsultationModeEnum(CaseInsensitiveEnum):
    online = "online"
    offline = "in-person"
    both = "both"
class GenderEnum(str, Enum):
    male = "male"
    female = "female"
    other = "other"

class MaritalStatusEnum(str, Enum):
    single = "single"
    married = "married"
    divorced = "divorced"
    widowed = "widowed"
class BloodGroupEnum(str, Enum):
    A_pos = "A+"
    A_neg = "A-"
    B_pos = "B+"
    B_neg = "B-"
    AB_pos = "AB+"
    AB_neg = "AB-"
    O_pos = "O+"
    O_neg = "O-"
