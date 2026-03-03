# app/services/call_service_routes.py
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from datetime import datetime, timedelta
import os
import hmac
import hashlib
import base64
import json
import uuid

from app.database.mongo import db
from app.services.chat_routes import sio  # reuse the running Socket.IO server
from app.utils.dependencies import get_current_user

router = APIRouter(prefix="/calls", tags=["Calls"]) 

# Mongo collections
calls_collection = db["calls"]

class InitiateCallRequest(BaseModel):
    callerId: str = Field(..., description="ID of the caller (patient/psychiatrist/counselor)")
    callerRole: str = Field(..., description="Role of the caller: patient | psychiatrist | counselor")
    calleeId: str = Field(..., description="ID of the callee")
    calleeRole: str = Field(..., description="Role of the callee: patient | psychiatrist | counselor")
    callType: str = Field(..., pattern="^(audio|video)$", description="audio | video")
    appointmentId: str | None = Field(None)

class InitiateCallResponse(BaseModel):
    success: bool
    message: str
    data: dict


def _zego_token(user_id: str, effective_time: int = 3600) -> str:
    """Generate a basic ZEGOCLOUD token using AppID + ServerSecret from env.
    This is a simplified token generation (JWT-like). Replace with official SDK if available.
    """
    app_id = os.getenv("ZEGO_APP_ID")
    server_secret = os.getenv("ZEGO_SERVER_SECRET")
    if not app_id or not server_secret:
        raise RuntimeError("ZEGO_APP_ID or ZEGO_SERVER_SECRET not configured")

    # Structure per Zego token guidelines (simplified) - ensure alignment with your SDK version
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


def _build_session(caller_id: str, callee_id: str, call_type: str, appointment_id: str | None) -> dict:
    session_id = uuid.uuid4().hex
    now = datetime.utcnow()
    return {
        "sessionId": session_id,
        "callerId": caller_id,
        "calleeId": callee_id,
        "callType": call_type,
        "status": "initiated",  # initiated | accepted | rejected | missed | completed
        "appointmentId": appointment_id,
        "createdAt": now,
        "updatedAt": now,
        "durationSec": 0,
    }


@router.post("/initiate", response_model=InitiateCallResponse)
async def initiate_call(body: InitiateCallRequest, current_user=Depends(get_current_user)):
    try:
        # Optionally: validate roles visibility/permission here
        session = _build_session(body.callerId, body.calleeId, body.callType, body.appointmentId)

        # Generate Zego tokens for both participants
        try:
            caller_token = _zego_token(body.callerId)
            callee_token = _zego_token(body.calleeId)
        except Exception as te:
            raise HTTPException(status_code=500, detail=f"Token error: {str(te)}")

        # Persist initial call record
        record = dict(session)
        record.update({
            "callerRole": body.callerRole,
            "calleeRole": body.calleeRole,
            "zego": {
                "appId": os.getenv("ZEGO_APP_ID"),
            }
        })
        await calls_collection.insert_one(record)

        # Emit Socket.IO call_invite to callee's personal room
        invite_payload = {
            "event": "call_invite",
            "sessionId": session["sessionId"],
            "fromUserId": body.callerId,
            "fromRole": body.callerRole,
            "toUserId": body.calleeId,
            "toRole": body.calleeRole,
            "callType": body.callType,
            "appointmentId": body.appointmentId,
            "tokens": {
                # Frontend should use its own user's token; sending both for convenience
                "caller": caller_token,
                "callee": callee_token,
            },
            "createdAt": session["createdAt"].isoformat() + "Z",
        }
        await sio.emit("call_invite", invite_payload, room=f"user:{body.calleeId}")

        return {
            "success": True,
            "message": "Call initiated",
            "data": {
                "sessionId": session["sessionId"],
                "zegoAppId": os.getenv("ZEGO_APP_ID"),
                "callerToken": caller_token,
                "calleeToken": callee_token,
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
USER_SIDS = {}  # userId -> set of sids

@sio.event
async def connect(sid, environ, auth):
    user_id = auth.get("userId")
    if not user_id:
        await sio.disconnect(sid)
        return

    # Track connections
    USER_SIDS.setdefault(user_id, set()).add(sid)

    await sio.enter_room(sid, f"user:{user_id}")
    print(f"User {user_id} connected with sid {sid}")

@sio.event
async def disconnect(sid):
    for user_id, sids in USER_SIDS.items():
        if sid in sids:
            sids.remove(sid)
            if not sids:
                del USER_SIDS[user_id]
            print(f"User {user_id} disconnected (sid {sid})")
            break
