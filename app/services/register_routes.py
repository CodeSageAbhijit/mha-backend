from fastapi import APIRouter, Form, UploadFile, File, HTTPException, status, Request
from pydantic import Field
from app.utils.constants import hash_password, upload_profile_photo
from app.utils.id_generator import generate_custom_id
from app.database.mongo import (
    psychiatrist_collection, counselor_collection, patient_collection, admin_collection,
    psychiatrist_collection, mentor_collection, business_coach_collection, buddy_collection
)
from app.utils.rate_limiter import limiter, RATE_LIMITS  # ✅ FIXED: Import rate limiter
from datetime import datetime
from typing import Optional, List
from pymongo.errors import PyMongoError


router = APIRouter(prefix="/api", tags=["Auth"])

# Helper for uniform error handling
def error_response(status_code: int, message: str, error: str, errors: list):
    raise HTTPException(
        status_code=status_code,
        detail={
            "success": False,
            "message": message,
            "data": None,
            "error": error,
            "errors": errors
        }
    )

@router.post("/register")
@limiter.limit(RATE_LIMITS["auth_register"])  # ✅ FIXED: Rate limit registration to 5/minute
async def register(request: Request,  # ✅ FIXED: Type hint for request parameter
    role: Optional[str] = Form(None),
    firstName: Optional[str] = Form(None),
    lastName: Optional[str] = Form(None),
    username: Optional[str] = Form(None),
    email: Optional[str] = Form(None),
    password: Optional[str] = Form(None),
    phoneNumber: Optional[str] = Form(None), 
    gender: Optional[str] = Form(None),
    maritalStatus: Optional[str] = Form(None),
    bloodGroup: Optional[str] = Form(None),
    dateOfBirth: Optional[str] = Form(None),
    joiningDate: Optional[str] = Form(None),
    qualification: Optional[str] = Form(None),
    specialization: Optional[str] = Form(None),  # will be sent as comma-separated string
    language: Optional[str] = Form(None),
    experienceYears: Optional[int] = Form(None),
    licenseNumber: Optional[str] = Form(None),
    shortBio: Optional[str] = Form(None),
    consultationMode: Optional[str] = Form(None),
    termsAccepted:Optional[bool] = Form(False),
    profilePhoto: Optional[UploadFile] = File(None),
 
):
    try:
        # Required fields
        if not role or not email or not username:
            error_response(
                status.HTTP_400_BAD_REQUEST,
                "Required fields missing",
                "role, email, and username are required",
                ["Missing required fields"]
            )

        # ✅ FIXED: Validate password length (bcrypt has 72-byte limit)
        if password and len(password.encode('utf-8')) > 72:
            error_response(
                status.HTTP_400_BAD_REQUEST,
                "Password too long",
                "Password cannot be longer than 72 bytes",
                ["Password exceeds maximum length of 72 bytes"]
            )

        # Validate role
        role = role.lower()
        valid_roles = ["psychiatrist", "mentor", "counselor", "business_coach", "buddy", "user", "admin", "superadmin"]
        if role not in valid_roles:
            error_response(
                status.HTTP_400_BAD_REQUEST,
                "Invalid role",
                f"Role must be one of: {', '.join(valid_roles)}",
                [f"Invalid role '{role}' provided"]
            )

        # Collection and prefix mapping
        role_map = {
            "psychiatrist": (psychiatrist_collection, "MHA-PSY", "psychiatristId"),
            "mentor": (mentor_collection, "MHA-M", "mentorId"),
            "counselor": (counselor_collection, "MHA-C", "counselorId"),
            "business_coach": (business_coach_collection, "MHA-BC", "businessCoachId"),
            "buddy": (buddy_collection, "MHA-B", "buddyId"),
            "user": (patient_collection, "MHA-P", "patientId"),
            "admin": (admin_collection, "MHA-A", "adminId"),
            "superadmin": (admin_collection, "MHA-SA", "superadminId")
        }
        target_collection, prefix, id_field = role_map[role]

        # Duplicate checks
        if await target_collection.find_one({"email": email}):
            error_response(
                status.HTTP_409_CONFLICT,
                "Email already registered",
                "Duplicate email",
                ["Email exists in database"]
            )
        if await target_collection.find_one({"username": username.strip().lower()}):
            error_response(
                status.HTTP_409_CONFLICT,
                "Username already taken",
                "Duplicate username",
                ["Username exists in database"]
            )

       
       
        # Only validate dateOfBirth if provided and not empty
        dob = None
        if dateOfBirth and dateOfBirth.strip():
            try:
                dob_date = datetime.strptime(dateOfBirth.strip(), "%d/%m/%Y").date()
                dob = dob_date.strftime("%d/%m/%Y") 
            except Exception:
                return error_response(
                    422,
                    "Validation error",
                    "Invalid date format for dateOfBirth, expected DD/MM/YYYY",
                    [
                        {
                            "field": "dateOfBirth",
                            "message": "Invalid date format, expected DD/MM/YYYY",
                            "type": "value_error.date",
                        }
                    ],
                )

       
        if joiningDate:
            try:
                joining_date_obj = datetime.strptime(joiningDate, "%d/%m/%Y").date()
                joiningDate = joining_date_obj.strftime("%d/%m/%Y")
            except Exception:
                return error_response(
                    422,
                    "Validation error",
                    "Invalid date format for joiningDate, expected DD/MM/YYYY",
                    [
                        {
                            "field": "joiningDate",
                            "message": "Invalid date format, expected DD/MM/YYYY",
                            "type": "value_error.date",
                        }
                    ],
                )
        else:
           joiningDate= None

      
        profilePhotoUrl = None
        if profilePhoto:
            try:
                profilePhotoUrl = upload_profile_photo(profilePhoto.file)
            except Exception as e:
                error_response(
                    status.HTTP_500_INTERNAL_SERVER_ERROR,
                    "Profile photo upload failed",
                    str(e),
                    ["Image upload error"]
                )


        # Generate custom ID
        try:
            customId = await generate_custom_id(role)

        except Exception as e:
            error_response(
                status.HTTP_500_INTERNAL_SERVER_ERROR,
                "Custom ID generation failed",
                str(e),
                ["ID generator error"]
            )

        # Format consultation modes and languages
      
        if language:
           
            lang = [l.strip().strip('"') for l in language.split(",") if l.strip()]
        else:
            lang = []
        if specialization:
            
            spec= [s.strip().strip('"') for s in specialization.split(",") if s.strip()]
        else:
            spec = []    

        
        user_data = {
            id_field: customId,
            "role": role,
            "firstName": firstName.strip() if firstName else None,
            "lastName": lastName.strip() if lastName else None,
            "username": username.strip().lower() if username else None,
            "email": email,
            "password": hash_password(password) if password else None,
            "phoneNumber": phoneNumber,
            "gender": gender.strip().lower() if gender else None,
            "maritalStatus": maritalStatus, #
            "bloodGroup": bloodGroup,#
            "dateOfBirth": dob,
            "joiningDate":joiningDate,
            "qualification": qualification,
            "specialization": spec,
            "experienceYears": experienceYears,
            "licenseNumber": licenseNumber,
            "shortBio": shortBio,
            "consultationMode": consultationMode or "",
            "language": lang,#
            "termsAccepted": termsAccepted,
            "profilePhoto": profilePhotoUrl,
            "createdBy": {          
                "role": "default"
            },
            "hasUsedFreeTrial": False,
            "createdAt": datetime.now(),
            "updatedAt": datetime.now(),
            "isActive": True,
            "isDeleted":False
        }

        if user_data.get("dateOfBirth"):
            user_data["dateOfBirth"] = datetime.strptime(user_data["dateOfBirth"], "%d/%m/%Y")
        if user_data.get("joiningDate"):
            user_data["joiningDate"] = datetime.strptime(user_data["joiningDate"], "%d/%m/%Y")
        try:
            result = await target_collection.insert_one(user_data)
        except Exception as e:
            error_response(
                status.HTTP_500_INTERNAL_SERVER_ERROR,
                "Database insert failed",
                str(e),
                ["MongoDB insert operation failed"]
            )

        return {
            "success": True,
            "message": f"{role.capitalize()} registered successfully",
            "data": {
                "id": str(result.inserted_id),
                id_field: customId,
                "email": email,
                "role": role
                # "isActive":True
            },
            "error": None,
            "errors": []
        }

    except HTTPException:
        raise
    except PyMongoError as e:
        error_response(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            "Database error",
            str(e),
            ["MongoDB error occurred"]
        )
    except Exception as e:
        error_response(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            "Registration failed",
            str(e),
            ["Unexpected error occurred"]
        )
