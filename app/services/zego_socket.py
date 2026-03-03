# app/services/zego_socket.py
# Socket.IO-only implementation combining call_meet_routes and googlemeet_routes
# - Adds ZEGOCLOUD token generation to call workflow
# - Adds appointment-based Zego meeting creation via Socket.IO event

from datetime import datetime, timedelta
from typing import Optional, Literal, Dict, Any, List
import os, hmac, hashlib, base64, json, uuid

from app.database.mongo import db, appointment_collection
from app.services.chat_routes import sio  # reuse the Socket.IO server instance

# Collections
calls_collection = db["calls"]

# -----------------------------
# Helpers
# -----------------------------
ROLE_COLLECTIONS = {
    "user": ("patients", "patientId"),
    "doctor": ("doctor", "doctorId"),
    "counselor": ("counselors", "counselorId"),
}


async def _ensure_active(user_id: str, role: str):
    coll, id_field = ROLE_COLLECTIONS[role]
    user = await db[coll].find_one({id_field: user_id}, {"isActive": 1})
    if not user:
        raise ValueError(f"{role.capitalize()} not found")
    if not user.get("isActive"):
        raise ValueError(f"{role.capitalize()} not active")


async def _user_busy(user_id: str) -> bool:
    active = await calls_collection.find_one({
        "$or": [{"callerId": user_id}, {"calleeId": user_id}],
        "status": "accepted"
    })
    return active is not None


def _zego_token(user_id: str, effective_time: int = 3600) -> str:
    app_id = os.getenv("ZEGO_APP_ID")
    server_secret = os.getenv("ZEGO_SERVER_SECRET")
    if not app_id or not server_secret:
        raise RuntimeError("ZEGO_APP_ID or ZEGO_SERVER_SECRET not configured")
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
    base = os.getenv("ZEGO_JOIN_BASE_URL")
    if not base:
        return None
    sep = '&' if '?' in base else '?'
    return f"{base}{sep}roomId={room_id}"


def _iso(dt: Optional[datetime]) -> Optional[str]:
    return dt.isoformat() + "Z" if isinstance(dt, datetime) else None


async def _require_session(session_id: str) -> dict:
    doc = await calls_collection.find_one({"sessionId": session_id})
    if not doc:
        raise ValueError("Call session not found")
    return doc


async def _get_socket_user(sid: str) -> dict:
    session = await sio.get_session(sid)
    if not session or "userId" not in session:
        raise ValueError("Unauthorized: missing user session")
    return session


async def _join_personal_room_if_needed(sid: str, user_id: str):
    await sio.enter_room(sid, f"user:{user_id}")


# ======================
# Socket Events (Zego Calls)
# ======================

@sio.on("call_initiate")
async def zego_call_initiate(sid, data: Dict[str, Any]):
    """Initiate a call, generate Zego tokens, and notify callee."""
    try:
        body = data or {}
        callerId = str(body.get("callerId") or "").strip()
        callerRole = str(body.get("callerRole") or "").strip()
        calleeId = str(body.get("calleeId") or "").strip()
        calleeRole = str(body.get("calleeRole") or "").strip()
        callType = str(body.get("callType") or "").strip()
        appointmentId = body.get("appointmentId")

        if not all([callerId, callerRole, calleeId, calleeRole, callType]):
            raise ValueError("Missing required fields")

        session = await _get_socket_user(sid)
        if session["userId"] != callerId:
            raise ValueError("Forbidden: callerId does not match authenticated user")

        await _join_personal_room_if_needed(sid, session["userId"])

        await _ensure_active(callerId, callerRole)
        await _ensure_active(calleeId, calleeRole)

        if await _user_busy(callerId) or await _user_busy(calleeId):
            raise ValueError("One of the users is already in another call")

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
        caller_token = _zego_token(callerId)
        callee_token = _zego_token(calleeId)
        record.update({
            "zegoSessionId": session_id,
            "zegoCallerToken": caller_token,
            "zegoCalleeToken": callee_token,
            "zegoAppId": os.getenv("ZEGO_APP_ID"),
        })

        await calls_collection.insert_one(record)

        # Notify callee (include only callee's token)
        invite_payload = {
            "event": "call_invite",
            "sessionId": session_id,
            "fromUserId": callerId,
            "fromRole": callerRole,
            "toUserId": calleeId,
            "toRole": calleeRole,
            "callType": callType,
            "appointmentId": appointmentId,
            "createdAt": _iso(now),
            "zego": {
                "appId": os.getenv("ZEGO_APP_ID"),
                "sessionId": session_id,
                "token": callee_token,
                "joinUrl": _join_url(session_id),
            },
        }
        await sio.emit("call_invite", invite_payload, room=f"user:{calleeId}")

        # Confirm to caller (include only caller's token)
        await sio.emit(
            "call_initiated",
            {
                "success": True,
                "sessionId": session_id,
                "zego": {
                    "appId": os.getenv("ZEGO_APP_ID"),
                    "sessionId": session_id,
                    "token": caller_token,
                    "joinUrl": _join_url(session_id),
                },
            },
            to=sid,
        )

    except Exception as e:
        await sio.emit("call_error", {"context": "call_initiate", "error": str(e)}, to=sid)


