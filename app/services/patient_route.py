from fastapi import APIRouter, Depends, HTTPException, status, Form, File, UploadFile, Query,Request
from app.utils.constants import upload_profile_photo, serialize_patient, hash_password
from datetime import datetime, date
from pymongo.errors import PyMongoError, DuplicateKeyError, WriteError, OperationFailure
import traceback, random, string
from pytz import timezone
from app.utils.id_generator import generate_custom_id
from app.database.mongo import patient_collection
from app.models.patient_schemas import (
   
    PatientRegisterResponse,
    PatientResponse
)
from app.utils.auth_guard import get_current_user
from app.utils.dependencies import get_admin_user
from app.utils.email_utils import send_login_email
from typing import Optional,List
from app.utils.id_generator import generate_custom_id
from bson.errors import InvalidId
from fastapi.exceptions import RequestValidationError
from fastapi import FastAPI
from pydantic import ValidationError
from app.utils.error_response import error_response,format_pydantic_errors
from app.database.mongo import appointment_collection,prescription_collection, assessment_collection
from bson import ObjectId
from fastapi.responses import JSONResponse
router = APIRouter(prefix="/api/patients", tags=["Patient"])




# ...existing code...

# def error_response(
#     status_code: int,
#     message: str,
#     main_error: str,
#     errors: list = None,
#     field: str = None,
#     error_type: str = None
# ):
   
#     if field and error_type:
#         errors = errors or []
#         errors.append({
#             "field": field,
#             "message": message,
#             "type": error_type
#         })
#     return JSONResponse(
#         status_code=status_code,
#         content={
#             "detail": {
#                 "success": False,
#                 "status": status_code,
#                 "message": message,
#                 "data": None,
#                 "error": main_error,
#                 "errors": errors or []
#             }
#         }
#     )




# def convert_dates(data: dict):
#     """Convert date objects to datetime for MongoDB storage"""
#     if "dateOfBirth" in data and isinstance(data["dateOfBirth"], date):
#         data["dob"] = datetime.combine(data.pop("dateOfBirth"), datetime.min.time())

