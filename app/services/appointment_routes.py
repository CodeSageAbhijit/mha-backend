from fastapi import APIRouter, HTTPException, Body, Depends, Query, status
from typing import Optional
from bson import ObjectId
from app.utils.dependencies import get_current_user
from app.utils.error_response import error_response
from app.models.appointment_schemas import AppointmentCreation, AppointmentStatusEnum, ConfirmationRequest, RescheduleRequest
from datetime import datetime, time
from pymongo.errors import PyMongoError
from uuid import uuid4
from pytz import timezone
from app.database.mongo import appointment_collection, patient_collection, psychiatrist_collection,counselor_collection,admin_collection
from app.utils.dependencies import get_current_user,get_admin_user
from app.utils.auth_guard import require_roles
from bson import ObjectId
from app.utils.error_response import error_response  
from app.models.appointment_schemas import AppointmentCreation,AppointmentCreationCounsolor
from datetime import datetime, timedelta
router = APIRouter(prefix="/api", tags=["Appointments"])



@router.post("/appointments")
async def create_appointment(
    appointment: AppointmentCreation = Body(...),
    current_user: dict = Depends(require_roles(['admin',  "psychiatrist"])) 
):
    try:
        patient_exists = await patient_collection.find_one({"patientId": appointment.patientId})
        if not patient_exists:
            return error_response(404, "Patient does not exist.", "Not Found", ["patientId invalid"])

        psychiatrist_exists = await psychiatrist_collection.find_one({"psychiatristId": appointment.doctorId})
        if not psychiatrist_exists:
            return error_response(404, "Psychiatrist does not exist.", "Not Found", ["psychiatristId invalid"])

        appointment_id = str(uuid4())
        status_value = appointment.status.value if hasattr(appointment.status, "value") else str(appointment.status)
        status_value = status_value.upper() if isinstance(status_value, str) else status_value

        appointment_data = {
            "appointment_id": appointment_id,
            "patientId": appointment.patientId,
            "doctorId": appointment.doctorId,
            #"timeSlot": appointment.timeSlot,
            "startTime": appointment.startTime,
            "endTime": appointment.endTime,
            "date": appointment.date,
            "reasonForVisit": appointment.reasonForVisit,
            "status": status_value,
            "consultationMode": appointment.consultationMode.value,  # ✅ store mode
            "createdAt": datetime.now(timezone("Asia/Kolkata")),
            "updatedAt": datetime.now(timezone("Asia/Kolkata")),
            "createdBy": {
                "userId": current_user.get("userId"),
                "role": current_user.get("role")
            },
            "updatedBy": None
        }


        result = await appointment_collection.insert_one(appointment_data)

        if not result.acknowledged:
            return error_response(500, "Failed to create appointment", "Database Error", [])

        created_doc = await appointment_collection.find_one({"_id": result.inserted_id})
        if created_doc and isinstance(created_doc.get("date"), datetime):
            india_tz = timezone("Asia/Kolkata")
            created_doc["date"] = created_doc["date"].astimezone(india_tz).strftime("%Y-%m-%d %I:%M %p")
        created_doc["_id"] = str(created_doc["_id"])

        return {
            "message": "Appointment created successfully",
            "appointment_id": appointment_id,
            "details": created_doc
        }

    except PyMongoError as e:
        return error_response(500, "Database error", str(e), [])
    except Exception as e:
        return error_response(500, "Unexpected error", str(e), [])
    

