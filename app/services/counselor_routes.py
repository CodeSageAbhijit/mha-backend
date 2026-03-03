from fastapi import (
    APIRouter, Depends, HTTPException, BackgroundTasks,
    Query, Form, UploadFile, File, status
)
from typing import List, Optional, Literal
from datetime import datetime, date
from bson import ObjectId
from dotenv import load_dotenv
from pymongo.errors import PyMongoError
from pydantic import ValidationError, EmailStr,BaseModel
from app.models.counselor_schema import CounselorCreate
from app.database.mongo import counselor_collection
from app.utils.dependencies import get_current_user, get_admin_user
from app.utils.constants import hash_password, upload_profile_photo
from app.utils.email_utils import send_login_email
from app.utils.bson_helper import document_to_json
from app.utils.id_generator import generate_custom_id
from app.models.enum import GenderEnum

from app.utils.error_response import error_response,format_pydantic_errors
import warnings
import bcrypt
from pytz import timezone

warnings.filterwarnings("ignore", category=DeprecationWarning)

load_dotenv()

router = APIRouter(prefix="/api/counselors", tags=["Counselors"])

def generate_password_from_name_and_dob(full_name: str, dob):
    """Generate default password from first name and DOB"""
    first_name = full_name.strip().split(" ")[0].lower()
    try:
        if isinstance(dob, str):
            dob_dt = datetime.fromisoformat(dob)
        elif isinstance(dob, date) and not isinstance(dob, datetime):
            dob_dt = datetime.combine(dob, datetime.min.time())
        else:
            dob_dt = dob or datetime.utcnow()
    except Exception:
        dob_dt = datetime.utcnow()

    dob_str = dob_dt.strftime("%d%m%Y")
    return f"{first_name}@{dob_str}"

def safe_int_conversion(value, default=0):
    """
    Safely convert a value to an integer, handling None, strings, floats, etc.
    Prevents 'NoneType' or '.isdigit()' errors.
    """
    if value is None:
        return default

    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)
    if isinstance(value, str):
        value = value.strip().lower()
        if value in ["", "none", "null", "string"]:
            return default
        try:
            return int(float(value))
        except ValueError:
            return default
    try:
        return int(value)
    except (ValueError, TypeError):
        return default

def to_response(doc: dict) -> dict:
    """Convert MongoDB document to JSON-serializable response"""
    if not doc:
        return None

    doc_copy = doc.copy()

    # Convert ObjectId to string
    doc_copy["id"] = str(doc_copy.get("_id", ""))
    doc_copy.pop("_id", None)

    # Convert dates to ISO strings
    dob = doc_copy.get("dateOfBirth") or doc_copy.get("dob")
    if isinstance(dob, (datetime, date)):
        doc_copy["dateOfBirth"] = dob.isoformat()
    else:
        doc_copy["dateOfBirth"] = None

    joining = doc_copy.get("joiningDate")
    if isinstance(joining, (datetime, date)):
        doc_copy["joiningDate"] = joining.isoformat()
    else:
        doc_copy["joiningDate"] = None

    # Convert enums to string
    if "gender" in doc_copy and isinstance(doc_copy["gender"], GenderEnum):
        doc_copy["gender"] = doc_copy["gender"].value

    # Remove sensitive fields
    doc_copy.pop("password", None)
    doc_copy.pop("confirmPassword", None)

    return doc_copy