@router.post("", response_model=PatientRegisterResponse, status_code=201)
async def create_patient(
    firstName: str = Form(...),
    lastName: str = Form(...),
    dateOfBirth: str = Form(...),
    gender: str = Form(None),
    disease: str = Form(None),
    diagnosis: str = Form(None),
    phoneNumber: str = Form(...),
    language:Optional[str]=Form(None),
    city: str = Form(None),
    state: str = Form(None),
    country: str = Form(None),
    postalCode: str = Form(None),
    email: str = Form(...),
    addressLine: str = Form(None),
    maritalStatus: str = Form(None),
    bloodGroup: str = Form(None),
    profilePhoto: UploadFile = File(None),
    current_user: dict = Depends(get_current_user)
):
    try:
      
        if not firstName:
            return error_response(400, "Missing required fields", "firstName not mentioned")
        if not lastName:
            return error_response(400, "Missing required fields", "lastName not mentioned")
        if not dateOfBirth:
            return error_response(400, "Missing required fields", "dateOfBirth not mentioned")
        if gender is not None:
            gender_lower=gender.strip().lower()
        #     if gender.lower() not in ["male", "female", "other"]:
        #         return error_response(400, "Invalid gender value", "gender must be male/female/other")

        if not email:
            return error_response(400, "Missing required fields", "email not mentioned")    
           
        if len(phoneNumber) != 10 or not phoneNumber.isdigit():
            return error_response(400, "Invalid phone number", "Value error, Phone number must be 10 digits")
        if not profilePhoto:
            return error_response(400, "Missing required fields", "Profile photo not uploaded")
        if maritalStatus is not None:
            maritalStatus=maritalStatus.lower()

       # Convert date strings to date objects
        try:
            dob_datetime = datetime.strptime(dateOfBirth, "%d/%m/%Y")
        except Exception:
            return error_response(400, "Invalid date format for dateOfBirth, expected DD/MM/YYYY", [])

       

        patient_id = await generate_custom_id("user")
        login_id = patient_id

        raw_password = ''.join(random.choices(string.ascii_letters + string.digits, k=16))
        hashed_password = hash_password(raw_password)
        if language:
            # Handles: "english,marathi", "english ,marathi", '"english","marathi"'
            lang = [l.strip().strip('"') for l in language.split(",") if l.strip()]
        else:
            lang = []

        patient_data = {
             "isDeleted": False,
            "isActive": True,
            "patientId": patient_id,
            "role": "user",
            "firstName": firstName,
            "lastName": lastName,
            "dateOfBirth": dob_datetime,
            "gender": gender_lower,
            "phoneNumber": phoneNumber,
            "email": email,
            "username": login_id.lower(),
            "password": hashed_password,
            "addressLine": addressLine,
            "language": lang,
            "city": city ,
            "state": state ,
            "country": country ,
            "postalCode": postalCode ,
            "maritalStatus": maritalStatus ,
            "bloodGroup": bloodGroup ,
            "disease": disease ,
            "diagnosis": diagnosis ,
            "profilePhoto": "",
            "createdAt": datetime.now(timezone("Asia/Kolkata")),
            "updatedAt": datetime.now(timezone("Asia/Kolkata")),
            "createdBy": {
                "userId": current_user.get("userId") or "MHA-Admin",
                "role": current_user.get("role") or "admin",
            },
            "updatedBy": None,
        }

       
        try:
            PatientResponse(**patient_data, id=str(patient_id))
        except ValidationError as e:
            main_error, errors = format_pydantic_errors(e)
            return error_response(400, "Validation error in patient data", main_error, errors)
          
       

       
        if profilePhoto:
            contents = await profilePhoto.read()
            patient_data["profilePhoto"] = upload_profile_photo(contents)

              
      
        try:
           
            existing_email = await patient_collection.find_one({"email": patient_data["email"]})
           
            if existing_email:
                return error_response(
                    400,
                    "Registration failed",
                    "Email already registered",
                    errors=[{"field": "email", "message": "Email already registered", "type": "value_error.duplicate"}]
                )
            
            result = await patient_collection.insert_one(patient_data)

        except DuplicateKeyError as e:
            
            # Detect which field caused duplication
            if "email" in str(e):
                return error_response(
                    400,
                    "Registration failed",
                    "Email already registered",
                    errors=[{"field": "email", "message": "Email already registered", "type": "value_error.duplicate"}]
                )
            else:
                return error_response(500, "Database error while creating patient", "Duplicate key error")

        except (WriteError, PyMongoError) as e:
            return error_response(500, "Database error while creating patient", str(e))


        # --- Step 6: Send login email ---
        try:
            await send_login_email(
                to_email=email,
                name=f"{firstName} {lastName}",
                login_id=patient_data["username"],
                password=raw_password,
            )
        except Exception as e:
            return error_response(500, "Error sending login email", str(e))

        return PatientRegisterResponse(
            status=201,
            message="Patient registered successfully",
            data=PatientResponse(**patient_data, id=str(result.inserted_id))
        )

    except Exception as e:
        return error_response(500, "Unexpected error", str(e))
  
@router.get("")
async def list_patients(
    page: int = Query(1, ge=1),
    limit: int = Query(100, ge=1, le=100),
    query: Optional[str] = Query(None),
    isActive: Optional[bool] = Query(None, description="Filter by active status (true/false)"),
    isDeleted: Optional[bool] = Query(False, description="Filter by deleted status (true/false)"),
    sort_by_date_field: Optional[str] = Query(None, description="Date field to sort by (e.g., createdAt, updatedAt, dateOfBirth)"),
    sort_order: str = Query("desc", regex="^(asc|desc)$", description="Sort order: asc or desc"),
    after_date: Optional[date] = Query(None, description="Show only patients after this date (YYYY-MM-DD)"),
    after_field: Optional[str] = Query("createdAt", description="Field to apply after_date filter on"),
    createdByUserId: Optional[str] = Query(None, description="Filter by creator's userId"),
    createdByRole: Optional[str] = Query(None, description="Filter by creator's role"),
):
    try:
        skip = (page - 1) * limit
        mongo_query = {}

     
        if query:
            mongo_query["$or"] = [
                {"firstName": {"$regex": query, "$options": "i"}},
                {"lastName": {"$regex": query, "$options": "i"}}
            ]

        if after_date and after_field:
            after_datetime = datetime.combine(after_date, datetime.min.time())
            mongo_query[after_field] = {"$gt": after_datetime}
  
        if createdByUserId is not None:
            mongo_query["createdBy.userId"] = createdByUserId

        if createdByRole is not None:
            mongo_query["createdBy.role"] = createdByRole

      
        if isActive is not None:
            mongo_query["isActive"] = isActive
        if isDeleted is not None:
            mongo_query["isDeleted"] = isDeleted
        else:
            mongo_query["isDeleted"] = False
      
        try:
            total_count = await patient_collection.count_documents(mongo_query)
        except (PyMongoError, OperationFailure) as e:
            traceback.print_exc()
            return error_response(500, "Database error while counting patients", str(e), [])

        total_pages = (total_count + limit - 1) // limit

    
        sort_criteria = None
        if sort_by_date_field:
            sort_direction = 1 if sort_order == "asc" else -1
            sort_criteria = [(sort_by_date_field, sort_direction)]


       
        try:
            patients_cursor = patient_collection.find(mongo_query)
            if sort_criteria:
                patients_cursor = patients_cursor.sort(sort_criteria)
            patients_cursor = patients_cursor.skip(skip).limit(limit)
        except (PyMongoError, OperationFailure) as e:
            traceback.print_exc()
            return error_response(500, "Database error while fetching patients", str(e), [])

       
        patients = []
        async for p in patients_cursor:
            patient_data = serialize_patient(p)
            if isinstance(patient_data.get("dateOfBirth"), datetime):
                patient_data["dateOfBirth"] = patient_data["dateOfBirth"].strftime("%Y-%m-%d")
            patients.append(patient_data)

        return {
            "status": 200,
            "message": "Patients fetched successfully",
            "pagination": {
                "total_records": total_count,
                "total_pages": total_pages,
                "current_page": page,
                "limit": limit
            },
            "data": patients
        }
    except Exception as e:
        traceback.print_exc()
        return error_response(500, "Error fetching patients", str(e), [])

        