@router.post("/appointments-counselor")
async def create_counselor_appointment(
    appointment: AppointmentCreationCounsolor = Body(...),
    current_user: dict = Depends(require_roles(['admin', "counselor"])) 
):
    try:
        # ✅ Check if patient exists
        patient_exists = await patient_collection.find_one({"patientId": appointment.patientId})
        if not patient_exists:
            return error_response(404, "Patient does not exist.", "Not Found", ["patientId invalid"])

        # Make sure this field matches your DB schema
        counselor_exists = await counselor_collection.find_one({"counselorId": appointment.counselorId})

        if not counselor_exists:
            return error_response(404, "Counselor does not exist.", "Not Found", ["counselorId invalid"])

        appointment_id = str(uuid4())

        # ✅ Normalize status
        status_value = appointment.status.upper() if isinstance(appointment.status, str) else str(appointment.status)

        # ✅ Prepare appointment data
        appointment_data = {
            "appointment_id": appointment_id,
            "patientId": appointment.patientId,
            "counselorId": appointment.counselorId,
            #"timeSlot": appointment.timeSlot,
            "startTime": appointment.startTime,
            "endTime": appointment.endTime,
            "date": appointment.date,
            "reasonForVisit": appointment.reasonForVisit,
            "status": status_value,
            "createdAt": datetime.now(timezone("Asia/Kolkata")),
            "updatedAt": datetime.now(timezone("Asia/Kolkata")),
            "createdBy": {
                "userId": current_user.get("userId"),
                "role": current_user.get("role")
            },
            "updatedBy": None
        }

        # ✅ Insert into DB
        result = await appointment_collection.insert_one(appointment_data)
        if not result.acknowledged:
            return error_response(500, "Failed to create appointment", "Database Error", [])

        # ✅ Fetch back the created document
        created_doc = await appointment_collection.find_one({"_id": result.inserted_id})
        if created_doc and isinstance(created_doc.get("date"), datetime):
            india_tz = timezone("Asia/Kolkata")
            created_doc["date"] = created_doc["date"].astimezone(india_tz).strftime("%Y-%m-%d %I:%M %p")
        created_doc["_id"] = str(created_doc["_id"])

        return {
            "message": "Counselor appointment created successfully",
            "appointment_id": appointment_id,
            "details": created_doc
        }

    except PyMongoError as e:
        return error_response(500, "Database error", str(e), [])
    except Exception as e:
        return error_response(500, "Unexpected error", str(e), [])


# from fastapi import APIRouter, Body, Depends, HTTPException
# from pymongo.errors import PyMongoError
# from uuid import uuid4
# from datetime import datetime
# from pytz import timezone

# from app.database.mongo import patient_collection, counsellor_collection, appointment_collection
# from app.models.appointment_schemas import AppointmentCreationCounselor
# from app.utils.auth_guard import require_roles, error_response


# # ✅ Helper for structured error response
# def error_response(status_code: int, message: str, errors: list = None):
#     return HTTPException(
#         status_code=status_code,
#         detail={
#             "message": message,
#             "errors": errors or []
#         }
#     )

# @router.post("/appointments/counselor/")
# async def create_counselor_appointment(
#     appointment: AppointmentCreationCounselor = Body(...),
#     current_user: dict = Depends(require_roles(['admin', 'counselor']))
# ):
#     try:
#         # Normalize patientId and counselorId if sent as {value, label}
#         patientId = appointment.patientId["value"] if isinstance(appointment.patientId, dict) else appointment.patientId
#         counselorId = appointment.counselorId["value"] if isinstance(appointment.counselorId, dict) else appointment.counselorId

#         # Check patient exists
#         patient_exists = await patient_collection.find_one({"patientId": patientId})
#         if not patient_exists:
#             raise error_response(404, "Patient does not exist.", ["patientId invalid"])

#         # Check counselor exists
#         counselor_exists = await counsellor_collection.find_one({"counselorId": counselorId})
#         if not counselor_exists:
#             raise error_response(404, "Counselor does not exist.", ["counselorId invalid"])

#         appointment_id = str(uuid4())

#         # Prepare appointment data
#         appointment_data = {
#             "appointment_id": appointment_id,
#             "patientId": patientId,
#             "counselorId": counselorId,
#             "timeSlot": appointment.timeSlot,
#             "date": appointment.date,
#             "reasonForVisit": appointment.reasonForVisit,
#             "status": appointment.status.upper() if isinstance(appointment.status, str) else str(appointment.status),
#             "createdAt": datetime.now(timezone("Asia/Kolkata")),
#             "updatedAt": datetime.now(timezone("Asia/Kolkata")),
#             "createdBy": {
#                 "userId": current_user.get("userId"),
#                 "role": current_user.get("role")
#             },
#             "updatedBy": None
#         }