@router.post("/create-counselor", status_code=201)
async def create_counselor(
    firstName: str = Form(...),
    lastName: str = Form(...),
    email: str = Form(...),
    dateOfBirth: str = Form(...),  # expects DD/MM/YYYY
    phoneNumber: str = Form(...),
    qualification: str = Form(...),
    designation: str = Form(...),
    department: str = Form(...),
    gender: str = Form(...),
    licenseNumber: str = Form(...),
    language: Optional[str] = Form(None),
    shortBio: Optional[str] = Form(None),
    consultationMode: str = Form(None),
    city: str = Form(...),
    state: str = Form(...),
    country: str = Form(...),
    postalCode: str = Form(...),
    addressLine : str = Form(...),
    specialization: Optional[str] = Form(None),
    experienceYears: Optional[int] = Form(0),
    joiningDate: Optional[str] = Form(None),  # expects DD/MM/YYYY
    profilePhoto: UploadFile = File(None),
    termsAccepted: Optional[bool] = Form(False),
    current_user: dict = Depends(get_admin_user)
):
    try:
        

        # Convert dateOfBirth safely (DD/MM/YYYY)
        try:
            dob_date = datetime.strptime(dateOfBirth, "%d/%m/%Y").date()
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

        # Convert joiningDate safely (if provided, DD/MM/YYYY)
        joining_date_str = None
        if joiningDate:
            try:
                joining_date_obj = datetime.strptime(joiningDate, "%d/%m/%Y").date()
                joining_date_str = joining_date_obj.strftime("%d/%m/%Y")
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

        experience_years = safe_int_conversion(experienceYears)
        if language:
           
            lang = [l.strip().strip('"') for l in language.split(",") if l.strip()]
        else:
            lang = []
        if specialization:
            
            spec= [s.strip().strip('"') for s in specialization.split(",") if s.strip()]
        else:
            spec = []    
       

        payload_dict = {
            "firstName": firstName,
            "lastName": lastName,
            "email": email,
            "phoneNumber": phoneNumber,
            "qualification": qualification,
            "designation": designation,
            "department": department,
            "gender": gender.strip().lower() if gender else None,
            "licenseNumber": licenseNumber,
            "language": lang,
            "shortBio": shortBio or "",
            "consultationMode": consultationMode,
            "dateOfBirth": dob,
            "joiningDate": joining_date_str,
            "city": city,
            "state": state,
            "country": country,
            "postalCode": postalCode,
            "addressLine": addressLine,
            "specialization": spec,
            "experienceYears": experience_years,
            "profilePhoto": profilePhoto,
            "termsAccepted": termsAccepted
        }
        if profilePhoto:
            try:
                contents = await profilePhoto.read()
                photo_url = upload_profile_photo(contents)
                if photo_url:
                    payload_dict["profilePhoto"] = photo_url
                else:
                    return error_response(
                        500,
                        "Error uploading profile photo",
                        "Upload returned null/empty",
                        errors=[{
                            "field": "profilePhoto",
                            "message": "Profile photo upload failed",
                            "type": "upload_error"
                        }]
                    )
            except Exception as e:
                return error_response(
                    500,
                    "Error uploading profile photo",
                    str(e),
                    errors=[{
                        "field": "profilePhoto",
                        "message": str(e),
                        "type": "upload_exception"
                    }]
                )

        # Validate via Pydantic
        try:
            payload = CounselorCreate(**payload_dict)
        except ValidationError as ve:
            main_error, errs = format_pydantic_errors(ve)
            return error_response(422, "Validation error", main_error, errs)

        formatted_dob = payload.dateOfBirth
        plain_password = f"{payload.firstName}@{formatted_dob}"
        hashed_password = bcrypt.hashpw(plain_password.encode("utf-8"), bcrypt.gensalt())
        role="counselor"

        counselor_id = await generate_custom_id(role)
        counselor_data = payload.dict()

        # Convert dateOfBirth and joiningDate to datetime for MongoDB storage
        if counselor_data.get("dateOfBirth"):
            counselor_data["dateOfBirth"] = datetime.strptime(counselor_data["dateOfBirth"], "%d/%m/%Y")
        if counselor_data.get("joiningDate"):
            counselor_data["joiningDate"] = datetime.strptime(counselor_data["joiningDate"], "%d/%m/%Y")

        counselor_data.update({
            "counselorId": counselor_id,
            "role": "counselor",
            "username": counselor_id + "." + payload.firstName.lower(),
            "isActive": True,
            "isDeleted": False,
            "password": hashed_password.decode("utf-8"),
            "confirmPassword": hashed_password.decode("utf-8"),
            "experienceYears": experience_years,
            "createdAt": datetime.now(timezone("Asia/Kolkata")),
            "updatedAt": None,
            "createdBy": {
                "userId": current_user.get("userId") or "MHA-Admin",
                "role": current_user.get("role") or "admin",
            },
            "updatedBy": None,
        })

        # Unique checks
        if await counselor_collection.find_one({"username": counselor_data["username"]}):
            return error_response(400, "Username already exists", "Username already exists", [
                {"field": "username", "message": "Username already exists", "type": "value_error.duplicate"}
            ])
        if await counselor_collection.find_one({"email": payload.email}):
            return error_response(400, "Email already exists", "Email already exists", [
                {"field": "email", "message": "Email already exists", "type": "value_error.duplicate"}
            ])

        result = await counselor_collection.insert_one(counselor_data)
        counselor = await counselor_collection.find_one({"_id": result.inserted_id})

        try:
            await send_login_email(
                to_email=payload.email,
                name=payload.firstName,
                login_id=counselor_data["username"],
                password=plain_password
            )
        except Exception as e:
            print(f"Email sending failed: {e}")

        return {
            "success": True,
            "status": 201,
            "message": "Counselor created successfully",
            "data": to_response(counselor),
            "error": None,
            "errors": []
        }

    except HTTPException:
        raise
    except Exception as e:
        return error_response(500, "Error creating counselor", str(e))


