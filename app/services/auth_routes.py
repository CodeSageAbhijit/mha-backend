from fastapi import APIRouter, HTTPException
from app.models.token_schemas import RefreshTokenRequest
from app.utils.jwt_tokens import create_access_token
from app.utils.jwt_tokens import decrypt_token
from app.database.mongo import db
from app.utils.jwt_tokens import create_access_token, decrypt_token
from app.utils.encryption import encrypt_token
from app.database.mongo import psychiatrist_collection, counselor_collection, patient_collection, db,admin_collection
from bson import ObjectId
import datetime

router = APIRouter(prefix="/api", tags=["Auth"])


role_map = {
    "admin": admin_collection,
    "psychiatrist": psychiatrist_collection,
    "counsellor": counselor_collection,
    "user": patient_collection
}


async def refresh_access_token(refresh_token: str) -> tuple[str, dict]:
    """
    Validates the refresh token and returns:
      - new access token
      - payload (user info)
    """
    if not refresh_token:
        raise ValueError("Refresh token not provided")

    # 🔹 1. Decrypt the JWE refresh token
    try:
        payload = decrypt_token(refresh_token)
    except Exception as e:
        raise ValueError("Invalid refresh token") from e

    # 🔹 2. Check expiry
    exp = payload.get("exp")
    if not exp or datetime.utcnow().timestamp() > exp:
        raise ValueError("Refresh token expired")

    userId = payload["userId"]
    role = payload["role"]

    # 🔹 3. Verify refresh token in DB (not revoked)
    encrypted_token = encrypt_token(refresh_token)
    stored_token = await db.refresh_tokens.find_one({
        "userId": userId,
        "role": role,
        "token": encrypted_token
    })
    if not stored_token:
        raise ValueError("Refresh token not found or revoked")

    # 🔹 4. Issue a new access token
    new_payload = {
        "userId": userId,
        "email": payload["email"],
        "role": role
    }
    new_access_token = create_access_token(new_payload)

    return new_access_token, payload





def error_response(status_code: int, message: str, error: str, errors: list):
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

@router.post("/token/refresh")
async def refresh_token(payload: RefreshTokenRequest):
    token = payload.refreshToken
    if not token:
        error_response(422, "Missing refresh token", "No refreshToken provided", [])

    token = token.strip()  # Remove accidental spaces

    # 1️⃣ Decrypt token
    try:
        decoded = decrypt_token(token)
    except Exception as e:
        error_response(401, "Invalid refresh token", "Decryption failed", [str(e)])

    if not decoded or "userId" not in decoded or "role" not in decoded:
        error_response(401, "Invalid refresh token", "Missing userId or role in token payload", [])

    user_id = decoded["userId"]
    role = decoded["role"].lower()
    collection = role_map.get(role)
    if collection is None:
        error_response(400, "Invalid role in token", "Role not recognized", [])

    # 2️⃣ Fetch user document
    try:
        user_doc = await collection.find_one({"_id": ObjectId(user_id)})
    except Exception as e:
        error_response(500, "Database error while fetching user", str(e), [])

    if not user_doc:
        error_response(404, "User not found", f"No {role} found with this ID", [])

    stored_token = user_doc.get("refreshToken")
    if stored_token is None:
        error_response(403, "Refresh token not found", "User has no active refresh token", [])

    # 3️⃣ Handle Binary or string token
    if isinstance(stored_token, bytes):
        stored_token = stored_token.decode("utf-8")

    if stored_token != token:
        error_response(403, "Refresh token mismatch", "Token does not match user's record", [])

    # 4️⃣ Generate new access token
    try:
        new_access_token = create_access_token(decoded)
    except Exception as e:
        error_response(500, "Failed to create new access token", str(e), [])

    return {
        "success": True,
        "status": 200,
        "message": "Access token refreshed successfully",
        "data": {"access_token": new_access_token},
        "error": None,
        "errors": []
    }
