from fastapi import APIRouter, HTTPException, Depends,Query,status
from fastapi import APIRouter, HTTPException, Depends,Query,status
from datetime import datetime
from bson import ObjectId
from app.database.mongo import prescription_collection, patient_collection,medicine_collection,psychiatrist_collection,counselor_collection,admin_collection
from app.database.mongo import prescription_collection, patient_collection,medicine_collection,psychiatrist_collection,counselor_collection,admin_collection
from app.models.prescription_schema import PrescriptionCreate, PrescriptionUpdate
from app.utils.dependencies import get_current_user  
from app.utils.error_response import error_response
from typing import Optional
from datetime import datetime, time, timedelta
from app.utils.error_response import error_response
from typing import Optional
from datetime import datetime, time, timedelta

router = APIRouter(prefix="/api/prescriptions", tags=["Prescriptions"])


# 🔹 Format Prescription for UI


# 🔹 Format Prescription for UI


async def prescription_helper(prescription) -> dict:
    # fetch patient name if not stored
    patient_name = prescription.get("patientName")
    if not patient_name and "patientId" in prescription:
        patient = await patient_collection.find_one({"userId": prescription["patientId"]})
        patient_name = patient.get("fullName") if patient else prescription["patientId"]

    # fetch medicine names if only medicineId is stored
    medicines_data = []
    for med in prescription.get("medicines", []):
        medicine_name = med.get("medicineName")
        if not medicine_name and med.get("medicineId"):
            medicine = await medicine_collection.find_one({"_id": ObjectId(med["medicineId"])})
            medicine_name = medicine.get("name") if medicine else med["medicineId"]

        medicines_data.append({
            "medicineName": medicine_name,
            "dosage": med.get("dosage"),
            "notes": med.get("notes"),
        })





    return {
        "id": str(prescription["_id"]),  # ✅ use Mongo's _id as id
        "date": prescription.get("date"),
        "patient": patient_name,
        "medicines": medicines_data,
        "createdBy": prescription.get("createdBy"),
        "prescribedBy": prescription.get("prescribedBy"),
    }


def convert_objectid(doc):
    """Recursively convert ObjectId fields to str in nested dicts/lists."""
    if isinstance(doc, dict):
        return {k: convert_objectid(v) for k, v in doc.items()}
    elif isinstance(doc, list):
        return [convert_objectid(i) for i in doc]
    elif isinstance(doc, ObjectId):
        return str(doc)
    return doc

