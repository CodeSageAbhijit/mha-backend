# app/services/googlemeet_routes.py (repurposed for ZEGOCLOUD)
from fastapi import APIRouter, HTTPException, Depends, Path
from app.utils.auth_guard import require_roles
from app.database.mongo import appointment_collection, psychiatrist_collection, patient_collection
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import os, hmac, hashlib, base64, json, uuid

router = APIRouter(prefix="/api", tags=["ZegoMeet"]) 

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
# Routes
# -----------------------------
@router.post("/appointments/{appointment_id}/zego-meet")
async def create_zego_meet_for_appointment(
    appointment_id: str = Path(...),
    current_user: dict = Depends(require_roles(["admin", "psychiatrist"]))
):
    appt = await appointment_collection.find_one({"appointment_id": appointment_id})
    if not appt:
        raise HTTPException(status_code=404, detail="Appointment not found")

    # Only owning psychiatrist or admin
    if current_user.get("role") == "psychiatrist":
        current_doctor_id = current_user.get("doctorId") or current_user.get("roleUserId") or current_user.get("userId")
        if current_doctor_id and appt.get("doctorId") and appt.get("doctorId") != current_doctor_id:
            raise HTTPException(status_code=403, detail="Forbidden: not appointment owner")

    # Prevent duplicate creation
    if appt.get("zegoSessionId") and appt.get("zegoDoctorToken") and appt.get("zegoPatientToken"):
        return {
            "message": "Zego meeting already exists for this appointment",
            "details": {
                "roomId": appt.get("zegoSessionId"),
                "joinUrl": _join_url(appt.get("zegoSessionId"))
            },
        }

    # Build room/session and tokens
    room_id = appt.get("appointment_id") or uuid.uuid4().hex

    # Determine participant ids
    doctor_id = appt.get("doctorId")
    patient_id = appt.get("patientId")
    if not doctor_id or not patient_id:
        raise HTTPException(status_code=400, detail="Missing doctorId or patientId on appointment")

    try:
        doctor_token = _zego_token(doctor_id)
        patient_token = _zego_token(patient_id)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Zego token error: {e}")

    update = {
        "zegoSessionId": room_id,
        "zegoDoctorToken": doctor_token,
        "zegoPatientToken": patient_token,
        "zegoAppId": os.getenv("ZEGO_APP_ID"),
        "updatedAt": datetime.utcnow(),
    }
    await appointment_collection.update_one({"_id": appt["_id"]}, {"$set": update})

    updated = await appointment_collection.find_one({"_id": appt["_id"]})
    if updated and "_id" in updated:
        updated["_id"] = str(updated["_id"])  # JSON-safe

    return {
        "message": "Zego meeting created successfully",
        "details": {
            "appointment": updated,
            "roomId": room_id,
            "joinUrl": _join_url(room_id),
            "zegoAppId": os.getenv("ZEGO_APP_ID"),
        },
    }