@router.get("/{patientId}", response_model=PatientRegisterResponse)
async def get_patient(patientId: str):
    try:
        try:
            patient = await patient_collection.find_one({"patientId": patientId})
        except (PyMongoError, OperationFailure) as e:
            traceback.print_exc()
            return error_response(500, "Database error while fetching patient", str(e), [])

        if not patient:
            return error_response(404, "Patient not found", "NotFoundError", [])

        patient_data = serialize_patient(patient)
        response_data = PatientResponse(**patient_data)

        return PatientRegisterResponse(
            status=200,
            message="Patient fetched successfully",
            data=response_data
        )

    except Exception as e:
        traceback.print_exc()
        return error_response(500, "Error fetching patient", str(e), [])

@router.put("/{patientId}")
async def update_patient(
    patientId: str,
    firstName: str = Form(None),
    lastName: str = Form(None),
    dateOfBirth: str = Form(None),
    gender: str = Form(None),
    disease: str = Form(None),
    diagnosis: str = Form(None),
    phoneNumber: str = Form(None),
    language:Optional[str] = Form(None),
    city: str = Form(None),
    state: str = Form(None),
    country: str = Form(None),
    postalCode: str = Form(None),
    email: str = Form(None),
    addressLine: str = Form(None),
    maritalStatus: str = Form(None),
    bloodGroup: str = Form(None),
    profilePhoto: UploadFile = File(None),
    current_user: dict = Depends(get_current_user)
):
    try:
        # --- Step 1: Build update dict only with provided fields ---
        update_data = {}
        
        if firstName is not None:
            update_data["firstName"] = firstName
        if lastName is not None:
            update_data["lastName"] = lastName
        if dateOfBirth is not None:
            try:
                if isinstance(dateOfBirth, str):
                    dob_datetime = datetime.strptime(dateOfBirth, "%d/%m/%Y")
                else:
                    dob_datetime = datetime.combine(dateOfBirth, datetime.min.time())
                update_data["dateOfBirth"] = dob_datetime
                
            except Exception:
                return error_response(400, "Invalid date of birth", "Date of birth parsing failed")  # ✅ auto update
        if gender is not None:
            update_data["gender"] = gender.strip().lower()

                            
        if disease is not None:
            update_data["disease"] = disease
        if diagnosis is not None:
            update_data["diagnosis"] = diagnosis
        if phoneNumber is not None:
            if len(phoneNumber) != 10 or not phoneNumber.isdigit():
                return error_response(400, "Invalid phone number", "Phone number must be 10 digits")
            update_data["phoneNumber"] = phoneNumber
        if language:
            # Handles: "english,marathi", "english ,marathi", '"english","marathi"'
            update_data["language"] = [l.strip().strip('"') for l in language.split(",") if l.strip()]
        else:
            update_data["language"] = []

        if city is not None:
            update_data["city"] = city
        if state is not None:
            update_data["state"] = state
        if country is not None:
            update_data["country"] = country
        if postalCode is not None:
            if len(postalCode) != 6 or not postalCode.isdigit():
                return error_response(400, "Invalid postal code", "Postal code must be 6 digits")
            update_data["postalCode"] = postalCode
        if email is not None:
            existing_email = await patient_collection.find_one({"email": email, "patientId": {"$ne": patientId}})
            if existing_email:
                return error_response(
                    400,
                    "Email already registered",
                    "Duplicate email",
                    errors=[{"field": "email", "message": "Email already registered", "type": "value_error.duplicate"}]
                )
            update_data["email"] = email
        if addressLine is not None:
            update_data["addressLine"] = addressLine
        if maritalStatus is not None:
            update_data["maritalStatus"] = maritalStatus
        if bloodGroup is not None:
            update_data["bloodGroup"] = bloodGroup

        if profilePhoto:
            try:
                contents = await profilePhoto.read()
                photo_url = upload_profile_photo(contents)
                if not photo_url:
                    return error_response(500, "Error uploading profile photo", "Upload returned null/empty")
                update_data["profilePhoto"] = photo_url
            except Exception as e:
                traceback.print_exc()
                return error_response(500, "Error uploading profile photo", str(e))
                

        # --- Step 3: Add audit fields ---
        update_data["updatedAt"] = datetime.utcnow()
        update_data["updatedBy"] = {
            "userId": current_user.get("userId"),
            "role": current_user.get("role") or "admin"
        }

        # --- Step 4: Perform update ---
        result = await patient_collection.update_one(
            {"patientId": patientId},
            {"$set": update_data}
        )
        update_data["createdBy"] = {
        "userId": current_user.get("userId"),
        "role": current_user.get("role", "default")
        }

        if result.matched_count == 0:
            return error_response(404, "Patient not found", "NotFoundError")
        updated_patient = await patient_collection.find_one({"patientId": patientId})
        if not updated_patient:
            return error_response(404, "Patient not found after update", "NotFoundError")
        patient_data = serialize_patient(updated_patient)
        

        return {"status":200,
                "message": "Patient updated successfully",
                "data": PatientResponse(**patient_data)}

    except Exception as e:
        traceback.print_exc()
        return error_response(500, "Error updating patient", str(e))



