# ...existing code...
from fastapi import APIRouter, HTTPException, status, Depends
from bson import ObjectId
from pymongo.errors import PyMongoError
from typing import List

from app.models.counselor_availability_schema import (
    AvailabilityCreate, AvailabilityUpdate, AvailabilityResponse
)
from pymongo import ReturnDocument
from app.database.mongo import counselor_availability_collection
from app.utils.auth_guard import get_current_user

router = APIRouter(prefix="/api/counselor_availability", tags=["Counselor Availability"])

# ----------------------------- #
# Create availability
# ----------------------------- #
@router.post("/", response_model=AvailabilityResponse)
async def create_availability(
    payload: AvailabilityCreate,
    current_user: dict = Depends(get_current_user)
):
    if current_user["role"].lower() != "counselor":
        raise HTTPException(status_code=403, detail="Only counselors can create availability")
    if payload.counselorId != current_user["roleUserId"]:
        raise HTTPException(status_code=403, detail="You can only create your own availability")

    try:
        existing = await counselor_availability_collection.find_one({"counselorId": payload.counselorId})
        if existing:
            raise HTTPException(status_code=400, detail="Availability already exists, use update instead")

        doc = payload.dict()
        result = await counselor_availability_collection.insert_one(doc)
        doc["id"] = str(result.inserted_id)
        return {"id": doc["id"], **doc}
    except PyMongoError as e:
        raise HTTPException(status_code=500, detail=str(e))


# ----------------------------- #
# Get availability (public)
# ----------------------------- #
@router.get("/{counselor_id}", response_model=AvailabilityResponse)
async def get_availability(counselor_id: str):
    doc = await counselor_availability_collection.find_one({"counselorId": counselor_id})
    if not doc:
        raise HTTPException(status_code=404, detail="Availability not found")
    doc["id"] = str(doc["_id"])
    return doc


# ----------------------------- #
# Update availability
# ----------------------------- #
@router.put("/{counselor_id}", response_model=AvailabilityResponse)
async def update_availability(
    counselor_id: str,
    payload: AvailabilityUpdate,
    current_user: dict = Depends(get_current_user)
):
    if current_user["role"].lower() != "counselor":
        raise HTTPException(status_code=403, detail="Only counselors can update availability")
    if counselor_id != current_user["roleUserId"]:
        raise HTTPException(status_code=403, detail="You can only update your own availability")

    try:
        update_data = {k: v for k, v in payload.dict(exclude_none=True).items()}
        if not update_data:
            raise HTTPException(status_code=400, detail="No fields to update")

        result = await counselor_availability_collection.find_one_and_update(
            {"counselorId": counselor_id},
            {"$set": update_data},
            return_document=ReturnDocument.AFTER
        )
        if not result:
            raise HTTPException(status_code=404, detail="Availability not found")

        result["id"] = str(result["_id"])
        return result
    except PyMongoError as e:
        raise HTTPException(status_code=500, detail=str(e))


# ----------------------------- #
# Delete availability
# ----------------------------- #
@router.delete("/{counselor_id}")
async def delete_availability(
    counselor_id: str,
    current_user: dict = Depends(get_current_user)
):
    if current_user["role"].lower() != "counselor":
        raise HTTPException(status_code=403, detail="Only counselors can delete availability")
    if counselor_id != current_user["roleUserId"]:
        raise HTTPException(status_code=403, detail="You can only delete your own availability")

    result = await counselor_availability_collection.delete_one({"counselorId": counselor_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Availability not found")
    return {"message": "Availability deleted successfully"}