#         # Insert into DB
#         result = await appointment_collection.insert_one(appointment_data)
#         if not result.acknowledged:
#             raise error_response(500, "Failed to create appointment")

#         created_doc = await appointment_collection.find_one({"_id": result.inserted_id})
#         if created_doc and isinstance(created_doc.get("date"), datetime):
#             india_tz = timezone("Asia/Kolkata")
#             created_doc["date"] = created_doc["date"].astimezone(india_tz).strftime("%Y-%m-%d %I:%M %p")
#         created_doc["_id"] = str(created_doc["_id"])

#         return {
#             "message": "Counselor appointment created successfully",
#             "appointment_id": appointment_id,
#             "details": created_doc
#         }

#     except PyMongoError as e:
#         raise error_response(500, "Database error", [str(e)])
#     except Exception as e:
#         raise error_response(500, "Unexpected error", [str(e)])

# @router.post("/appointments-counselor")
# async def create_appointment_counselor(
#     appointment: AppointmentCreationCounselor = Body(...),
#     current_user: dict = Depends(require_roles(['admin', "counselor", "doctor"])) 
# ):
#     try:
#         patient_exists = await patient_collection.find_one({"patientId": appointment.patientId})
#         if not patient_exists:
#             return error_response(404, "Patient does not exist.", "Not Found", ["patientId invalid"])

#         # Make sure this field matches your DB schema
#         counselor_exists = await counsellor_collection.find_one({"counselorId": appointment.counselorId})
#         if not counselor_exists:
#             return error_response(404, "Counselor does not exist.", "Not Found", ["counselorId invalid"])

#         appointment_id = str(uuid4())

#         status_value = appointment.status.value if hasattr(appointment.status, "value") else str(appointment.status)
#         status_value = status_value.upper() if isinstance(status_value, str) else status_value

#         appointment_data = {
#             "appointment_id": appointment_id,
#             "patientId": appointment.patientId,
#             "counselorId": appointment.counselorId,
#             "timeSlot": appointment.timeSlot,
#             "date": appointment.date,
#             "reasonForVisit": appointment.reasonForVisit,
#             "status": status_value,
#             "createdAt": datetime.now(timezone("Asia/Kolkata")),
#             "updatedAt": datetime.now(timezone("Asia/Kolkata")),
#             "createdBy": {
#                 "userId": current_user.get("userId"),
#                 "role": current_user.get("role")
#             },
#             "updatedBy": None
#         }

#         result = await appointment_collection.insert_one(appointment_data)

#         if not result.acknowledged:
#             return error_response(500, "Failed to create appointment", "Database Error", [])

#         created_doc = await appointment_collection.find_one({"_id": result.inserted_id})
#         if created_doc and isinstance(created_doc.get("date"), datetime):
#             india_tz = timezone("Asia/Kolkata")
#             created_doc["date"] = created_doc["date"].astimezone(india_tz).strftime("%Y-%m-%d %I:%M %p")
#         created_doc["_id"] = str(created_doc["_id"])

#         return {
#             "message": "Appointment created successfully",
#             "appointment_id": appointment_id,
#             "details": created_doc
#         }

#     except PyMongoError as e:
#         return error_response(500, "Database error", str(e), [])
#     except Exception as e:
#         return error_response(500, "Unexpected error", str(e), [])


