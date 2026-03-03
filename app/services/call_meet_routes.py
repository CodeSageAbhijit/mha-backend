# app/services/call_meet_routes.py (ZEGOCLOUD-powered call sessions)
from fastapi import APIRouter, HTTPException, Depends, Body
from app.utils.auth_guard import require_roles
from app.database.mongo import db
from datetime import datetime, timedelta
from typing import Optional, Literal
import os, hmac, hashlib, base64, json, uuid

# Collections
calls_collection = db["calls"]

router = APIRouter(prefix="/api", tags=["ZegoCalls"]) 

# -----------------------------
# Role helpers (mirrors call_routes.py)
# -----------------------------
ROLE_COLLECTIONS = {
    "user": ("patients", "patientId"),
    "psychiatrist": ("psychiatrists", "psychiatristId"),
    "counselor": ("counselors", "counselorId"),
}


async def _ensure_active(user_id: str, role: str):
    coll, id_field = ROLE_COLLECTIONS[role]
    user = await db[coll].find_one({id_field: user_id}, {"isActive": 1})
    if not user:
        raise HTTPException(status_code=404, detail=f"{role.capitalize()} not found")
    if not user.get("isActive"):
        raise HTTPException(status_code=400, detail=f"{role.capitalize()} not active")


async def _user_busy(user_id: str) -> bool:
    active = await calls_collection.find_one({
        "$or": [{"callerId": user_id}, {"calleeId": user_id}],
        "status": "accepted"
    })
    return active is not None


# -----------------------------
# ZEGOCLOUD helpers
# -----------------------------

def _zego_token(user_id: str, effective_time: int = 3600) -> str:
    app_id = os.getenv("ZEGO_APP_ID")
    server_secret = os.getenv("ZEGO_SERVER_SECRET")
    if not app_id or not server_secret:
        raise HTTPException(status_code=501, detail="ZEGO_APP_ID or ZEGO_SERVER_SECRET not configured")
    payload = {
        "app_id": int(app_id),
        "user_id": user_id,
        "nonce": uuid.uuid4().hex,
        "ctime": int(datetime.utcnow().timestamp()),
        "expire": int((datetime.utcnow() + timedelta(seconds=effective_time)).timestamp()),
    }
    payload_bytes = json.dumps(payload, separators=(",", ":")).encode()
    sign = hmac.new(server_secret.encode(), payload_bytes, hashlib.sha256).digest()
    token = base64.b64encode(payload_bytes + b"." + sign).decode()
    return token


def _join_url(room_id: str) -> Optional[str]:
    base = os.getenv("ZEGO_JOIN_BASE_URL")  # e.g., https://your-frontend/meet
    if not base:
        return None
    sep = '&' if '?' in base else '?'
    return f"{base}{sep}roomId={room_id}"


# -----------------------------
# Schemas (inline typing via Body)
# -----------------------------
# Mirrors CallInitiatePayload in call_routes.py
# -----------------------------

