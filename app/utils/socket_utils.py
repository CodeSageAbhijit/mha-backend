import os,hmac, hashlib    
import base64, json, uuid  
from datetime import datetime, timedelta
from typing import Any, Dict, Optional
from pydantic import ValidationError  
from app.services.socket_server import sio
from app.database.mongo import chat_collection, db  
from bson import ObjectId
from app.services.socket_server import ROLE_COLLECTIONS, COLLECTION_ROLE
from app.services.socket_server import USER_SIDS



def _iso(dt: Optional[datetime]) -> Optional[str]:
    return dt.isoformat() + "Z" if isinstance(dt, datetime) else None


async def _get_socket_user(sid: str) -> dict:
    session = await sio.get_session(sid)
    if not session or "userId" not in session:
        raise ValueError("Unauthorized: missing user session") 
    return session


async def _join_personal_room_if_needed(sid: str, user_id: str):
    await sio.enter_room(sid, f"user:{user_id}")


async def _emit_error(sid: str, context: str, error: Any):
    await sio.emit("error", {"context": context, "error": str(error)}, to=sid)


def _call_doc_to_public(d: dict) -> dict:
    return {
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
    }


async def mark_messages_delivered(room_id: str, receiver_id: str):
    await chat_collection.update_many(
        {"room_id": room_id, "receiver_id": receiver_id, "delivered": False},
        {"$set": {"delivered": True}}
    )
    



# helper function to recursively convert ObjectId and datetime
def make_json_safe(obj):
    from bson import ObjectId
    from datetime import datetime

    if isinstance(obj, ObjectId):
        return str(obj)
    if isinstance(obj, datetime):
        return obj.isoformat() + "Z"
    if isinstance(obj, list):
        return [make_json_safe(i) for i in obj]
    if isinstance(obj, dict):
        return {k: make_json_safe(v) for k, v in obj.items()}
    return obj
    return obj

def convert_objectid_to_str(obj):
    if isinstance(obj, dict):
        return {k: convert_objectid_to_str(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_objectid_to_str(i) for i in obj]
    elif isinstance(obj, ObjectId):
        return str(obj)
    else:
        return obj


def serialize_user(user: dict, role_hint: str = None) -> dict:
    u = dict(user)
    id_map = {"patient": "patientId", "psychiatrist": "psychiatristId", "counselor": "counselorId"}
    user_id = u.get(id_map.get(role_hint, "_id")) or str(u.get("_id"))
    full_name = (u.get("firstName", "") + " " + u.get("lastName", "")).strip() or u.get("username") or u.get("email")
    serialized = {
        "id": user_id,
        "username": u.get("username") or full_name,
        "fullName": full_name,
        "email": u.get("email"),
        "role": role_hint or u.get("role", ""),
        "profilePhoto": u.get("profilePhoto"),
    }
    if role_hint in id_map:
        serialized[id_map[role_hint]] = user_id
    return serialized


async def find_user_by_id_any(user_id: str) -> Optional[dict]:
    search_fields = {
        "patients": ["code", "patientId", "_id"],
        "psychiatrists": ["code", "psychiatristId", "_id"],
        "counselors": ["code", "counselorId", "_id"],
    }
    for coll_name, fields in search_fields.items():
        collection = db[coll_name]
        for field in fields:
            if field == "_id" and ObjectId.is_valid(user_id):
                query_val = ObjectId(user_id)
            else:
                query_val = user_id  
            found = await collection.find_one({field: query_val})
            if found:
                role = COLLECTION_ROLE.get(coll_name, "")
                return serialize_user(found, role_hint=role)
    return None



async def _require_session(session_id: str, collection) -> dict:
    doc = await collection.find_one({"sessionId": session_id})
    if not doc:
        raise ValueError("Session not found")
    return doc


async def _ensure_active(user_id: str, role: str):
    coll, id_field = ROLE_COLLECTIONS[role]
    user = await db[coll].find_one({id_field: user_id}, {"isActive": 1})
    if not user or not user.get("isActive"):
        raise ValueError(f"{role.capitalize()} not active")


async def _user_busy(user_id: str) -> bool:
    active = await db["calls"].find_one({
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