@router.get("/appointment/{appointment_id}")
async def get_appointment_by_id(
    appointment_id: str,
    current_user: dict = Depends(require_roles(['admin', "counselor", "psychiatrist","user"]))
):
    try:
        appointment = await appointment_collection.find_one({"appointment_id": appointment_id})
        if not appointment:
            return error_response(404, "Appointment not found.", "Not Found", [])

        patient = await patient_collection.find_one({"patientId": appointment.get("patientId")})
        print(f"Patient data: {patient}")
        doctor = await psychiatrist_collection.find_one({"doctorId": appointment.get("doctorId")})
        print(f"Doctor data: {doctor}")

        india_tz = timezone("Asia/Kolkata")
        formatted_date = (
            appointment["date"].astimezone(india_tz).strftime("%Y-%m-%d %I:%M %p")
            if isinstance(appointment["date"], datetime)
            else str(appointment["date"])
        )

        return {
            "id": str(appointment["_id"]),
            "patientName": f"{patient.get('firstName', '')} {patient.get('lastName', '')}".strip() if patient else None,
            "doctorName": f"{doctor.get('firstName','')} {doctor.get('lastName','')}".strip() if doctor else None,
            #"timeSlot": appointment.get("timeSlot"),
            "startTime": appointment.get("startTime"),
            "endTime": appointment.get("endTime"),
            "date": formatted_date,
            "status": appointment.get("status")
        }


    except PyMongoError as e:
        return error_response(500, "Database error", str(e), [])
    except Exception as e:
        return error_response(500, "Unexpected error", str(e), [])
    
@router.post("/appointments-counsolor")
async def create_appointment_counselor(
    appointment: AppointmentCreationCounsolor = Body(...),
    current_user: dict = Depends(require_roles(['admin', "counselor", "psychiatrist","user"])) 
):
    try:
        patient_exists = await patient_collection.find_one({"patientId": appointment.patientId})
        if not patient_exists:
            return error_response(404, "Patient does not exist.", "Not Found", ["patientId invalid"])

        # Make sure this field matches your DB schema
        counselor_exists = await counselor_collection.find_one({"counselorId": appointment.counselorId})
        if not counselor_exists:
            return error_response(404, "Counselor does not exist.", "Not Found", ["counselorId invalid"])

        appointment_id = str(uuid4())

        status_value = appointment.status.value if hasattr(appointment.status, "value") else str(appointment.status)
        status_value = status_value.upper() if isinstance(status_value, str) else status_value

        appointment_data = {
            "appointment_id": appointment_id,
            "patientId": appointment.patientId,
            "counselorId": appointment.counselorId,
            #"timeSlot": appointment.timeSlot,
            "startTime": appointment.startTime,
            "endTime": appointment.endTime,
            "date": appointment.date,
            "reasonForVisit": appointment.reasonForVisit,
            "status": status_value,
            "createdAt": datetime.now(timezone("Asia/Kolkata")),
            "updatedAt": datetime.now(timezone("Asia/Kolkata")),
            "createdBy": {
                "userId": current_user.get("userId"),
                "role": current_user.get("role")
            },
            "updatedBy": None
        }

        result = await appointment_collection.insert_one(appointment_data)

        if not result.acknowledged:
            return error_response(500, "Failed to create appointment", "Database Error", [])

        created_doc = await appointment_collection.find_one({"_id": result.inserted_id})
        if created_doc and isinstance(created_doc.get("date"), datetime):
            india_tz = timezone("Asia/Kolkata")
            created_doc["date"] = created_doc["date"].astimezone(india_tz).strftime("%Y-%m-%d %I:%M %p")
        created_doc["_id"] = str(created_doc["_id"])

        return {
            "message": "Appointment created successfully",
            "appointment_id": appointment_id,
            "details": created_doc
        }

    except PyMongoError as e:
        return error_response(500, "Database error", str(e), [])
    except Exception as e:
        return error_response(500, "Unexpected error", str(e), [])


def convert_objectid(doc):
    """Recursively convert ObjectId fields to str in nested dicts/lists."""
    if isinstance(doc, dict):
        return {k: convert_objectid(v) for k, v in doc.items()}
    elif isinstance(doc, list):
        return [convert_objectid(i) for i in doc]
    elif isinstance(doc, ObjectId):
        return str(doc)
    return doc