# -----------------------------
# Routes
# -----------------------------
@router.post("/calls/zego-meet")
async def create_zego_call_session(
    callerId: str = Body(...),
    callerRole: Literal["user", "psychiatrist", "counselor"] = Body(...),
    calleeId: str = Body(...),
    calleeRole: Literal["user", "psychiatrist", "counselor"] = Body(...),
    callType: Literal["audio", "video"] = Body(...),
    appointmentId: Optional[str] = Body(default=None),
    current_user: dict = Depends(require_roles(["admin", "psychiatrist", "counselor", "user"]))
):
    """
    Create a ZEGOCLOUD-backed call session between caller and callee.
    - Ensures both users are active
    - Prevents double-booking if either user is in an accepted call
    - Creates a calls document and attaches Zego tokens
    - Returns session and join details
    """
    # Authorization: user must be caller, or admin/psychiatrist/counselor can create on behalf
    role = current_user.get("role")
    user_id = current_user.get("userId") or current_user.get("roleUserId")
    if role == "user" and user_id != callerId:
        raise HTTPException(status_code=403, detail="Forbidden: callerId must match authenticated user")

    # Validate roles active
    await _ensure_active(callerId, callerRole)
    await _ensure_active(calleeId, calleeRole)

    # Busy check
    if await _user_busy(callerId) or await _user_busy(calleeId):
        raise HTTPException(status_code=409, detail="One of the users is already in another call")

    # Create or reuse a session
    session_id = uuid.uuid4().hex
    now = datetime.utcnow()
    record = {
        "sessionId": session_id,
        "callerId": callerId,
        "callerRole": callerRole,
        "calleeId": calleeId,
        "calleeRole": calleeRole,
        "callType": callType,
        "status": "initiated",
        "appointmentId": appointmentId,
        "createdAt": now,
        "updatedAt": now,
        "durationSec": 0,
    }

    # Generate Zego tokens
    try:
        caller_token = _zego_token(callerId)
        callee_token = _zego_token(calleeId)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Zego token error: {e}")

    record.update({
        "zegoSessionId": session_id,
        "zegoCallerToken": caller_token,
        "zegoCalleeToken": callee_token,
        "zegoAppId": os.getenv("ZEGO_APP_ID"),
    })

    await calls_collection.insert_one(record)

    # Build response
    return {
        "message": "Zego call session created successfully",
        "details": {
            "sessionId": session_id,
            "callerId": callerId,
            "calleeId": calleeId,
            "callType": callType,
            "status": "initiated",
            "joinUrl": _join_url(session_id),
            "zegoAppId": os.getenv("ZEGO_APP_ID"),
            "callerToken": caller_token,
            "calleeToken": callee_token,
        },
    }


@router.post("/calls/{session_id}/accept")
async def accept_zego_call_session(
    session_id: str,
    current_user: dict = Depends(require_roles(["admin", "psychiatrist", "counselor", "user"]))
):
    doc = await calls_collection.find_one({"sessionId": session_id})
    if not doc:
        raise HTTPException(status_code=404, detail="Call session not found")

    uid = current_user.get("userId") or current_user.get("roleUserId")
    if uid not in (doc.get("callerId"), doc.get("calleeId")) and current_user.get("role") not in ("admin",):
        raise HTTPException(status_code=403, detail="Forbidden: not a participant of this call")

    if doc.get("status") != "initiated":
        raise HTTPException(status_code=400, detail="Call cannot be accepted")

    await calls_collection.update_one(
        {"sessionId": session_id},
        {"$set": {"status": "accepted", "updatedAt": datetime.utcnow()}}
    )

    return {"message": "Call accepted", "sessionId": session_id, "status": "accepted"}


@router.post("/calls/{session_id}/end")
async def end_zego_call_session(
    session_id: str,
    durationSec: Optional[int] = Body(default=None),
    current_user: dict = Depends(require_roles(["admin", "psychiatrist", "counselor", "user"]))
):
    doc = await calls_collection.find_one({"sessionId": session_id})
    if not doc:
        raise HTTPException(status_code=404, detail="Call session not found")

    uid = current_user.get("userId") or current_user.get("roleUserId")
    if uid not in (doc.get("callerId"), doc.get("calleeId")) and current_user.get("role") not in ("admin",):
        raise HTTPException(status_code=403, detail="Forbidden: not a participant of this call")

    now = datetime.utcnow()
    start = doc.get("createdAt")
    computed_duration = int((now - start).total_seconds()) if isinstance(start, datetime) else 0
    duration = durationSec if durationSec is not None else computed_duration

    new_status = "completed" if doc.get("status") == "accepted" else "missed"

    await calls_collection.update_one(
        {"sessionId": session_id},
        {"$set": {"status": new_status, "updatedAt": now, "durationSec": duration}}
    )

    return {"message": "Call ended", "sessionId": session_id, "status": new_status, "durationSec": duration}
