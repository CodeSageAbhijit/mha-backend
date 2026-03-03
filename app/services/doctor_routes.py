from fastapi import APIRouter, HTTPException, Depends, Query, UploadFile, File, Form, status
from bson import ObjectId
from app.database.mongo import psychiatrist_collection, counselor_collection, patient_collection, db, admin_collection
from fastapi import Body
from app.models.doctor_schemas import DoctorCreate
from datetime import datetime, date
from app.utils.dependencies import get_current_user, get_admin_user
from app.utils.email_utils import send_login_email
import bcrypt
from typing import Optional, Literal,List
from pydantic import EmailStr,ValidationError
from app.utils.id_generator import generate_custom_id
import os
from app.utils.constants import upload_profile_photo
from fastapi.security import OAuth2PasswordBearer
from app.utils.jwt_tokens import decrypt_token
from app.models.enum import GenderEnum
from app.utils.error_response import error_response,format_pydantic_errors
import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)



router = APIRouter(prefix="/api", tags=["Psychiatrist"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/login")
SECRET_KEY = os.getenv("SECRET_KEY", "mysecret")
ALGORITHM = "HS256"



async def get_current_user_local(token: str = Depends(get_admin_user)):
    """Local implementation to avoid conflicts with the imported one"""
    try:
        payload = decrypt_token(token)
        if payload.get("exp") < int(datetime.utcnow().timestamp()):
            raise HTTPException(status_code=401, detail="Token expired")

        user_id = payload.get("userId")
        role = payload.get("role")
        if not user_id or not role:
            raise HTTPException(status_code=401, detail="Invalid token payload")
        
        
        if role == "psychiatrist":
            user = await psychiatrist_collection.find_one({"_id": ObjectId(user_id)})
        elif role == "admin":
            user = await admin_collection.find_one({"_id": ObjectId(user_id)})
        else:
            raise HTTPException(status_code=401, detail="Only psychiatrist role supported in this example")

        if not user:
            raise HTTPException(status_code=401, detail="User not found")

        user["user_id"] = str(user["_id"])
        user["role"] = role
        return user

    except HTTPException:
        raise
    except Exception as e:
        print(f"Error in get_current_user_local: {e}")
        raise HTTPException(status_code=401, detail="Invalid token")


def to_response(doc: dict) -> dict:
    """Convert MongoDB document to JSON-serializable response"""
    if not doc:
        return None

    doc_copy = doc.copy()

    
    doc_copy["id"] = str(doc_copy.get("_id", ""))
    doc_copy.pop("_id", None)

    
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

    
    if "gender" in doc_copy and isinstance(doc_copy["gender"], GenderEnum):
        doc_copy["gender"] = doc_copy["gender"].value

    
    doc_copy.pop("password", None)
    doc_copy.pop("confirmPassword", None)

    return doc_copy


def convert_dates(data: dict):
    """Convert date objects to dd/mm/yyyy string format for MongoDB storage"""
    if "dateOfBirth" in data and isinstance(data["dateOfBirth"], date):
        data["dateOfBirth"] = data["dateOfBirth"].strftime("%d/%m/%Y")
    
    if "joiningDate" in data and isinstance(data["joiningDate"], date):
        data["joiningDate"] = data["joiningDate"].strftime("%d/%m/%Y")
    
    return data



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


@router.post("/create-doctor", status_code=201)
async def create_doctor(
    firstName: str = Form(...),
    lastName: str = Form(...),
    email: str = Form(...),
    dateOfBirth:str= Form(...),
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
    joiningDate: Optional[str] = Form(None),
    profilePhoto: UploadFile = File(None),
    termsAccepted: Optional[bool] = Form(False),
    current_user: dict = Depends(get_admin_user)
):
    try:
        

       
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
        else:
            joining_date_str = None
        if language:
           
            lang = [l.strip().strip('"') for l in language.split(",") if l.strip()]
        else:
            lang = []
        if specialization:
            
            spec= [s.strip().strip('"') for s in specialization.split(",") if s.strip()]
        else:
            spec = []    


        experience_years = safe_int_conversion(experienceYears)

        payload_dict = {
           
            "dateOfBirth": dob,
            "joiningDate": joining_date_str,
            "firstName": firstName,
            "lastName": lastName,
            "email": email,
            "phoneNumber": phoneNumber,
            "qualification": qualification,
            "designation": designation,
            "department": department,
            "gender":gender.strip().lower() if gender else None,
            "licenseNumber":licenseNumber,
            "language": lang,
            "shortBio": shortBio or "",
            "consultationMode": consultationMode or "",
            "city": city,
            "state": state,
            "country": country,
            "postalCode": postalCode,
            "addressLine":addressLine,
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

      
        try:
            payload = DoctorCreate(**payload_dict)
        except ValidationError as ve:
            main_error, errs = format_pydantic_errors(ve)
            return error_response(422, "Validation error", main_error, errs)

        formatted_dob = payload.dateOfBirth
        plain_password = f"{payload.firstName}@{formatted_dob}"
        hashed_password = bcrypt.hashpw(plain_password.encode("utf-8"), bcrypt.gensalt())

        doctor_id = await generate_custom_id("doctor")
        doctor_data = payload.dict()

        # Convert dateOfBirth and joiningDate to datetime for MongoDB storage
        if doctor_data.get("dateOfBirth"):
            doctor_data["dateOfBirth"] = datetime.strptime(doctor_data["dateOfBirth"], "%d/%m/%Y")
        if doctor_data.get("joiningDate"):
            doctor_data["joiningDate"] = datetime.strptime(doctor_data["joiningDate"], "%d/%m/%Y")
        doctor_data.update({
            "doctorId": doctor_id,
            "role": "psychiatrist",
            "username": doctor_id + "." + payload.firstName.lower(),
            "isActive": True,
            "isDeleted": False,
            "password": hashed_password.decode("utf-8"),
            "confirmPassword": hashed_password.decode("utf-8"),
            "experienceYears": experience_years,
            "createdAt": datetime.utcnow()
        })
        if await psychiatrist_collection.find_one({"username": doctor_data["username"]}):
            return error_response(400, "Username already exists", "Username already exists", [
                {"field": "username", "message": "Username already exists", "type": "value_error.duplicate"}
            ])
        if await psychiatrist_collection.find_one({"email": payload.email}):
            return error_response(400, "Email already exists", "Email already exists", [
                {"field": "email", "message": "Email already exists", "type": "value_error.duplicate"}
            ])

        result = await psychiatrist_collection.insert_one(doctor_data)
        doctor = await psychiatrist_collection.find_one({"_id": result.inserted_id})

        try:
            await send_login_email(
                to_email=payload.email,
                name=payload.firstName,
                login_id=doctor_data["username"],
                password=plain_password
            )
        except Exception as e:
            print(f"Email sending failed: {e}")

        return {
            "success": True,
            "status": 201,
            "message": "Doctor created successfully",
            "data": to_response(doctor),
            "error": None,
            "errors": []
        }

    except HTTPException:
        raise
    except Exception as e:
        return error_response(500, "Error creating doctor", str(e))


@router.put("/update-doctor/{doctorId}")
async def update_doctor(
    doctorId: str,
    firstName: Optional[str] = Form(None),
    lastName: Optional[str] = Form(None),
    email: Optional[str] = Form(None),
    dateOfBirth: Optional[str] = Form(None),
    phoneNumber: Optional[str] = Form(None),
    qualification: Optional[str] = Form(None),
    designation: Optional[str] = Form(None),
    department: Optional[str] = Form(None),
    gender: Optional[str] = Form(None),
    licenseNumber:str = Form(...),
    language:Optional[str] = Form(None),
    shortBio: Optional[str] = Form(None),
    consultationMode:str = Form(None),
    city: Optional[str] = Form(None),
    state: Optional[str] = Form(None),
    country: Optional[str] = Form(None),
    postalCode: Optional[str] = Form(None),
    addressLine : Optional[str] = Form(None),
    specialization: Optional[str] = Form(None),
    experienceYears: Optional[int] = Form(None),
    joiningDate: Optional[str] = Form(None),
    profilePhoto: Optional[UploadFile] = File(None),
    current_user: dict = Depends(get_current_user)
):
    try:
        existing_doctor = await psychiatrist_collection.find_one({"doctorId": doctorId.strip()})
        if not existing_doctor:
            return error_response(404, "Doctor not found", "DoctorNotFound", [])

        is_admin = current_user.get("role", "").strip().lower() == "admin"
        is_self = str(current_user.get("userId", "")).strip() == str(existing_doctor["_id"])
        if not (is_admin or is_self):
            return error_response(403, "Not authorized to update this doctor", "UnauthorizedError", [])

        update_data = {}
        if firstName: update_data["firstName"] = firstName.strip()
        if lastName: update_data["lastName"] = lastName.strip()
        if email: update_data["email"] = email.strip()
        if phoneNumber: update_data["phoneNumber"] = phoneNumber.strip()
        if qualification: update_data["qualification"] = qualification.strip()
        if designation: update_data["designation"] = designation.strip()
        if department: update_data["department"] = department.strip()
        if licenseNumber:update_data["licenseNumber"] = licenseNumber.strip()
        if language:
    
            update_data["language"] = [l.strip().strip('"') for l in language.split(",") if l.strip()]
        else:
            update_data["language"] = []
        if shortBio:update_data["shortBio"] = shortBio.strip()
        if consultationMode:update_data["consultationMode"] = consultationMode.strip()
        if gender: update_data["gender"] = gender.strip()
        if city: update_data["city"] = city.strip().lower()
        if state: update_data["state"] = state.strip()
        if country: update_data["country"] = country.strip()
        if addressLine: update_data["addressLine"] = addressLine.strip()
        if postalCode: update_data["postalCode"] = postalCode.strip()
        if specialization:
            update_data['specialization']= [s.strip().strip('"') for s in specialization.split(",") if s.strip()]
            
        else:
            update_data["specialization"]= []    
            
        if experienceYears is not None:
            try:
                exp_years = safe_int_conversion(experienceYears)
                if exp_years < 0:
                    return error_response(422, "Validation error", "experienceYears must be >= 0", [{"field": "experienceYears", "message": "experienceYears must be >= 0", "type": "value_error"}])
                update_data["experienceYears"] = exp_years
            except Exception:
                return error_response(422, "Validation error", "experienceYears must be an integer", [{"field": "experienceYears", "message": "experienceYears must be an integer", "type": "type_error.integer"}])

        if dateOfBirth:
            try:
                update_data["dateOfBirth"] = datetime.strptime(dateOfBirth, "%d/%m/%Y")
            except Exception:
                return error_response(422, "Validation error", f"Invalid date format for dateOfBirth: {dateOfBirth} format should be DD/MM/YYY", [])

        if joiningDate:
            try:
                update_data["joiningDate"] = datetime.strptime(joiningDate, "%d/%m/%Y")
            except Exception:
                return error_response(422, "Validation error", f"Invalid date format for joiningDate: {joiningDate}", [])

      
        if profilePhoto:
            try:
                contents = await profilePhoto.read()
                photo_url = upload_profile_photo(contents)
                if photo_url:
                    update_data["profilePhoto"] = photo_url
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
                return error_response(400, "Profile photo upload failed", str(e))
        print("updated data",update_data)    

        if not update_data:
            return error_response(400, "No data provided for update", "NoDataError", [])

        if email and email != existing_doctor.get("email"):
            if await psychiatrist_collection.find_one({"email": email, "doctorId": {"$ne": doctorId}}):
                return error_response(400, "Email already exists", "DuplicateEmailError", [{"field": "email", "message": "Email already exists", "type": "value_error.duplicate"}])

        update_data["updatedAt"] = datetime.utcnow()
        data = update_data

        await psychiatrist_collection.update_one({"doctorId": doctorId.strip()}, {"$set": data})
        updated_doc = await psychiatrist_collection.find_one({"doctorId": doctorId.strip()})

        return {
            "success": True,
            "status": 200,
            "message": "Doctor updated successfully",
            "data":to_response(updated_doc),
            "error": None,
            "errors": []
        }

    except HTTPException:
        raise
    except Exception as e:
        return error_response(500, "Error updating doctor", str(e))



@router.delete("/doctor/{doctorId}")
async def delete_doctor(doctorId: str,current_user:dict=Depends(get_admin_user)):
    try:
        
        result = await psychiatrist_collection.update_one(
            {"doctorId": doctorId.strip()},
            {"$set": {"isDeleted": True}}
        )

        if result.matched_count == 1:
            return {
                "status": 200,
                "message": f"Doctor with ID {doctorId} deactivated successfully",
                "data": None
            }

     
        return error_response(
            status_code=404,
            message="Doctor not found",
            error="Doctor Not Found",
            errors=[
                {
                    "field": "doctorId",
                    "message": "No doctor found with the given ID",
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




@router.get("/doctors")
async def list_doctors(
    query: Optional[str] = Query(None, description="Filter by doctor name or department"),
    experienceYears: Optional[int] = Query(None, description="Filter by minimum experienceYears in years"),
    isActive:Optional[bool]=Query(None,description="filter the doctor by active (true/false)"),
    isDeleted:Optional[bool]=Query(None,description="filter the doctor by active status(true/false)"),
    problemType: Optional[str] = Query(None, description="Filter by problem type (e.g., relationship, breakup, business, divorce, anxiety, depression, family, career)"),
    limit: int = Query(100, ge=1, le=100, description="Number of doctors per page"),
    page: int = Query(1, ge=1, description="Page number"),
    after_date: Optional[date] = Query(None, description="Show only doctors after this date (YYYY-MM-DD)"),
    after_field: Optional[str] = Query("createdAt", description="Field to apply after_date filter on"),
    sort_by_date_field: Optional[str] = Query(None, description="Date field to sort by (e.g., createdAt, joiningDate)"),
    sort_order: str = Query("desc", regex="^(asc|desc)$", description="Sort order: asc or desc"),
    current_user: dict = Depends(get_current_user)
):
    filters = {}
    if query:
        filters["$or"] = [
            {"firstName": {"$regex": query, "$options": "i"}},
            {"lastName": {"$regex": query, "$options": "i"}},
            {"department": {"$regex": query, "$options": "i"}},
            {"specialization": {"$regex": query, "$options": "i"}},
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
        filters["isActive"]=isActive
    if isDeleted is not None:
        filters["isDeleted"]=isDeleted
    else:
        filters["isDeleted"] = False

    skip = (page - 1) * limit

    
    sort_criteria = None
    if sort_by_date_field:
        sort_direction = 1 if sort_order == "asc" else -1
        sort_criteria = [(sort_by_date_field, sort_direction)]

    try:
        cursor = psychiatrist_collection.find(filters)
        if sort_criteria:
            cursor = cursor.sort(sort_criteria)
        cursor = cursor.skip(skip).limit(limit)
        doctors = []
        
        async for doc in cursor:
            try:
                doc = to_response(doc)
                experience_value = 0
                if "experienceYears" in doc and doc["experienceYears"] is not None:
                    experience_value = safe_int_conversion(doc["experienceYears"])
                elif "experienceYears" in doc and doc["experienceYears"] is not None:
                    experience_value = safe_int_conversion(doc["experienceYears"])
                doc["experienceYears"] = experience_value

                if isinstance(doc.get("specialization"), list):
                    doc["specialization"] = ", ".join(doc["specialization"])
                elif doc.get("specialization") is None:
                    doc["specialization"] = ""
                doctors.append(doc)
            except Exception as doc_error:
                print(f"Error processing doctor document {doc.get('_id', 'unknown')}: {doc_error}")
                continue

        total_count = await psychiatrist_collection.count_documents(filters)
        total_pages = (total_count + limit - 1) // limit

        return {
            "status": 200,
            "message": "Doctors list fetched successfully",
            "data": doctors,
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
        print(f"Error in list_doctors: {e}")
        return error_response(
            status_code=500,
            message="An error occurred while fetching doctors",
            error=str(e),
            errors=[]
        )


@router.get("/doctor/{doctorId}")
async def get_doctor_by_id(
    doctorId: str,
    current_user: dict = Depends(get_current_user)
):
    try:
        doctor = await psychiatrist_collection.find_one({"doctorId": doctorId})
        if not doctor:
            return error_response(
                status_code=404,
                message="Doctor not found",
                error="NotFoundError"
            )

        doc = to_response(doctor)
        if isinstance(doc.get("specialization"), list):
            doc["specialization"] = ", ".join(doc["specialization"])
        doc["experienceYears"] = (
            doc.get("experienceYears") 
            or int(doc.get("experienceYears") or 0)
        )

        return {
            "status": 200,
            "message": "Doctor details fetched successfully",
            "data": doc
        }

    except Exception as e:
        return error_response(
            status_code=500,
            message="Failed to fetch doctor details",
            error=str(e)
        )

    