@sio.on("call_accept")
async def zego_call_accept(sid, data: Dict[str, Any]):
    try:
        session_id = (data or {}).get("sessionId")
        if not session_id:
            raise ValueError("Missing sessionId")
        session = await _get_socket_user(sid)

        doc = await _require_session(session_id)
        if doc.get("status") != "initiated":
            raise ValueError("Call cannot be accepted")
        if session["userId"] not in (doc.get("callerId"), doc.get("calleeId")):
            raise ValueError("Forbidden: not a participant of this call")

        await calls_collection.update_one(
            {"sessionId": session_id},
            {"$set": {"status": "accepted", "updatedAt": datetime.utcnow()}}
        )

        payload = {"sessionId": session_id, "status": "accepted"}
        await sio.emit("call_accept", payload, room=f"user:{doc['callerId']}")
        await sio.emit("call_accept", payload, room=f"user:{doc['calleeId']}")

    except Exception as e:
        await sio.emit("call_error", {"context": "call_accept", "error": str(e)}, to=sid)


@sio.on("call_reject")
async def zego_call_reject(sid, data: Dict[str, Any]):
    try:
        session_id = (data or {}).get("sessionId")
        if not session_id:
            raise ValueError("Missing sessionId")
        session = await _get_socket_user(sid)

        doc = await _require_session(session_id)
        if doc.get("status") != "initiated":
            raise ValueError("Call cannot be rejected")
        if session["userId"] not in (doc.get("callerId"), doc.get("calleeId")):
            raise ValueError("Forbidden: not a participant of this call")

        await calls_collection.update_one(
            {"sessionId": session_id},
            {"$set": {"status": "rejected", "updatedAt": datetime.utcnow()}}
        )

        payload = {"sessionId": session_id, "status": "rejected"}
        await sio.emit("call_reject", payload, room=f"user:{doc['callerId']}")
        await sio.emit("call_reject", payload, room=f"user:{doc['calleeId']}")

    except Exception as e:
        await sio.emit("call_error", {"context": "call_reject", "error": str(e)}, to=sid)


@sio.on("call_end")
async def zego_call_end(sid, data: Dict[str, Any]):
    try:
        session_id = (data or {}).get("sessionId")
        durationSec = (data or {}).get("durationSec")
        if not session_id:
            raise ValueError("Missing sessionId")
        session = await _get_socket_user(sid)

        doc = await _require_session(session_id)
        if session["userId"] not in (doc.get("callerId"), doc.get("calleeId")):
            raise ValueError("Forbidden: not a participant of this call")

        now = datetime.utcnow()
        start = doc.get("createdAt")
        computed_duration = int((now - start).total_seconds()) if isinstance(start, datetime) else 0
        duration = int(durationSec) if durationSec is not None else computed_duration

        new_status = "completed" if doc.get("status") == "accepted" else "missed"

        await calls_collection.update_one(
            {"sessionId": session_id},
            {"$set": {"status": new_status, "updatedAt": now, "durationSec": duration}}
        )

        payload = {"sessionId": session_id, "status": new_status, "durationSec": duration}
        await sio.emit("call_end", payload, room=f"user:{doc['callerId']}")
        await sio.emit("call_end", payload, room=f"user:{doc['calleeId']}")

    except Exception as e:
        await sio.emit("call_error", {"context": "call_end", "error": str(e)}, to=sid)


