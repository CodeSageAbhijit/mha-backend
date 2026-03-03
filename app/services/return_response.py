from fastapi import APIRouter, Depends, HTTPException, status
from bson import ObjectId
from app.utils.dependencies import get_current_user
from app.database.mongo import patient_collection, psychiatrist_collection, counselor_collection, admin_collection

router = APIRouter(prefix="/api", tags=["Auth"])

def error_response(status_code: int, message: str, error: str, errors: list):
    """Helper to raise HTTPException with camelCase keys."""
    raise HTTPException(
        status_code=status_code,
        detail={
            "success": False,
            "status": status_code,
            "message": message,
            "data": None,
            "error": error,
            "errors": errors
        }
    )

@router.get("/current-user")
async def get_current_user_info(currentUser: dict = Depends(get_current_user)):
    try:
        userId = currentUser.get("userId")
        role = currentUser.get("role")
        print(f"Fetching user details for userId: {userId}, role: {role}")

        if not userId or not role:
            error_response(
                status.HTTP_400_BAD_REQUEST,
                "Missing userId or role",
                "Invalid authentication payload",
                ["userId or role not found in token"]
            )

        role_map = {
            "user": patient_collection,
            "doctor": psychiatrist_collection,
            "counselor": counselor_collection,
            "admin": admin_collection
        }
        collection = role_map.get(role)
        if collection is None:
            error_response(
                status.HTTP_400_BAD_REQUEST,
                "Invalid role",
                "Role not recognized",
                [f"Invalid role '{role}' provided"]
            )

        try:
            userData = await collection.find_one(
                {"_id": ObjectId(userId)},
                {"password": 0, "access_token": 0, "refresh_token": 0}
            )
            print(f"User data fetched: {userData}")
        except Exception as e:
            error_response(
                status.HTTP_400_BAD_REQUEST,
                "Invalid userId format for MongoDB _id",
                str(e),
                ["ObjectId conversion failed", "Invalid userId format"]
            )

        if not userData:
            error_response(
                status.HTTP_404_NOT_FOUND,
                "User not found",
                "No matching record in database",
                [f"No user found with id '{userId}' for role '{role}'"]
            )

        # Convert _id to string
        userData["id"] = str(userData["_id"])
        del userData["_id"]

        return {
            "success": True,
            "status": status.HTTP_200_OK,
            "message": "User details fetched successfully",
            "data": userData,
            "error": None,
            "errors": []
        }

    except HTTPException:
        raise
    except Exception as e:
        error_response(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            "An unexpected error occurred",
            str(e),
            ["Internal server error"]
        )
