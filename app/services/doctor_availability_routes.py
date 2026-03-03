from fastapi import APIRouter, HTTPException, status, Depends
from bson import ObjectId
from pymongo.errors import PyMongoError
from typing import List

from app.models.psychiatrist_availability_schema import (
    AvailabilityCreate, AvailabilityUpdate, AvailabilityResponse
)
from pymongo import ReturnDocument
from app.database.mongo import psychiatrist_availability_collection
from app.utils.auth_guard import get_current_user

router = APIRouter(prefix="/api/psychiatrist_availability", tags=["Psychiatrist Availability"])

# -------------------- Routes -------------------- #

# -----------------------------
# Create availability
# -----------------------------
@router.post("/", response_model=AvailabilityResponse)
async def create_availability(
    payload: AvailabilityCreate,
    current_user: dict = Depends(get_current_user)
):
    # ✅ Allow only the logged-in psychiatrist
    print(current_user)
    if current_user["role"].lower() != "psychiatrist":
        raise HTTPException(status_code=403, detail="Only psychiatrists can create availability")
    if payload.doctor_id != current_user["roleUserId"]:
        raise HTTPException(status_code=403, detail="You can only create your own availability")

    try:
        # Check if availability already exists
        existing = await psychiatrist_availability_collection.find_one({"doctorId": payload.doctor_id})
        if existing:
            raise HTTPException(status_code=400, detail="Availability already exists, use update instead")

        doc = payload.dict()
        result = await psychiatrist_availability_collection.insert_one(doc)
        doc["id"] = str(result.inserted_id)
        return {
            "id": doc["id"],
            **doc
        }
    except PyMongoError as e:
        raise HTTPException(status_code=500, detail=str(e))
    
# -----------------------------
# Get availability (public)
# -----------------------------
@router.get("/{doctor_id}", response_model=AvailabilityResponse)
async def get_availability(doctor_id: str):
    print(doctor_id)
    doc = await psychiatrist_availability_collection.find_one({"doctorId": doctor_id})
    print(doc)
    if not doc:
        raise HTTPException(status_code=404, detail="Availability not found")
    doc["id"] = str(doc["_id"])
    return doc

# -----------------------------
# Update availability
# -----------------------------
@router.put("/{doctor_id}", response_model=AvailabilityResponse)
async def update_availability(
    doctor_id: str,
    payload: AvailabilityUpdate,
    current_user: dict = Depends(get_current_user)
):
    # ✅ Only the owner psychiatrist can update
    if current_user["role"].lower() != "psychiatrist":
        raise HTTPException(status_code=403, detail="Only psychiatrists can update availability")
    print(doctor_id, current_user["userId"])
    if doctor_id != current_user["userId"]:
        raise HTTPException(status_code=403, detail="You can only update your own availability")

    try:
        update_data = {k: v for k, v in payload.dict(exclude_none=True).items()}
        if not update_data:
            raise HTTPException(status_code=400, detail="No fields to update")

        result = await psychiatrist_availability_collection.find_one_and_update(
            {"doctorId": doctor_id},
            {"$set": update_data},
            return_document=ReturnDocument.AFTER
        )
        
        result["id"] = str(result["_id"])
        return result
    except PyMongoError as e:
        raise HTTPException(status_code=500, detail=str(e))
    

# -----------------------------
# Delete availability
# -----------------------------
@router.delete("/{doctor_id}")
async def delete_availability(
    doctor_id: str,
    current_user: dict = Depends(get_current_user)
):
    print(doctor_id, current_user["userId"])
    # ✅ Only the owner psychiatrist can delete
    if current_user["role"].lower() != "psychiatrist":
        raise HTTPException(status_code=403, detail="Only psychiatrists can delete availability")
    if doctor_id != current_user["userId"]:
        raise HTTPException(status_code=403, detail="You can only delete your own availability")

    result = await psychiatrist_availability_collection.delete_one({"doctorId": doctor_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Availability not found")
    return {"message": "Availability deleted successfully"}