@router.get("")
async def list_counselors(
    query: Optional[str] = Query(None, description="Filter by name, department, etc."),
    experienceYears: Optional[int] = Query(None, description="Filter by minimum experienceYears in years"),
    isActive: Optional[bool] = Query(None, description="Filter by active status (true/false)"),
    isDeleted: Optional[bool] = Query(None, description="Filter by deleted status (true/false)"),
    problemType: Optional[str] = Query(None, description="Filter by problem type (e.g., relationship, breakup, business, divorce, anxiety, depression, family, career)"),
    limit: int = Query(100, ge=1, le=100, description="Number of counselors per page"),
    page: int = Query(1, ge=1, description="Page number"),
    after_date: Optional[date] = Query(None, description="Show only counselors after this date"),
    after_field: Optional[str] = Query("createdAt", description="Field to apply after_date filter on"),
    sort_by_date_field: Optional[str] = Query(None, description="Date field to sort by (e.g., createdAt)"),
    sort_order: str = Query("desc", regex="^(asc|desc)$", description="Sort order: asc or desc"),
    current_user: dict = Depends(get_current_user)
):
    filters = {}
    if query:
        filters["$or"] = [
            {"firstName": {"$regex": query, "$options": "i"}},
            {"lastName": {"$regex": query, "$options": "i"}},
            {"qualification": {"$regex": query, "$options": "i"}},
            {"specialization": {"$regex": query, "$options": "i"}},
            {"department": {"$regex": query, "$options": "i"}},
            {"designation": {"$regex": query, "$options": "i"}},
            {"city": {"$regex": query, "$options": "i"}},
            {"state": {"$regex": query, "$options": "i"}},
            {"country": {"$regex": query, "$options": "i"}},
            {"counselorId": {"$regex": query, "$options": "i"}}
        ]
    if problemType:
        filters["problemTypes"] = {"$in": [problemType]}

    if experienceYears is not None:
        filters["$or"] = [
            {"experienceYears": {"$gte": experienceYears}},
            {"experienceYears": {"$gte": str(experienceYears)}}
        ]

    if after_date and after_field:
        after_datetime = datetime.combine(after_date, datetime.min.time())
        filters[after_field] = {"$gt": after_datetime}

    if isActive is not None:
        filters["isActive"] = isActive

    if isDeleted is not None:
        filters["isDeleted"] = isDeleted
    else:
        filters["isDeleted"] = False

    skip = (page - 1) * limit

    sort_criteria = None
    if sort_by_date_field:
        sort_direction = 1 if sort_order == "asc" else -1
        sort_criteria = [(sort_by_date_field, sort_direction)]

    try:
        cursor = counselor_collection.find(filters)
        if sort_criteria:
            cursor = cursor.sort(sort_criteria)
        cursor = cursor.skip(skip).limit(limit)

        counselors = []
        async for doc in cursor:
            try:
                doc = document_to_json(doc)

                # Safe Experience Handling
                experience_value = 0
                if "experienceYears" in doc and doc["experienceYears"] is not None:
                    try:
                        experience_value = int(doc["experienceYears"])
                    except:
                        experience_value = 0
                doc["experienceYears"] = experience_value

                # Format Specializations to CSV
                if isinstance(doc.get("specialization"), list):
                    doc["specialization"] = ", ".join(doc["specialization"])
                elif doc.get("specialization") is None:
                    doc["specialization"] = ""

                counselors.append(doc)
            except Exception as doc_error:
                print(f"Error processing counselor document {doc.get('_id', 'unknown')}: {doc_error}")
                continue

        total_count = await counselor_collection.count_documents(filters)
        total_pages = (total_count + limit - 1) // limit

        return {
            "status": 200,
            "message": "Counselors list fetched successfully",
            "data": counselors,
            "pagination": {
                "page": page,
                "limit": limit,
                "total_pages": total_pages,
                "total_count": total_count,
                "has_next": page < total_pages,
                "has_previous": page > 1
            }
        }

    except Exception as e:
        print(f"Error in list_counselors: {e}")
        return error_response(
            status_code=500,
            message="An error occurred while fetching counselors",
            error=str(e),
            errors=[]
        )


