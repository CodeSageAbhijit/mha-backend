from fastapi import APIRouter, HTTPException, Depends
from bson import ObjectId
from datetime import datetime
from app.database.mongo import prescription_collection
from app.models.prescription_schema import PrescriptionCreate, PrescriptionUpdate, PrescriptionResponse
from app.utils.dependencies import get_current_user  
from app.database.mongo import patient_collection

router = APIRouter(prefix="/api/prescriptions", tags=["Prescriptions"])

# 🔹 Format Prescription for UI (table-like response)
async def prescription_helper(prescription) -> dict:
    # fetch patient name from patient_collection if only patientId is stored
    patient_name = prescription.get("patientName")
    if not patient_name and "patientId" in prescription:
        patient = await patient_collection.find_one({"userId": prescription["patientId"]})
        if patient:
            patient_name = patient.get("fullName", prescription["patientId"])
        else:
            patient_name = prescription["patientId"]

    return {
        "id": str(prescription["_id"]),
        "date": prescription.get("date"),
        "patient": patient_name,
        "medicines": [
            {
                "medicineName": med.get("medicineName"),
                "dosage": med.get("dosage"),
                "notes": med.get("notes"),
            }
            for med in prescription.get("medicines", [])
        ]
    }


# ✅ POST → Create Prescription
@router.post("/", response_model=dict)
async def create_prescription(
    prescription: PrescriptionCreate,
    current_user: dict = Depends(get_current_user)
):
    # 🔹 Access Control → Only Psychiatrist / Counselor can create
    if current_user["role"] not in ["psychiatrist", "counselor"]:
        raise HTTPException(status_code=403, detail="Only psychiatrists/counselors can create prescriptions")

    # 🔹 Prepare prescription data
    new_prescription = prescription.dict()
    new_prescription["createdAt"] = datetime.utcnow()
    new_prescription["updatedAt"] = datetime.utcnow()
    new_prescription["updatedBy"] = new_prescription["createdBy"]

    # 🔹 Insert into DB
    result = await prescription_collection.insert_one(new_prescription)
    created = await prescription_collection.find_one({"_id": result.inserted_id})

    # 🔹 Return formatted response
    return {"success": True, "data": await prescription_helper(created)}


# ✅ Get All Prescriptions with role-based access
@router.get("/", response_model=dict)
async def get_prescriptions(current_user: dict = Depends(get_current_user)):
    """
    Role-based prescription listing:
    - Admin: See all prescriptions
    - Psychiatrist/Counselor: See only prescriptions created by them
    - Patient: See only prescriptions prescribed to them
    """
    query = {}

    # 🔹 Admin → all prescriptions
    if current_user["role"] == "admin":
        query = {}

    # 🔹 Psychiatrist/Counselor → prescriptions they created
    elif current_user["role"] in ["psychiatrist", "counselor"]:
        query = {"createdBy.userId": current_user["userId"]}

    # 🔹 Patient → prescriptions prescribed to them
    elif current_user["role"] == "patient":
        query = {"patientId": current_user["userId"]}

    prescriptions = []
    async for p in prescription_collection.find(query):
        prescriptions.append(prescription_helper(p))

    return {"success": True, "count": len(prescriptions), "data": prescriptions}


# ✅ Update Prescription
# ✅ Update Prescription
@router.put("/{id}", response_model=dict)
async def update_prescription(
    id: str,
    update: PrescriptionUpdate,
    current_user: dict = Depends(get_current_user)
):
    prescription = await prescription_collection.find_one({"_id": ObjectId(id)})
    if not prescription:
        raise HTTPException(status_code=404, detail="Prescription not found")

    # Access Control
    if current_user["role"] == "patient":
        raise HTTPException(status_code=403, detail="Patients cannot update prescriptions")

    if current_user["role"] in ["psychiatrist", "counselor"]:
        if prescription["createdBy"]["userId"] != current_user["userId"]:
            raise HTTPException(status_code=403, detail="You can only update your own prescriptions")

    # ✅ Prepare update data
    update_data = {k: v for k, v in update.dict().items() if v is not None}
    update_data["updatedAt"] = datetime.utcnow()
    update_data["updatedBy"] = update.updatedBy.dict()

    result = await prescription_collection.update_one(
        {"_id": ObjectId(id)}, {"$set": update_data}
    )

    updated = await prescription_collection.find_one({"_id": ObjectId(id)})
    return {"success": True, "message": "Updated successfully", "data": prescription_helper(updated)}


# ✅ Delete Prescription
@router.delete("/{id}", response_model=dict)
async def delete_prescription(
    id: str,
    current_user: dict = Depends(get_current_user)
):
    prescription = await prescription_collection.find_one({"_id": ObjectId(id)})
    if not prescription:
        raise HTTPException(status_code=404, detail="Prescription not found")

    # Access Control
    if current_user["role"] == "patient":
        raise HTTPException(status_code=403, detail="Patients cannot delete prescriptions")

    if current_user["role"] in ["psychiatrist", "counselor"]:
        if prescription["createdBy"]["userId"] != current_user["userId"]:
            raise HTTPException(status_code=403, detail="You can only delete your own prescriptions")

    await prescription_collection.delete_one({"_id": ObjectId(id)})
    return {"success": True, "message": "Prescription deleted successfully"}