@router.get("/listappointments")
async def list_appointments(
    status_filter: Optional[str] = Query(None),
    start_date: Optional[str] = Query(None),   # YYYY-MM-DD or ISO
    end_date: Optional[str] = Query(None),
    creator_id: Optional[str] = Query(None),
    creator_role: Optional[str] = Query(None),
    mode: Optional[str] = Query(None),
    current_user: dict = Depends(get_current_user),
):
    try:
        match_stage = {}

        # Role and ids from token
        role = (current_user.get("role") or "").lower()
        user_id = current_user.get("userId")          # MongoDB user _id string
        role_user_id = current_user.get("roleUserId") # e.g., MHA-Dxxx / MHA-Cxxx / MHA-Pxxx

        print("current_user:", {"role": role, "userId": user_id, "roleUserId": role_user_id})

        # Role-based filtering
        if role == "admin":
            if creator_id:
                match_stage["createdBy.userId"] = creator_id
            if creator_role:
                match_stage["createdBy.role"] = creator_role

        elif role == "psychiatrist":
            match_stage["$or"] = [
                {"doctorId": role_user_id},         # assigned to this psychiatrist
                {"createdBy.userId": user_id}       # created by this psychiatrist
            ]

        elif role == "counselor":
            match_stage["$or"] = [
                {"counselorId": role_user_id},
                {"createdBy.userId": user_id}
            ]

        elif role == "user":  # patient
            pid = role_user_id or user_id
            match_stage["patientId"] = pid

        else:
            return error_response(
                status_code=status.HTTP_403_FORBIDDEN,
                message="Unauthorized role",
                errors="Invalid role"
            )

        # Other filters
        if status_filter:
            match_stage["status"] = status_filter.upper()

        # Date filter
        try:
            if start_date:
                if len(start_date) == 10:  # YYYY-MM-DD
                    start_date = datetime.strptime(start_date, "%Y-%m-%d")
                else:
                    start_date = datetime.fromisoformat(start_date.replace("Z", "+00:00"))

            if end_date:
                if len(end_date) == 10:  # YYYY-MM-DD
                    end_date = datetime.strptime(end_date, "%Y-%m-%d") + timedelta(days=1)
                else:
                    end_date = datetime.fromisoformat(end_date.replace("Z", "+00:00"))

            if start_date and end_date:
                match_stage["date"] = {"$gte": start_date, "$lt": end_date}
            elif start_date:
                match_stage["date"] = {"$gte": start_date}
            elif end_date:
                match_stage["date"] = {"$lt": end_date}

        except Exception:
            return error_response(
                status_code=status.HTTP_400_BAD_REQUEST,
                message="Invalid date format. Use YYYY-MM-DD or ISO 8601",
                error="Date parsing failed"
            )

        if mode:
            match_stage["consultationMode"] = mode.lower()

        print("Match filter:", match_stage)

        # Final aggregation pipeline
        pipeline = [
            {"$match": match_stage},

            # Join patient details
            {"$lookup": {
                "from": patient_collection.name,
                "localField": "patientId",
                "foreignField": "patientId",
                "as": "patientInfo"
            }},
            {"$unwind": {"path": "$patientInfo", "preserveNullAndEmptyArrays": True}},

            # Join doctor details
            {"$lookup": {
                "from": psychiatrist_collection.name,
                "localField": "doctorId",
                "foreignField": "doctorId",
                "as": "doctorInfo"
            }},
            {"$unwind": {"path": "$doctorInfo", "preserveNullAndEmptyArrays": True}},

            # Join counselor details
            {"$lookup": {
                "from": counselor_collection.name,
                "localField": "counselorId",
                "foreignField": "counselorId",
                "as": "counselorInfo"
            }},
            {"$unwind": {"path": "$counselorInfo", "preserveNullAndEmptyArrays": True}},

            # --- NEW STAGES FOR CREATOR INFO ---
            # Join creator's info from the doctor collection.
            {"$addFields": {
                "createdBy.userId_obj": { "$toObjectId": "$createdBy.userId" }
            }},

            # Join creator's info from the doctor collection
            {"$lookup": {
                "from": psychiatrist_collection.name,
                "localField": "createdBy.userId_obj",
                "foreignField": "_id",
                "as": "creatorDoctor"
            }},
            {"$unwind": {"path": "$creatorDoctor", "preserveNullAndEmptyArrays": True}},

            # Join creator's info from the counselor collection
            {"$lookup": {
                "from": counselor_collection.name,
                "localField": "createdBy.userId_obj",
                "foreignField": "_id",
                "as": "creatorCounselor"
            }},
            {"$unwind": {"path": "$creatorCounselor", "preserveNullAndEmptyArrays": True}},

            # Join creator's info from the admin collection
            {"$lookup": {
                "from": admin_collection.name,
                "localField": "createdBy.userId_obj",
                "foreignField": "_id",
                "as": "creatorAdmin"
            }},
            {"$unwind": {"path": "$creatorAdmin", "preserveNullAndEmptyArrays": True}},


            # Shape final projection
            {"$project": {
                "_id": 1,
                "appointment_id": 1,
                "patientId": 1,
                "doctorId": 1,
                "counselorId": 1,
                #"timeSlot": 1,
                "startTime": 1,
                "endTime": 1,
                "date": 1,
                "reasonForVisit": 1,
                "status": 1,
                "consultationMode": 1,
                "createdAt": 1,
                "updatedAt": 1,
                # "createdBy": 1,   # keep as audit info (not joined)
                "createdBy": {
                    "userId": "$createdBy.userId",
                    "role": "$createdBy.role",
                    "firstName": {"$ifNull": ["$creatorDoctor.firstName", "$creatorCounselor.firstName", "$creatorAdmin.firstName"]},
                    "lastName": {"$ifNull": ["$creatorDoctor.lastName", "$creatorCounselor.lastName", "$creatorAdmin.lastName"]},
                    "email": {"$ifNull": ["$creatorDoctor.email", "$creatorCounselor.email", "$creatorAdmin.email"]},
                    "phoneNumber": {"$ifNull": ["$creatorDoctor.phoneNumber", "$creatorCounselor.phoneNumber", "$creatorAdmin.phoneNumber"]},
                    "profilePhoto": {"$ifNull": ["$creatorDoctor.profilePhoto", "$creatorCounselor.profilePhoto", "$creatorAdmin.profilePhoto"]}
                },
                "patient": {
                    "patientId": "$patientInfo.patientId",
                    "firstName": "$patientInfo.firstName",
                    "lastName": "$patientInfo.lastName",
                    "email": "$patientInfo.email",
                    "phoneNumber": "$patientInfo.phoneNumber",
                    "profilePhoto": "$patientInfo.profilePhoto"
                },
                "psychiatrist": {
                    "psychiatristId": "$doctorInfo.psychiatristId",
                    "firstName": "$doctorInfo.firstName",
                    "lastName": "$doctorInfo.lastName",
                    "email": "$doctorInfo.email",
                    "phoneNumber": "$doctorInfo.phoneNumber",
                    "profilePhoto": "$doctorInfo.profilePhoto"
                },
                "counselor": {
                    "counselorId": "$counselorInfo.counselorId",
                    "firstName": "$counselorInfo.firstName",
                    "lastName": "$counselorInfo.lastName",
                    "email": "$counselorInfo.email",
                    "phoneNumber": "$counselorInfo.phoneNumber",
                    "profilePhoto": "$counselorInfo.profilePhoto"
                }
            }},

            {"$unset": ["patientInfo", "doctorInfo", "counselorInfo", "creatorDoctor", "creatorCounselor", "creatorAdmin", "createdBy.userId_obj"]}
        ]

        appointments = await appointment_collection.aggregate(pipeline).to_list(length=None)
        appointments = convert_objectid(appointments)

        total_appointments = len(appointments)
        completed = sum(1 for a in appointments if a.get("status") == "COMPLETED")
        pending = sum(1 for a in appointments if a.get("status") == "PENDING")
        cancelled = sum(1 for a in appointments if a.get("status") == "CANCELLED")
        rescheduled = sum(1 for a in appointments if a.get("status") == "RESCHEDULED")

        return {
            "success": True,
            "count": total_appointments,
            "completed": completed,
            "pending": pending,
            "cancelled": cancelled,
            "rescheduled":rescheduled,
            "data": appointments
        }

    except Exception as e:
        return error_response(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message="Failed to fetch appointments",
            error=str(e)
        )