@sio.on("call_history")
async def zego_call_history(sid, data: Dict[str, Any]):
    try:
        body = data or {}
        userId = str(body.get("userId") or "").strip()
        page = int(body.get("page") or 1)
        limit = int(body.get("limit") or 50)

        session = await _get_socket_user(sid)
        if session["userId"] != userId:
            raise ValueError("Forbidden: cannot access another user's call history")

        skip = (page - 1) * limit
        q = {"$or": [{"callerId": userId}, {"calleeId": userId}]}

        items: List[dict] = []
        cursor = calls_collection.find(q).sort("createdAt", -1).skip(skip).limit(limit)
        async for d in cursor:
            items.append({
                "sessionId": d.get("sessionId"),
                "callerId": d.get("callerId"),
                "callerRole": d.get("callerRole"),
                "calleeId": d.get("calleeId"),
                "calleeRole": d.get("calleeRole"),
                "callType": d.get("callType"),
                "status": d.get("status"),
                "durationSec": int(d.get("durationSec", 0)),
                "appointmentId": d.get("appointmentId"),
                "createdAt": _iso(d.get("createdAt")),
                "updatedAt": _iso(d.get("updatedAt")),
            })

        total = await calls_collection.count_documents(q)
        await sio.emit(
            "call_history_response",
            {
                "success": True,
                "page": page,
                "limit": limit,
                "total": total,
                "total_pages": (total + limit - 1) // limit,
                "items": items,
            },
            to=sid,
        )

    except Exception as e:
        await sio.emit("call_error", {"context": "call_history", "error": str(e)}, to=sid)


# ======================
# Socket Event: Create Zego meet for appointment
# ======================
@sio.on("appointment_zego_meet_create")
async def appointment_zego_meet_create(sid, data: Dict[str, Any]):
    try:
        appointment_id = (data or {}).get("appointmentId")
        if not appointment_id:
            raise ValueError("Missing appointmentId")

        session = await _get_socket_user(sid)
        user_id = session["userId"]

        appt = await appointment_collection.find_one({"appointment_id": appointment_id})
        if not appt:
            raise ValueError("Appointment not found")

        # Authorization: only owning doctor or the patient can trigger via sockets
        if user_id not in (appt.get("doctorId"), appt.get("patientId")):
            raise ValueError("Forbidden: not participant of this appointment")

        # Prevent duplicate creation
        if appt.get("zegoSessionId") and appt.get("zegoDoctorToken") and appt.get("zegoPatientToken"):
            await sio.emit(
                "appointment_zego_meet_response",
                {
                    "success": True,
                    "message": "Zego meeting already exists for this appointment",
                    "details": {
                        "roomId": appt.get("zegoSessionId"),
                        "joinUrl": _join_url(appt.get("zegoSessionId")),
                        "zegoAppId": os.getenv("ZEGO_APP_ID"),
                    },
                },
                to=sid,
            )
            return

        # Build room/session and tokens
        room_id = appt.get("appointment_id") or uuid.uuid4().hex
        doctor_id = appt.get("doctorId")
        patient_id = appt.get("patientId")
        if not doctor_id or not patient_id:
            raise ValueError("Missing doctorId or patientId on appointment")

        doctor_token = _zego_token(doctor_id)
        patient_token = _zego_token(patient_id)

        update = {
            "zegoSessionId": room_id,
            "zegoDoctorToken": doctor_token,
            "zegoPatientToken": patient_token,
            "zegoAppId": os.getenv("ZEGO_APP_ID"),
            "updatedAt": datetime.utcnow(),
        }
        await appointment_collection.update_one({"_id": appt["_id"]}, {"$set": update})

        await sio.emit(
            "appointment_zego_meet_response",
            {
                "success": True,
                "message": "Zego meeting created successfully",
                "details": {
                    "appointmentId": appointment_id,
                    "roomId": room_id,
                    "joinUrl": _join_url(room_id),
                    "zegoAppId": os.getenv("ZEGO_APP_ID"),
                },
            },
            to=sid,
        )

    except Exception as e:
        await sio.emit("call_error", {"context": "appointment_zego_meet_create", "error": str(e)}, to=sid)
