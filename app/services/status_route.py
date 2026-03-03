# app/services/routers/status.py
from fastapi import APIRouter, HTTPException, Depends, status, Body
from bson import ObjectId
from pymongo.errors import PyMongoError
from app.database.mongo import psychiatrist_collection, counselor_collection, patient_collection
from app.utils.dependencies import get_current_user
from pydantic import BaseModel

router = APIRouter(prefix="/api/status", tags=["Status"])

# Helper: select collection based on role
def get_collection(role: str):
    role = role.lower() if role else ""
    if role == "psychiatrist":
        return psychiatrist_collection
    elif role in ( "counselor"):
        return counselor_collection
    elif role in ("patient", "user"):
        return patient_collection
    return None

class StatusUpdateRequest(BaseModel):
    isActive: bool

@router.put("/update")
async def update_status(
    payload: StatusUpdateRequest,
    current_user: dict = Depends(get_current_user)
):
    
    try:
        role = current_user.get("role")
        user_id = current_user.get("userId")
        collection = get_collection(role)

        if collection is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "success": False,
                    "message": f"Invalid role: {role}",
                    "error": "InvalidRoleError",
                    "errors": []
                }
            )

        if not ObjectId.is_valid(user_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "success": False,
                    "message": f"Invalid userId format: {user_id}",
                    "error": "InvalidObjectIdError",
                    "errors": []
                }
            )

        # Update MongoDB
        result = await collection.update_one(
            {"_id": ObjectId(user_id)},
            {"$set": {"isActive": payload.isActive}}
        )

        if result.matched_count == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "success": False,
                    "message": "User not found",
                    "error": "NotFoundError",
                    "errors": []
                }
            )

        return {
            "success": True,
            "status": 200,
            "message": f"Status updated to {'active' if payload.isActive else 'inactive'}",
            "data": {
                "userId": user_id,
                "isActive": payload.isActive
            },
            "errors": []
        }

    except PyMongoError as db_err:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "success": False,
                "message": "Database operation failed",
                "error": str(db_err),
                "errors": []
            }
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "success": False,
                "message": "An unexpected error occurred",
                "error": str(e),
                "errors": []
            }
        )