@router.get("/listprescriptions")
async def list_prescriptions(
    status_filter: Optional[str] = Query(None),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    creator_id: Optional[str] = Query(None),
    creator_role: Optional[str] = Query(None),
    current_user: dict = Depends(get_current_user),
):
    try:
        match_stage = {}

        # ==========================
        # Role-based filtering
        # ==========================
        role = (current_user.get("role") or "").lower()
        user_id = current_user.get("userId")
        role_user_id = current_user.get("roleUserId")

        if role == "admin":
            if creator_id:
                match_stage["createdBy.userId"] = creator_id
            if creator_role:
                match_stage["createdBy.role"] = creator_role

        elif role == "psychiatrist":
            # Psychiatrists can see prescriptions they created
            match_stage["createdBy.userId"] = user_id

        elif role == "mentor":
            # Mentors can see prescriptions they might have assisted with
            match_stage["createdBy.userId"] = user_id

        elif role == "user":  # patient
            pid = role_user_id or user_id
            match_stage["patientId"] = pid

        else:
            return error_response(
                status_code=status.HTTP_403_FORBIDDEN,
                message="Unauthorized role",
                errors="Invalid role"
            )

        # ==========================
        # Status filter
        # ==========================
        if status_filter:
            match_stage["status"] = status_filter.upper()

        # ==========================
        # Date filters
        # ==========================
        try:
            if start_date:
                start_date = (
                    datetime.strptime(start_date, "%Y-%m-%d")
                    if len(start_date) == 10
                    else datetime.fromisoformat(start_date.replace("Z", "+00:00"))
                )
            if end_date:
                end_date = (
                    datetime.strptime(end_date, "%Y-%m-%d") + timedelta(days=1)
                    if len(end_date) == 10
                    else datetime.fromisoformat(end_date.replace("Z", "+00:00"))
                )

            if start_date and end_date:
                match_stage["issuedAt"] = {"$gte": start_date, "$lt": end_date}
            elif start_date:
                match_stage["issuedAt"] = {"$gte": start_date}
            elif end_date:
                match_stage["issuedAt"] = {"$lt": end_date}

        except Exception:
            return error_response(
                status_code=status.HTTP_400_BAD_REQUEST,
                message="Invalid date format. Use YYYY-MM-DD or ISO 8601",
                error="Date parsing failed"
            )

        # ==========================
        # Aggregation pipeline
        # ==========================
        pipeline = [
            {"$match": match_stage},

            # Join patient
            {"$lookup": {
                "from": patient_collection.name,
                "localField": "patientId",
                "foreignField": "patientId",
                "as": "patientInfo"
            }},
            {"$unwind": {"path": "$patientInfo", "preserveNullAndEmptyArrays": True}},

            # Join doctor
            {"$lookup": {
                "from": psychiatrist_collection.name,
                "localField": "doctorId",
                "foreignField": "doctorId",
                "as": "doctorInfo"
            }},
            {"$unwind": {"path": "$doctorInfo", "preserveNullAndEmptyArrays": True}},

            # Join counselor
            {"$lookup": {
                "from": counselor_collection.name,
                "localField": "counselorId",
                "foreignField": "counselorId",
                "as": "counselorInfo"
            }},
            {"$unwind": {"path": "$counselorInfo", "preserveNullAndEmptyArrays": True}},

            # Resolve createdBy details
            {"$addFields": {
                "createdBy.userId_obj": {"$toObjectId": "$createdBy.userId"}
            }},
            {"$lookup": {
                "from": psychiatrist_collection.name,
                "localField": "createdBy.userId_obj",
                "foreignField": "_id",
                "as": "creatorDoctor"
            }},
            {"$unwind": {"path": "$creatorDoctor", "preserveNullAndEmptyArrays": True}},
            {"$lookup": {
                "from": counselor_collection.name,
                "localField": "createdBy.userId_obj",
                "foreignField": "_id",
                "as": "creatorCounselor"
            }},
            {"$unwind": {"path": "$creatorCounselor", "preserveNullAndEmptyArrays": True}},
            {"$lookup": {
                "from": admin_collection.name,
                "localField": "createdBy.userId_obj",
                "foreignField": "_id",
                "as": "creatorAdmin"
            }},
            {"$unwind": {"path": "$creatorAdmin", "preserveNullAndEmptyArrays": True}},

            # Resolve prescribedBy details
            {"$addFields": {
                "prescribedBy.userId_obj": {
                    "$cond": {
                        "if": {"$regexMatch": {"input": "$prescribedBy.userId", "regex": "^[0-9a-fA-F]{24}$"}},
                        "then": {"$toObjectId": "$prescribedBy.userId"},
                        "else": None
                    }
                }
            }},
            {"$lookup": {
                "from": psychiatrist_collection.name,
                "localField": "prescribedBy.userId",
                "foreignField": "doctorId",
                "as": "prescriberDoctor"
            }},
            {"$unwind": {"path": "$prescriberDoctor", "preserveNullAndEmptyArrays": True}},
            {"$lookup": {
                "from": counselor_collection.name,
                "localField": "prescribedBy.userId_obj",
                "foreignField": "_id",
                "as": "prescriberCounselor"
            }},
            {"$unwind": {"path": "$prescriberCounselor", "preserveNullAndEmptyArrays": True}},

            # Final projection
            {"$project": {
                "_id": 1,
                "patientId": 1,
                "doctorId": 1,
                "counselorId": 1,
                "medicines": 1,
                "instructions": 1,
                "notes": 1,
                "issuedAt": 1,
                "validTill": 1,
                "status": 1,
                "createdAt": 1,
                "updatedAt": 1,
                "updatedBy": 1,
                "prescribedBy": {
                    "userId": "$prescribedBy.userId",
                    "role": "$prescribedBy.role",
                    "date": "$prescribedBy.date",
                    "firstName": {"$ifNull": ["$prescriberDoctor.firstName", "$prescriberCounselor.firstName"]},
                    "lastName": {"$ifNull": ["$prescriberDoctor.lastName", "$prescriberCounselor.lastName"]},
                    "email": {"$ifNull": ["$prescriberDoctor.email", "$prescriberCounselor.email"]},
                    "phoneNumber": {"$ifNull": ["$prescriberDoctor.phoneNumber", "$prescriberCounselor.phoneNumber"]},
                    "profilePhoto": {"$ifNull": ["$prescriberDoctor.profilePhoto", "$prescriberCounselor.profilePhoto"]}
                },
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
                "doctor": {
                    "doctorId": "$doctorInfo.doctorId",
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
            {"$unset": [
                "patientInfo", "doctorInfo", "counselorInfo",
                "creatorDoctor", "creatorCounselor", "creatorAdmin",
                "prescriberDoctor", "prescriberCounselor",
                "createdBy.userId_obj", "prescribedBy.userId_obj"
            ]}
        ]

        prescriptions = await prescription_collection.aggregate(pipeline).to_list(length=None)

        # Convert ObjectId → string id
        for p in prescriptions:
            p["id"] = str(p.pop("_id"))

        return {
            "success": True,
            "count": len(prescriptions),
            "data": prescriptions
        }

    except Exception as e:
        return error_response(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message="Failed to fetch prescriptions",
            error=str(e)
        )



# ✅ POST → Create Prescription
@router.post("", response_model=dict)
async def create_prescription(
    prescription: PrescriptionCreate,
    current_user: dict = Depends(get_current_user)
):
    # Only Psychiatrist can create prescriptions
    if current_user["role"] != "psychiatrist":
        raise HTTPException(status_code=403, detail="Only psychiatrists can create prescriptions")

    new_prescription = prescription.dict()
    new_prescription["createdAt"] = datetime.utcnow()
    new_prescription["updatedAt"] = datetime.utcnow()

    # ✅ Ensure patientId is stored
    if not new_prescription.get("patientId"):
        raise HTTPException(status_code=400, detail="Prescription must include patientId")

    # Who created it
    new_prescription["createdBy"] = {
        "userId": current_user["userId"],
        "role": current_user["role"]
    }
    new_prescription["updatedBy"] = new_prescription["createdBy"]

    result = await prescription_collection.insert_one(new_prescription)
    created = await prescription_collection.find_one({"_id": result.inserted_id})
    return {"success": "prescription added successfully", "data": await prescription_helper(created)}

# ✅ GET → Get all prescriptions with role-based access
@router.get("", response_model=dict)
async def get_prescriptions(current_user: dict = Depends(get_current_user)):
    if current_user["role"] == "admin":
        query = {}
    elif current_user["role"] == "psychiatrist":
        query = {"createdBy.userId": current_user["userId"]}
    elif current_user["role"] == "mentor":
        query = {"createdBy.userId": current_user["userId"]}
    elif current_user["role"] == "user":  # patient
        query = {"patientId": current_user["userId"]}
    else:
        query = {}

    prescriptions = []
    async for p in prescription_collection.find(query):
        prescriptions.append(await prescription_helper(p))



    return {"success": True, "count": len(prescriptions), "data": prescriptions}




# ✅ PUT → Update Prescription




@router.put("/{id}", response_model=dict)
async def update_prescription(
    id: str,
    update: PrescriptionUpdate,
    current_user: dict = Depends(get_current_user)
):
    try:
        oid = ObjectId(id)
    except:
        raise HTTPException(status_code=400, detail="Invalid prescription ID")

    prescription = await prescription_collection.find_one({"_id": oid})
    if not prescription:
        raise HTTPException(status_code=404, detail="Prescription not found")

    if current_user["role"] == "patient":
        raise HTTPException(status_code=403, detail="Patients cannot update prescriptions")

    if current_user["role"] in ["psychiatrist", "counselor"]:
        if prescription["createdBy"]["userId"] != current_user["userId"]:
            raise HTTPException(status_code=403, detail="You can only update your own prescriptions")

    update_data = {k: v for k, v in update.dict(exclude_unset=True).items()}
    update_data["updatedAt"] = datetime.utcnow()
    update_data["updatedBy"] = {
        "userId": current_user["userId"],
        "role": current_user["role"]
    }



    await prescription_collection.update_one({"_id": oid}, {"$set": update_data})
    updated = await prescription_collection.find_one({"_id": oid})


    return {"success": True, "message": "Updated successfully", "data": await prescription_helper(updated)}


# ✅ DELETE → Delete Prescription
@router.delete("/{id}", response_model=dict)
async def delete_prescription(
    id: str,
    current_user: dict = Depends(get_current_user)
):
    try:
        oid = ObjectId(id)
    except:
        raise HTTPException(status_code=400, detail="Invalid prescription ID")

    prescription = await prescription_collection.find_one({"_id": oid})
    if not prescription:
        raise HTTPException(status_code=404, detail="Prescription not found")

    if current_user["role"] == "patient":
        raise HTTPException(status_code=403, detail="Patients cannot delete prescriptions")

    if current_user["role"] in ["psychiatrist", "counselor"]:
        if prescription["createdBy"]["userId"] != current_user["userId"]:
            raise HTTPException(status_code=403, detail="You can only delete your own prescriptions")

    await prescription_collection.delete_one({"_id": oid})
    return {"success": True, "message": "Prescription deleted successfully"}
