from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field, validator
from app.utils.auth_guard import get_current_user
from app.database.mongo import psychiatrist_collection, counselor_collection, patient_collection
from app.utils.constants import hash_password
from app.utils.error_response import error_response

router = APIRouter(prefix="/api", tags=["Auth"])

class ChangePasswordRequest(BaseModel):
    newPassword: str = Field(..., min_length=6)
    confirmPassword: str = Field(..., min_length=6)

    @validator("confirmPassword")
    def passwords_match(cls, v, values):
        if "newPassword" in values and v != values["newPassword"]:
            raise ValueError("Passwords do not match")
        return v


@router.post("/change-password")
async def change_password(
    payload: ChangePasswordRequest, 
    current_user: dict = Depends(get_current_user)
):
    """
    Allow authenticated doctor / counselor / patient to change password from settings.
    """
    try:
        role = (current_user.get("role") or "").lower()
        user_db = current_user.get("db_user")
        if not user_db:
            return error_response(401, "Unauthorized", "User not found in token", [])

        # Prepare update
        new_hashed = hash_password(payload.newPassword)

        collection_map = {
            "doctor": psychiatrist_collection,
            "counselor": counselor_collection,
            "counsellor": counselor_collection,  # support both spellings
            "user": patient_collection,
            "patient": patient_collection,
        }

        collection = collection_map.get(role)
        if collection is None:
            return error_response(
                400,
                "Invalid role for password change",
                "RoleError",
                [f"Unsupported role: {role}"],
            )

        # Update password in DB
        await collection.update_one(
            {"_id": user_db["_id"]},
            {"$set": {"password": new_hashed}}
        )

        return {
            "success": True,
            "status": 200,
            "message": "Password updated successfully",
            "data": None,
            "error": None,
            "errors": [],
        }

    except Exception as e:
        return error_response(500, "Unexpected error", str(e), [])