@router.get("/{counselor_id}")
async def get_counselor(counselor_id: str, current_user=Depends(get_current_user)):
    try:
        doc = await counselor_collection.find_one({"counselorId": counselor_id})
        if not doc:
            return error_response(404, "Counselor not found", "No record in database", [])
        return {
            "success": True,
            "status": 200,
            "message": "Counselor fetched successfully",
            "data": document_to_json(doc),
            "error": None,
            "errors": []
        }
    except Exception as e:
        return error_response(500, "Error fetching counselor", str(e))


def parse_date_safe(date_str: str):
    """Try to parse date in multiple formats, return None if invalid."""
    if not date_str:
        return None
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%Y-%m-%dT%H:%M:%S.%fZ", "%Y-%m-%dT%H:%M:%SZ"):
        try:
            return datetime.strptime(date_str, fmt).date()
        except ValueError:
            continue
    return None




@router.put("/{counselor_id}")
async def update_counselor(
    counselor_id: str,
    firstName: Optional[str] = Form(None),
    lastName: Optional[str] = Form(None),
    email: Optional[str] = Form(None),
    phoneNumber: Optional[str] = Form(None),
    gender: Optional[str] = Form(None),
    dateOfBirth: Optional[str] = Form(None),
    qualification: Optional[str] = Form(None),
    specialization: Optional[str] = Form(None),
    experienceYears: Optional[int] = Form(None),
    licenseNumber: Optional[str] = Form(None),
    shortBio: Optional[str] = Form(None),
    consultationMode: Optional[str] = Form(None),
    language: Optional[str] = Form(None),
    department: Optional[str] = Form(None),
    designation: Optional[str] = Form(None),
    state: Optional[str] = Form(None),
    country: Optional[str] = Form(None),
    postalCode: Optional[str] = Form(None),
    addressLine: Optional[str] = Form(None),
    city: Optional[str] = Form(None),
    joiningDate: Optional[str] = Form(None),
    profilePhoto: Optional[UploadFile] = File(None),
    current_user=Depends(get_current_user)
):
    try:
        # Fetch existing document
        existing_doc = await counselor_collection.find_one({"counselorId": counselor_id})
        if not existing_doc:
            return error_response(404, "Counselor not found", f"No counselor with ID {counselor_id}")
        if language:
            # Handles: "english,marathi", "english ,marathi", '"english","marathi"'
            lang = [l.strip().strip('"') for l in language.split(",") if l.strip()]
        else:
            lang = []
        if specialization:
            # Handles: "english,marathi", "english ,marathi", '"english","marathi"'
            spec= [s.strip().strip('"') for s in specialization.split(",") if s.strip()]
        else:
            spec= []            

        update_data = {
            "firstName": firstName,
            "lastName": lastName,
            "email": email,
            "phoneNumber": phoneNumber,
            "gender": gender.strip().lower() if gender else None,
            "dateOfBirth": dateOfBirth,
            "qualification": qualification,
            "specialization": spec,
            "experienceYears": experienceYears,
            "licenseNumber": licenseNumber,
            "shortBio": shortBio,
            "consultationMode": consultationMode.split(",") if consultationMode else None,
            "language": lang,
            "department": department,
            "designation": designation,
            "state": state,
            "country": country,
            "postalCode": postalCode,
            "city": city,
            "addressLine": addressLine,
            "joiningDate": joiningDate,
        }

        # ✅ Handle profile photo upload errors
        if profilePhoto:
            try:
                contents = await profilePhoto.read()
                update_data["profilePhoto"] = upload_profile_photo(contents)
            except Exception as fe:
                return error_response(400, "Profile photo upload failed", str(fe))

        # ✅ Remove None fields
        update_data = {k: v for k, v in update_data.items() if v is not None}

        # ✅ Validate dateOfBirth
        if "dateOfBirth" in update_data:
            try:
                dob = datetime.strptime(update_data["dateOfBirth"], "%d/%m/%Y").date()
                if dob > date.today():
                    return error_response(422, "Validation error", "Date of birth cannot be in the future", [
                        {"field": "dateOfBirth", "message": "Date of birth cannot be in the future", "type": "value_error"}
                    ])
            except Exception:
                return error_response(422, "Validation error", "dateOfBirth must be in DD/MM/YYYY format", [
                    {"field": "dateOfBirth", "message": "dateOfBirth must be in DD/MM/YYYY format", "type": "value_error"}
                ])

        # ✅ Validate joiningDate
        if "joiningDate" in update_data:
            try:
                jd = datetime.strptime(update_data["joiningDate"], "%d/%m/%Y").date()
                if jd > date.today():
                    return error_response(422, "Validation error", "joiningDate cannot be in the future", [
                        {"field": "joiningDate", "message": "joiningDate cannot be in the future", "type": "value_error"}
                    ])
            except Exception:
                return error_response(422, "Validation error", "joiningDate must be in DD/MM/YYYY format", [
                    {"field": "joiningDate", "message": "joiningDate must be in DD/MM/YYYY format", "type": "value_error"}
                ])

        # ✅ Other validations (email, names, experience, etc.)
        validation_errors = []
        if "email" in update_data:
            try:
                class _EmailCheck(BaseModel):
                    email: EmailStr
                _EmailCheck(email=update_data["email"])
            except ValidationError:
                validation_errors.append({
                    "field": "email",
                    "message": "value is not a valid email address",
                    "type": "value_error.email"
                })
        if "firstName" in update_data and (not update_data["firstName"] or not str(update_data["firstName"]).strip()):
            validation_errors.append({"field": "firstName", "message": "firstName is required", "type": "value_error"})
        if "lastName" in update_data and (not update_data["lastName"] or not str(update_data["lastName"]).strip()):
            validation_errors.append({"field": "lastName", "message": "lastName is required", "type": "value_error"})
        if "experienceYears" in update_data:
            try:
                if update_data["experienceYears"] is not None and int(update_data["experienceYears"]) < 0:
                    validation_errors.append({"field": "experienceYears", "message": "experienceYears must be >= 0", "type": "value_error"})
            except Exception:
                validation_errors.append({"field": "experienceYears", "message": "experienceYears must be an integer", "type": "type_error.integer"})

        if "username" in update_data:
            if update_data["username"] is not None and len(update_data["username"]) < 3:
                validation_errors.append({"field": "username", "message": "Username must be at least 3 characters long", "type": "value_error"})

        if addressLine is not None:
            update_data["addressLine"] = addressLine

        if validation_errors:
            main_err = validation_errors[0]["message"]
            return error_response(422, "Validation error", main_err, validation_errors)

        # ✅ Duplicate checks
        if "email" in update_data and update_data["email"] != existing_doc.get("email"):
            other = await counselor_collection.find_one({"email": update_data["email"]})
            if other:
                return error_response(400, "Email already registered", "Duplicate email", [
                    {"field": "email", "message": "Email already registered", "type": "value_error.duplicate"}
                ])

        if "username" in update_data and update_data["username"] != existing_doc.get("username"):
            other = await counselor_collection.find_one({"username": update_data["username"]})
            if other:
                return error_response(400, "Username already taken", "Duplicate username", [
                    {"field": "username", "message": "Username already taken", "type": "value_error.duplicate"}
                ])

        update_data.update({
            "updatedAt": datetime.utcnow(),
            "updatedBy": {
                "userId": current_user.get("userId") or "MHA-Admin",
                "role": current_user.get("role") or "admin",
            },
        })
        update_data.pop("counselorId", None)

        # ✅ DB update
        result = await counselor_collection.update_one(
            {"counselorId": counselor_id},
            {"$set": update_data}
        )

        if result.matched_count == 0:
            return error_response(404, "Counselor not found", f"No counselor with ID {counselor_id}")

        updated_doc = await counselor_collection.find_one({"counselorId": counselor_id})
        return {
            "success": True,
            "status": 200,
            "message": "Counselor updated successfully",
            "data": document_to_json(updated_doc),
            "error": None,
            "errors": []
        }

    except HTTPException:
        raise
    except Exception as e:
        return error_response(500, "Unexpected error while updating counselor", str(e))



@router.delete("/{counselor_id}", status_code=200)
async def delete_counselor(counselor_id: str, current_user=Depends(get_admin_user)):
    try:
        # Soft delete: update isActive to False instead of removing document
        result = await counselor_collection.update_one(
            {"counselorId": counselor_id.strip()},
            {"$set": {"isDeleted":True,"isActive":False}},
           
        )

        if result.matched_count == 1:
            return {
                "success": True,
                "status": 200,
                "message": f"Counselor with ID {counselor_id} deactivated successfully",
                "data": None,
                "error": None,
                "errors": []
            }

        # Counselor not found
        return error_response(
            status_code=404,
            message="Counselor not found",
            error="No counselor found with the given ID",
            errors=[
                {
                    "field": "counselorId",
                    "message": "No counselor found with the given ID",
                    "type": "not_found"
                }
            ]
        )

    except Exception as e:
        return error_response(
            status_code=500,
            message="Internal Server Error",
            error=str(e),
            errors=[]
        )