# @router.post("/appointments/confirm")
# async def confirm_appointment(
#     req: ConfirmationRequest
#     # current_user: dict = Depends(require_roles(['admin', "counselor", "doctor"]))
# ):
#     try:
#         if not req.appointmentId or not req.status:
#             return error_response(422, "Validation failed", "Missing fields", ["Appointment ID and status are required."])

#         result = await appointment_collection.update_one(
#             {"appointment_id": req.appointmentId},
#             {"$set": {"status": req.status}}
#         )

#         if result.modified_count == 0:
#             return error_response(404, "Appointment not found or already updated", "Not Found", [])

#         return {"message": f"Appointment {req.status.lower()} successfully."}

#     except PyMongoError as e:
#         return error_response(500, "Database error", str(e), [])
#     except Exception as e:
#         return error_response(500, "Unexpected error", str(e), [])





@router.put("/appointments/{appointment_id}/status")
async def update_status(
    appointment_id: str,
    status: str = Query(..., description="Status must be one of 'pending', 'cancelled', 'completed'"),
    current_user: dict = Depends(require_roles(['admin', "counselor", "psychiatrist"]))
):
    try:
        normalized_status = status.upper() 
        
        if normalized_status not in ['PENDING', 'CANCELLED', 'COMPLETED']:
            return error_response(400, "Invalid status", "Status must be one of 'pending', 'cancelled', 'completed'", [])
          
        result = await appointment_collection.update_one(
            {"appointment_id": appointment_id},
            {"$set": {
                "status": normalized_status,
                "updatedAt": datetime.now(timezone("Asia/Kolkata")),
                "updatedBy": {
                    "userId": current_user.get("userId"),
                    "role": current_user.get("role")
                }
            }}
        )

        if result.matched_count == 0:
            return error_response(404, "Appointment not found", "Not Found", [])

        return {
            "success": True,
            "status": 200,
            "message": "Appointment status updated successfully",
            "data": {
                "appointment_id": appointment_id,
                "new_status": normalized_status
            }
        }

    except PyMongoError as e:
        return error_response(500, "Database error", str(e), [])
    except Exception as e:
        return error_response(500, "Unexpected error", str(e), [])

