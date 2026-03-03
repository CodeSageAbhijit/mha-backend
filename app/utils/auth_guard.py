from fastapi import APIRouter, HTTPException, Depends, Request, status
from fastapi.security import OAuth2PasswordBearer
from app.utils.jwt_tokens import create_access_token, decrypt_token
from app.database.mongo import db
from bson import ObjectId
from datetime import datetime
import traceback
from typing import List

router = APIRouter(prefix="/api", tags=["Auth"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/login")

# MongoDB collections mapping
ROLE_COLLECTIONS = {
    "psychiatrist": ("psychiatrists", "_id"),
    "counselor": ("counselors", "_id"),
    "admin": ("admin", "_id"),  # <-- Fixed plural
    "user": ("patients", "_id"),
}

def error_response(status_code: int, message: str, error: str, errors: list):
    """Standard error response"""
    raise HTTPException(
        status_code=status_code,
        detail={
            "success": False,
            "status": status_code,
            "message": message,
            "data": None,
            "error": error,
            "errors": errors or []
        }
    )

async def get_current_user(token: str = Depends(oauth2_scheme), request: Request = None):
    """
    Get current user from access token.
    Automatically refreshes token using refresh token if expired.
    """
    try:
        if not token:
            raise HTTPException(status_code=401, detail="Missing authentication token")

        payload = decrypt_token(token)
        if not payload:
            raise HTTPException(status_code=401, detail="Token decryption failed")

        exp = payload.get("exp")
        if not exp or datetime.utcnow().timestamp() > exp:
            # Access token expired, try refresh token
            refresh_token = request.headers.get("X-Refresh-Token")
            if not refresh_token:
                raise HTTPException(status_code=401, detail="Token expired and no refresh token provided")

            # Validate refresh token in DB
            refresh_payload = decrypt_token(refresh_token)
            role = refresh_payload.get("role")
            userId = refresh_payload.get("userId")
            collection_name, id_field = ROLE_COLLECTIONS[role]
            collection = db[collection_name]

            db_user = await collection.find_one({id_field: userId}) if role != "admin" else await collection.find_one({"_id": ObjectId(userId)})
            if not db_user or db_user.get("refreshToken") != refresh_token:
                raise HTTPException(status_code=403, detail="Refresh token invalid or revoked")

            # Issue new access token
            new_access_token = create_access_token(refresh_payload)
            request.state.new_access_token = new_access_token
            payload = refresh_payload

        # Fetch DB user normally
        role = payload.get("role")
        userId = payload.get("userId")
        # print(f"Fetching user details for userId: {userId}, role: {role}")
        collection_name, id_field = ROLE_COLLECTIONS[role]
        # print(f"Fetching user from collection: {collection_name}, id_field: {id_field}, userId: {userId}")
        
        collection = db[collection_name]
        # print("collection_name, id_field, userId",collection)  # Debugging line")

        db_user = await collection.find_one({id_field: ObjectId(userId)}) if role != "admin" else await collection.find_one({"_id": ObjectId(userId)})
            # if role == "admin":
            #     db_user = await collection.find_one({"_id": ObjectId(userId)})
            # elif role == "doctor":
            #     db_user = await collection.find_one({id_field: ObjectId(userId)})
            # elif role == "counselor":
            #     db_user = await collection.find_one({id_field: ObjectId(userId)})
            # elif role == "user":
            #     db_user = await collection.find_one({id_field:ObjectId(userId)})
                # HTTPException(status_code=404, detail="not permitted")

                # 👆 if you prefer patientId (MHA-P050), change to:
                # db_user = await collection.find_one({"patientId": userId})
            # else:
            #     db_user = None
        if not db_user:
            raise HTTPException(status_code=404, detail=f"{role.capitalize()} with ID '{userId}' not found or databade name mismatch")

        payload["db_user"] = db_user
        return payload

    except HTTPException:
        raise
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=401, detail=f"Token validation failed: {str(e)}")

# Role-based auth dependency
def require_roles(allowed_roles: List[str]):
    async def role_checker(current_user: dict = Depends(get_current_user)):
        if current_user["role"] not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to perform this action"
            )
        return current_user
    return role_checker

# Predefined role dependencies

get_psychiatrist_user = require_roles("psychiatrist")
get_counselor_user = require_roles("counselor")
get_admin_user = require_roles("admin")
get_patient_user =require_roles("user")