@router.delete("/{patientId}", status_code=200)
async def delete_patient(patientId: str,current_user: dict = Depends(get_admin_user)):
    try:
        result = await patient_collection.update_one(
            {"patientId": patientId},   
            {
                "$set": {
                    "isDeleted": True,
                    "updatedAt": datetime.utcnow(),
                }
            }
        )

        if result.matched_count == 0:
            return error_response(
                404,
                "Patient not found",
                "No record in database",
                []
            )

        return {"detail": f"Patient {patientId} soft deleted successfully"}

    except InvalidId:
        return error_response(
            400,
            "Invalid patient ID format",
            "ObjectId parsing error",
            [f"Invalid ID: {patientId}"]
        )
    except Exception as e:
        return error_response(
            500,
            "Error deleting patient",   
            str(e),
            []
        )



def serialize_mongo_doc(doc: dict) -> dict:
    """Convert MongoDB document into JSON-serializable dict."""
    if not doc:
        return None
    doc = dict(doc)
    for k, v in doc.items():
        if isinstance(v, ObjectId):
            doc[k] = str(v)
        elif isinstance(v, datetime):
            doc[k] = v.isoformat()
    return doc



@router.get("/{patientId}/history")
async def get_patient_history(
    patientId: str,
    include_appointments: bool = Query(True, description="Include appointments history"),
    include_prescriptions: bool = Query(True, description="Include prescriptions history"),
    include_assessments: bool = Query(True, description="Include assessment history")
):
    try:
        history = {"patientId": patientId}

        # Fetch appointments
        if include_appointments:
            appointments_cursor = appointment_collection.find({"patientId": patientId})
            history["appointments"] = [serialize_mongo_doc(appt) async for appt in appointments_cursor]

        # Fetch prescriptions
        if include_prescriptions:
            prescriptions_cursor = prescription_collection.find({"patientId": patientId})
            history["prescriptions"] = [serialize_mongo_doc(pres) async for pres in prescriptions_cursor]

        patient = await patient_collection.find_one({"patientId": patientId})
        print("patient",patient)
        if not patient:
            return error_response(404, "Patient not found", "NotFound", [])

        # ✅ Use userId (from patient doc) to find assessments
        user_id = str(patient["_id"])

        if not user_id or not ObjectId.is_valid(user_id):
            return error_response(400, "Patient has no valid userId", "MissingUserId", [])
        if include_assessments:
            assessments_cursor = assessment_collection.find({"userId":user_id})
            history["assessments"] = [serialize_mongo_doc(assess) async for assess in assessments_cursor]


        return {
            "status": 200,
            "message": "Patient history fetched successfully",
            "data": history
        }

    except Exception as e:
        traceback.print_exc()
        return error_response(500, "Error fetching patient history", str(e))