@router.put("/appointments/{appointment_id}/reschedule")
async def reschedule_appointment(
    appointment_id: str,
    req: RescheduleRequest
    # current_user: dict = Depends(require_roles(['admin', "counselor", "doctor"]))
):
    try:
        appointment = await appointment_collection.find_one({"appointment_id": appointment_id})
        if not appointment:
            return error_response(404, "Appointment not found", "Not Found", [])

        new_datetime = datetime.combine(req.newDate, time.min)

        updated_fields = {
            "date": new_datetime,
            #"timeSlot": req.newTimeSlot,
            "startTime": req.newStartTime,
            "endTime": req.newEndTime,
            "status": "RESCHEDULED"
        }

        result = await appointment_collection.update_one(
            {"appointment_id": appointment_id},
            {"$set": updated_fields}
        )

        if result.modified_count == 0:
            return error_response(400, "Appointment not updated.", "Update Failed", [])

        return {
            "message": "Appointment rescheduled successfully",
            "appointment_id": appointment_id,
            "new_date": new_datetime.strftime("%Y-%m-%d"),
            #"new_timeSlot": req.newTimeSlot
            "new_startTime": req.newStartTime,
            "new_endTime": req.newEndTime
        }

    except PyMongoError as e:
        return error_response(500, "Database error", str(e), [])
    except Exception as e:
        return error_response(500, "Unexpected error", str(e), [])


@router.delete("/appointments/{appointment_id}")
async def delete_appointment(
    appointment_id: str
    # current_user: dict = Depends(require_roles(['admin', "counselor", "doctor"]))
):
    try:
        result = await appointment_collection.delete_one({"appointment_id": appointment_id})
        if result.deleted_count == 0:
            return error_response(404, "Appointment not found", "Not Found", [])

        return {"message": "Appointment deleted"}

    except PyMongoError as e:
        return error_response(500, "Database error", str(e), [])
    except Exception as e:
        return error_response(500, "Unexpected error", str(e), [])
