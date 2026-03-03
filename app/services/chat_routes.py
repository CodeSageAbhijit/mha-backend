# app/services/socket_server.py
import os
import uuid
from datetime import datetime, timedelta
from typing import Optional, Literal, List, Any, Dict
import asyncio

import socketio
from bson import ObjectId
from pydantic import BaseModel, Field, ValidationError

from app.database.mongo import db, chat_collection
from app.services.room_routes import get_or_create_room
# from app.utils.encryption import decrypt_token


# =========================
# Socket.IO Setup
# =========================
sio = socketio.AsyncServer(
    async_mode="asgi",
    cors_allowed_origins="*",
    logger=True,
    engineio_logger=True,
    ping_timeout=60,
    ping_interval=25,
    namespace="/"
)

socket_app = socketio.ASGIApp(
    sio,
    static_files={},
    on_startup=lambda: print("✅ Socket.IO server started"),
    on_shutdown=lambda: print("❌ Socket.IO server shutdown")
)
# =========================
# Role ↔ Collection Mapping
# =========================
ROLE_COLLECTIONS = {
    "user": ("patients", "patientId"),
    "psychiatrist": ("psychiatrists", "psychiatristId"),
    "counselor": ("counselors", "counselorId"),
}

COLLECTION_ROLE = {
    "patients": "user",
    "psychiatrists": "psychiatrist",
    "counselors": "counselor",
}

# =========================
# Globals
# =========================

typing_users: dict[str, dict] = {}  
USER_SIDS: dict[str, set[str]] = {}
online_users: dict[str, dict] = {}  # {user_id: {"sid": sid, "last_seen": datetime, "status": "online"}}
user_sessions: dict[str, str] = {}  # {sid: user_id} for quick lookups



calls_collection = db["calls"]

# =========================
# Helpers
# =========================
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

async def _get_user_role(user_id: str) -> str:
    """Get the role of a user by checking all collections"""
    # Check patients
    patient = await db["patients"].find_one({"patientId": user_id})
    if patient:
        return "user"
    
    # Check psychiatrists
    psychiatrist = await db["psychiatrists"].find_one({"psychiatristId": user_id})
    if psychiatrist:
        return "psychiatrist"
    
    # Check counselors
    counselor = await db["counselors"].find_one({"counselorId": user_id})
    if counselor:
        return "counselor"
    
    return "user"  # Default

async def _get_user_doc(user_id: str, role: str) -> Optional[dict]:
    """Get user document based on role"""
    if role == "user":
        return await db["patients"].find_one({"patientId": user_id})
    elif role == "psychiatrist":
        return await db["psychiatrists"].find_one({"psychiatristId": user_id})
    elif role == "counselor":
        return await db["counselors"].find_one({"counselorId": user_id})
    return None

def convert_objectid_to_str(obj):
    if isinstance(obj, dict):
        return {k: convert_objectid_to_str(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_objectid_to_str(i) for i in obj]
    elif isinstance(obj, ObjectId):
        return str(obj)
    else:
        return obj

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
    



def make_json_safe(obj):
    if isinstance(obj, datetime):
        return obj.isoformat()
    if isinstance(obj, ObjectId):
        return str(obj)
    if isinstance(obj, list):
        return [make_json_safe(item) for item in obj]
    if isinstance(obj, dict):
        return {k: make_json_safe(v) for k, v in obj.items()}
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
        "patients": ["code", "patientId"],
        "psychiatrists": ["code", "psychiatristId"],
        "counselors": ["code", "counselorId"],
    }
    for coll_name, fields in search_fields.items():
        collection = db[coll_name]
        for field in fields:
            query_val = ObjectId(user_id) if field == "_id" and ObjectId.is_valid(user_id) else user_id
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


async def _user_online(user_id: str) -> bool:
    """Check if user is currently online (connected via socket)"""
    try:
        # First check our online_users tracking
        if user_id in online_users:
            user_status = online_users[user_id]
            if user_status.get("status") == "online":
                return True
        
        # Fallback: Check room participants
        room_name = f"user:{user_id}"
        room_members = sio.manager.get_participants(sio.namespace, room_name)
        return len(room_members) > 0
    except Exception as e:
        print(f"[DEBUG] _user_online error for {user_id}: {e}")
        return False


async def _user_busy(user_id: str) -> bool:
    """Check if user is currently in an active call"""
    try:
        # First, clean up any stale calls (older than 5 minutes)
        five_minutes_ago = datetime.utcnow() - timedelta(minutes=5)
        await db["calls"].update_many(
            {
                "$or": [{"callerId": user_id}, {"calleeId": user_id}],
                "status": {"$in": ["initiated", "accepted"]},
                "createdAt": {"$lt": five_minutes_ago}
            },
            {"$set": {"status": "missed", "updatedAt": datetime.utcnow()}}
        )
        
        # Now check for truly active calls (recent and in progress)
        recent_time = datetime.utcnow() - timedelta(minutes=2)  # Only consider calls from last 2 minutes
        active = await db["calls"].find_one({
            "$or": [{"callerId": user_id}, {"calleeId": user_id}],
            "status": {"$in": ["initiated", "accepted"]},
            "createdAt": {"$gte": recent_time}  # Only recent calls
        })
        
        if active:
            print(f"[DEBUG] User {user_id} is busy in recent call {active.get('sessionId')} with status {active.get('status')}")
            return True
        else:
            print(f"[DEBUG] User {user_id} is not busy - no recent active calls")
            return False
            
    except Exception as e:
        print(f"[DEBUG] _user_busy error for {user_id}: {e}")
        return False

# import json

# def decrypt_token(encrypted: str | bytes) -> dict:
#     if isinstance(encrypted, bytes):
#         decrypted = fernet.decrypt(encrypted)
#     elif isinstance(encrypted, str):
#         decrypted = fernet.decrypt(encrypted.encode())
#     else:
#         raise ValueError("Invalid encrypted token type")
    
#     # ✅ Convert JSON string to Python dict
#     return json.loads(decrypted.decode())




# @sio.event
# async def connect(sid, environ, auth):
#     try:
#         token = auth.get("token")
#         print("🔑 Received token:", token)
#         data = decrypt_token(token)
#         print("✅ Decrypted payload:", data)

#         user_id = data.get("sub")
#         print(f"Expected userId: {user_id}, received userId: {auth.get('userId')}")

#         if not user_id or user_id != auth.get("userId"):
#             raise ConnectionRefusedError("Invalid credentials")

#         await sio.save_session(sid, {"userId": user_id, "role": auth.get("role")})
#         print(f"✅ Session saved for {sid}")

#     except Exception as e:
#         print(f"❌ Token validation failed: {e}")
#         raise ConnectionRefusedError("Invalid credentials")



async def cleanup_user_stale_calls(user_id: str):
    """Clean up stale call records for a user"""
    try:
        # Mark old calls as missed/ended
        five_minutes_ago = datetime.utcnow() - timedelta(minutes=5)
        result = await db["calls"].update_many(
            {
                "$or": [{"callerId": user_id}, {"calleeId": user_id}],
                "status": {"$in": ["initiated", "accepted"]},
                "createdAt": {"$lt": five_minutes_ago}
            },
            {"$set": {"status": "missed", "updatedAt": datetime.utcnow()}}
        )
        
        if result.modified_count > 0:
            print(f"[DEBUG] Cleaned up {result.modified_count} stale calls for user {user_id}")
            
    except Exception as e:
        print(f"[DEBUG] Error cleaning up stale calls for {user_id}: {e}")


# =========================
# Socket.IO Events
# =========================
@sio.event
async def connect(sid, environ, auth):
    try:
        user_id, role = (auth or {}).get("userId"), (auth or {}).get("role")
        if not user_id or role not in ROLE_COLLECTIONS:
            raise ConnectionRefusedError("Invalid credentials")

        coll_name, id_field = ROLE_COLLECTIONS[role]
        user = await db[coll_name].find_one({id_field: user_id})
        if not user:
            raise ConnectionRefusedError(f"{role.capitalize()} not found")

        await sio.save_session(sid, {"userId": user_id, "role": role})
        await sio.enter_room(sid, f"user:{user_id}")
        
        # Track online status - handle reconnections
        was_offline = False
        if user_id in online_users:
            was_offline = online_users[user_id].get("status") == "offline"
        
        online_users[user_id] = {
            "sid": sid,
            "last_seen": datetime.utcnow(),
            "status": "online",
            "role": role,
            "reconnected": was_offline
        }
        user_sessions[sid] = user_id
        
        # Clean up any stale calls for this user on connect
        await cleanup_user_stale_calls(user_id)
        
        # Notify others about online status
        await sio.emit("user_status", {
            "userId": user_id,
            "status": "online",
            "lastSeen": datetime.utcnow().isoformat()
        }, skip_sid=sid)  # Don't send to the user themselves
        
        # If this is a reconnection, check for active calls
        if was_offline:
            print(f"✅ Reconnected: {user_id} ({role}) - checking for active calls")
            try:
                active_calls = await db["calls"].find({
                    "$or": [{"callerId": user_id}, {"calleeId": user_id}],
                    "status": {"$in": ["initiated", "accepted"]}
                }).to_list(length=None)
                
                for call in active_calls:
                    # Notify user about their active calls
                    await sio.emit("call_reconnect", {
                        "sessionId": call.get("sessionId"),
                        "status": call.get("status"),
                        "callerId": call.get("callerId"),
                        "calleeId": call.get("calleeId")
                    }, to=sid)
                    print(f"[DEBUG] Notified {user_id} about active call {call.get('sessionId')}")
            except Exception as e:
                print(f"[DEBUG] Error checking active calls for reconnected user {user_id}: {e}")
        else:
            print(f"✅ Connected: {user_id} ({role}) - Status: Online")
        
        return True
    except Exception as e:
        print(f"❌ Connection error: {e}")
        raise ConnectionRefusedError(str(e))


@sio.event
async def disconnect(sid):
    typing_users.pop(sid, None)
    
    # Handle offline status
    user_id = user_sessions.pop(sid, None)
    if user_id and user_id in online_users:
        # DON'T immediately clean up calls on disconnect
        # Users frequently disconnect/reconnect (mobile apps, page refresh, etc.)
        # Instead, add a delay to allow for reconnection
        
        # Mark as offline
        online_users[user_id]["status"] = "offline"
        online_users[user_id]["last_seen"] = datetime.utcnow()
        online_users[user_id]["disconnect_time"] = datetime.utcnow()
        
        # Notify others about offline status
        await sio.emit("user_status", {
            "userId": user_id,
            "status": "offline",
            "lastSeen": datetime.utcnow().isoformat()
        })
        
        # Schedule call cleanup after a delay (30 seconds)
        # This allows time for reconnection
        asyncio.create_task(delayed_call_cleanup(user_id, sid))
        
        print(f"❌ {sid} disconnected - User {user_id} is now offline (calls preserved for 30s)")
    else:
        print(f"❌ {sid} disconnected")


async def delayed_call_cleanup(user_id: str, original_sid: str):
    """Clean up calls after a delay, but only if user hasn't reconnected"""
    await asyncio.sleep(30)  # Wait 30 seconds
    
    try:
        # Check if user has reconnected
        if user_id in online_users:
            current_status = online_users[user_id]
            # If user reconnected (different SID or online status), don't cleanup
            if (current_status.get("status") == "online" or 
                current_status.get("sid") != original_sid):
                print(f"[DEBUG] User {user_id} reconnected, skipping call cleanup")
                return
        
        # User hasn't reconnected, proceed with call cleanup
        active_calls = await db["calls"].find({
            "$or": [{"callerId": user_id}, {"calleeId": user_id}],
            "status": {"$in": ["initiated", "accepted"]}
        }).to_list(length=None)
        
        for call in active_calls:
            session_id = call.get("sessionId")
            caller_id = call.get("callerId")
            callee_id = call.get("calleeId")
            call_status = call.get("status")
            
            # Only cleanup if call is still in progress and user is truly disconnected
            if call_status in ["initiated", "accepted"]:
                # Mark call as dropped
                await calls_collection.update_one(
                    {"sessionId": session_id},
                    {"$set": {"status": "dropped", "updatedAt": datetime.utcnow()}}
                )
                
                # Notify the other participant
                other_user = callee_id if caller_id == user_id else caller_id
                await sio.emit("call_end", {
                    "sessionId": session_id, 
                    "status": "dropped", 
                    "reason": "User disconnected (after 30s timeout)"
                }, room=f"user:{other_user}")
                
                print(f"[DEBUG] Delayed cleanup: Call {session_id} marked as dropped after 30s timeout")
    except Exception as e:
        print(f"[DEBUG] Error in delayed call cleanup for {user_id}: {e}")


# =========================
# Debug and Status Events  
# =========================
@sio.on("debug_user_status")
async def debug_user_status(sid, data):
    """Debug endpoint to check user online status and call states"""
    try:
        session = await _get_socket_user(sid)
        user_id = data.get("userId") if data else session["userId"]
        
        # Clean up stale calls first
        await cleanup_user_stale_calls(user_id)
        
        # Check online status
        is_online = await _user_online(user_id)
        is_busy = await _user_busy(user_id)
        
        # Get active calls
        active_calls = await db["calls"].find({
            "$or": [{"callerId": user_id}, {"calleeId": user_id}],
            "status": {"$in": ["initiated", "accepted"]}
        }).to_list(length=10)
        
        # Check online_users tracking
        online_status = online_users.get(user_id, {})
        
        response = {
            "userId": user_id,
            "isOnline": is_online,
            "isBusy": is_busy,
            "activeCalls": [
                {
                    "sessionId": call.get("sessionId"),
                    "status": call.get("status"),
                    "callerId": call.get("callerId"),
                    "calleeId": call.get("calleeId"),
                    "createdAt": call.get("createdAt").isoformat() if call.get("createdAt") else None
                } for call in active_calls
            ],
            "onlineTracking": {
                "status": online_status.get("status"),
                "lastSeen": online_status.get("last_seen").isoformat() if online_status.get("last_seen") else None,
                "sid": online_status.get("sid")
            }
        }
        
        await sio.emit("debug_user_status_response", response, to=sid)
        print(f"[DEBUG] User status check for {user_id}: {response}")
        
    except Exception as e:
        await _emit_error(sid, "debug_user_status", str(e))


@sio.on("debug_clear_user_calls")
async def debug_clear_user_calls(sid, data):
    """Debug endpoint to forcefully clear a user's call state"""
    try:
        session = await _get_socket_user(sid)
        user_id = data.get("userId") if data else session["userId"]
        
        # Force clear all call records for this user
        result = await db["calls"].update_many(
            {
                "$or": [{"callerId": user_id}, {"calleeId": user_id}],
                "status": {"$in": ["initiated", "accepted"]}
            },
            {"$set": {"status": "force_ended", "updatedAt": datetime.utcnow()}}
        )
        
        response = {
            "userId": user_id,
            "clearedCalls": result.modified_count,
            "message": f"Forcefully cleared {result.modified_count} call records for user {user_id}"
        }
        
        await sio.emit("debug_clear_calls_response", response, to=sid)
        print(f"[DEBUG] Force cleared calls for {user_id}: {response}")
        
    except Exception as e:
        await _emit_error(sid, "debug_clear_user_calls", str(e))


@sio.on("debug_cleanup_calls")
async def debug_cleanup_calls(sid, data):
    """Debug endpoint to cleanup stale calls"""
    try:
        session = await _get_socket_user(sid)
        
        # Find stale calls (older than 5 minutes and still initiated)
        five_minutes_ago = datetime.utcnow() - timedelta(minutes=5)
        stale_calls = await db["calls"].find({
            "status": "initiated",
            "createdAt": {"$lt": five_minutes_ago}
        }).to_list(length=100)
        
        cleaned_count = 0
        for call in stale_calls:
            await calls_collection.update_one(
                {"sessionId": call["sessionId"]},
                {"$set": {"status": "missed", "updatedAt": datetime.utcnow()}}
            )
            cleaned_count += 1
            print(f"[DEBUG] Cleaned stale call: {call['sessionId']}")
        
        await sio.emit("debug_cleanup_response", {
            "cleaned": cleaned_count,
            "message": f"Cleaned {cleaned_count} stale calls"
        }, to=sid)
        
    except Exception as e:
        await _emit_error(sid, "debug_cleanup_calls", str(e))


# =========================
# Online Status Events
# =========================
@sio.on("get_user_status")
async def get_user_status(sid, data):
    """Get online status of specific users"""
    try:
        user_ids = data.get("userIds", [])
        status_info = {}
        
        for user_id in user_ids:
            if user_id in online_users:
                user_info = online_users[user_id]
                status_info[user_id] = {
                    "status": user_info["status"],
                    "lastSeen": user_info["last_seen"].isoformat(),
                    "isOnline": user_info["status"] == "online"
                }
            else:
                status_info[user_id] = {
                    "status": "offline",
                    "lastSeen": None,
                    "isOnline": False
                }
        
        await sio.emit("user_status_response", status_info, to=sid)
    except Exception as e:
        await _emit_error(sid, "get_user_status", e)


@sio.on("update_status")
async def update_status(sid, data):
    """Update user's online status (online, away, busy, etc.)"""
    try:
        session = await _get_socket_user(sid)
        user_id = session["userId"]
        new_status = data.get("status", "online")
        
        if user_id in online_users:
            online_users[user_id]["status"] = new_status
            online_users[user_id]["last_seen"] = datetime.utcnow()
            
            # Notify others about status change
            await sio.emit("user_status", {
                "userId": user_id,
                "status": new_status,
                "lastSeen": datetime.utcnow().isoformat()
            }, skip_sid=sid)
            
    except Exception as e:
        await _emit_error(sid, "update_status", e)


# =========================
# Chat Events
# =========================
@sio.on("join_room")
async def join_room(sid, data):
    try:
        session = await _get_socket_user(sid)
        user_id = session["userId"]
        other_user_id = data.get("other_user_id")
        if not other_user_id:
            raise ValueError("Missing other_user_id")

        room_id = str(await get_or_create_room(user_id, other_user_id))
        await sio.enter_room(sid, room_id)
        print("Joining room", room_id, "for", user_id, "with", other_user_id)


        # ✅ Tell *this* client that they joined successfully
        await sio.emit("room_joined", {"roomId": room_id, "userId": user_id}, to=sid)

        # 🔔 Optionally notify others already in the room
        await sio.emit("user_joined", {"roomId": room_id, "userId": user_id}, room=room_id, skip_sid=sid)

    except Exception as e:
        await _emit_error(sid, "join_room", e)


@sio.on("send_message")
async def send_message(sid, data):
    try:
        # ✅ Get authenticated session (uses token from connect)
        session = await _get_socket_user(sid)
        sender_id = session["userId"]  # override client-sent senderId
        sender_role = session.get("role", "user")

        # ✅ Extract and validate input safely
        room_id = (data or {}).get("roomId")
        receiver_id = (data or {}).get("receiverId")
        text = (data or {}).get("message")

        if not room_id or not receiver_id or not text:
            raise ValueError("Missing required fields: roomId, receiverId, or message")

        # 💰 CHAT BILLING LOGIC - Charge user when messaging psychiatrist/counselor
        receiver_role = await _get_user_role(receiver_id)
        should_charge = False
        charge_amount = 0
        
        if sender_role == "user" and receiver_role in ["psychiatrist", "counselor"]:
            # Count messages sent today by this user in this room
            today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
            messages_today = await chat_collection.count_documents({
                "room_id": room_id,
                "sender_id": sender_id,
                "timestamp": {"$gte": today_start}
            })
            
            # Charge after free messages
            if messages_today >= CHAT_FREE_MESSAGES:
                should_charge = True
                charge_amount = CHAT_MESSAGE_CHARGE
                
                # Check user balance
                user_balance = await get_wallet_balance(sender_id)
                if user_balance < charge_amount:
                    await sio.emit("error", {
                        "context": "send_message",
                        "error": "Insufficient wallet balance to send message. Please recharge.",
                        "code": "INSUFFICIENT_BALANCE"
                    }, to=sid)
                    return
                
                # Deduct from user
                await update_wallet_balance(
                    sender_id, 
                    -charge_amount,
                    reason=f"Chat message to {receiver_role}"
                )
                
                # Calculate commission and provider share
                commission = round(charge_amount * COMMISSION_RATE, 2)
                provider_amount = round(charge_amount - commission, 2)
                
                # Credit provider (doctor/counselor)
                await update_wallet_balance(
                    receiver_id,
                    provider_amount,
                    from_user_id=sender_id,
                    reason=f"Chat message from user"
                )
                
                # Credit referrer or platform
                receiver_doc = await _get_user_doc(receiver_id, receiver_role)
                ref_target = None
                if receiver_doc:
                    ref_target = receiver_doc.get("clientLink") or receiver_doc.get("referrerId")
                
                if ref_target:
                    await update_wallet_balance(ref_target, commission, reason="Chat commission")
                else:
                    await update_wallet_balance(PLATFORM_WALLET_USERID, commission, reason="Chat commission")
                
                # Notify user about charge
                new_user_balance = await get_wallet_balance(sender_id)
                await sio.emit("chat_message_charged", {
                    "amount": charge_amount,
                    "newBalance": new_user_balance,
                    "message": f"₹{charge_amount} charged for message"
                }, to=sid)

        # ✅ Build message document
        msg_doc = {
            "room_id": room_id,
            "sender_id": sender_id,
            "receiver_id": receiver_id,
            "message": text,
            "timestamp": datetime.utcnow(),
            "delivered": False,
            "read": False,
            "charged": should_charge,
            "charge_amount": charge_amount if should_charge else 0
        }

        # ✅ Save to DB
        result = await chat_collection.insert_one(msg_doc)
        msg_doc["id"] = str(result.inserted_id)

        # ✅ Broadcast to all users in the room (except sender)
        await sio.emit(
            "new_message",
            {
                "id": msg_doc["id"],
                "roomId": room_id,
                "senderId": sender_id,
                "receiverId": receiver_id,
                "message": text,
                "timestamp": msg_doc["timestamp"].isoformat(),
                "charged": should_charge
            },
            room=room_id,
            skip_sid=sid
        )

    except Exception as e:
        await _emit_error(sid, "send_message", e)

# @sio.on("send_message")
# async def send_message(sid, data):
#     try:
#         room_id, sender_id, receiver_id, text = data["roomId"], data["senderId"], data["receiverId"], data["message"]
#         msg_doc = {
#             "room_id": room_id, "sender_id": sender_id, "receiver_id": receiver_id,
#             "message": text, "timestamp": datetime.utcnow(), "delivered": False, "read": False
#         }
#         result = await chat_collection.insert_one(msg_doc)
#         msg_doc["id"] = str(result.inserted_id)

#         await sio.emit("new_message", {
#             "id": msg_doc["id"], "roomId": room_id, "senderId": sender_id,
#             "receiverId": receiver_id, "message": text,
#             "timestamp": msg_doc["timestamp"].isoformat()
#         }, room=room_id)
#     except Exception as e:
#         await _emit_error(sid, "send_message", e)

# @sio.on("typing_start")
# async def typing_start(sid, data):
#     try:
#         room_id = (data or {}).get("roomId")
#         if not room_id:
#             raise ValueError("Missing roomId")

#         session = await sio.get_session(sid)
#         print(session, "session")
#         sender_id = session.get("userId")

#         # broadcast typing event to everyone in the room
#         await sio.emit(
#             "typing_start",   # 🔹 match frontend
#             {"senderId": sender_id, "isTyping": True, "roomId": room_id},
#             room=room_id,
#             skip_sid=sid  # prevent echo back to sender
#         )
#     except Exception as e:
#         await _emit_error(sid, "typing_start", e)


# @sio.on("typing_stop")
# async def typing_stop(sid, data):
#     try:
#         room_id = (data or {}).get("roomId")
#         if not room_id:
#             raise ValueError("Missing roomId")

#         session = await sio.get_session(sid)
#         sender_id = session.get("userId")

#         # broadcast stop typing event to everyone in the room
#         await sio.emit(
#             "typing_stop",   # 🔹 match frontend
#             {"senderId": sender_id, "isTyping": False, "roomId": room_id},
#             room=room_id,
#             skip_sid=sid
#         )
#     except Exception as e:
#         await _emit_error(sid, "typing_stop", e)


import time
from collections import defaultdict

# Store last typing event timestamps per (userId, roomId)
_last_typing_times = defaultdict(lambda: 0)
TYPING_COOLDOWN = 1.0  # seconds between broadcasts

@sio.on("typing_start")
async def typing_start(sid, data):
    try:
        room_id = (data or {}).get("roomId")
        if not room_id:
            raise ValueError("Missing roomId")

        session = await sio.get_session(sid)
        sender_id = session.get("userId")

        key = f"{sender_id}:{room_id}"
        now = time.time()

        # ✅ Debounce: only emit if cooldown has passed
        if now - _last_typing_times[key] >= TYPING_COOLDOWN:
            _last_typing_times[key] = now

            await sio.emit(
                "typing_start",
                {"senderId": sender_id, "isTyping": True, "roomId": room_id},
                room=room_id,
                skip_sid=sid
            )
    except Exception as e:
        await _emit_error(sid, "typing_start", e)


@sio.on("typing_stop")
async def typing_stop(sid, data):
    try:
        room_id = (data or {}).get("roomId")
        if not room_id:
            raise ValueError("Missing roomId")

        session = await sio.get_session(sid)
        sender_id = session.get("userId")

        key = f"{sender_id}:{room_id}"
        _last_typing_times[key] = 0  # Reset cooldown

        await sio.emit(
            "typing_stop",
            {"senderId": sender_id, "isTyping": False, "roomId": room_id},
            room=room_id,
            skip_sid=sid
        )
    except Exception as e:
        await _emit_error(sid, "typing_stop", e)


@sio.on("mark_read")
async def mark_read(sid, data):
    try:
        room_id = data["roomId"]
        receiver_id = data["receiverId"]
        message_ids = data.get("messageIds", [])
        
        # Update messages as read in database
        if message_ids:
            # Update specific messages
            await chat_collection.update_many(
                {
                    "_id": {"$in": [ObjectId(mid) for mid in message_ids if ObjectId.is_valid(mid)]},
                    "room_id": room_id,
                    "receiver_id": receiver_id
                },
                {"$set": {"read": True, "read_at": datetime.utcnow()}}
            )
        else:
            # Update all unread messages for this receiver in this room
            await chat_collection.update_many(
                {"room_id": room_id, "receiver_id": receiver_id, "read": {"$ne": True}},
                {"$set": {"read": True, "read_at": datetime.utcnow()}}
            )
        
        # Get the updated messages to send read receipts
        updated_messages = []
        if message_ids:
            cursor = chat_collection.find({
                "_id": {"$in": [ObjectId(mid) for mid in message_ids if ObjectId.is_valid(mid)]},
                "room_id": room_id
            })
        else:
            cursor = chat_collection.find({
                "room_id": room_id,
                "receiver_id": receiver_id,
                "read": True
            }).sort("timestamp", -1).limit(50)
            
        async for msg in cursor:
            updated_messages.append({
                "id": str(msg["_id"]),
                "roomId": msg["room_id"],
                "senderId": msg["sender_id"],
                "receiverId": msg["receiver_id"],
                "read": True,
                "read_at": msg.get("read_at").isoformat() if msg.get("read_at") else None
            })
        
        # Emit read receipt to all users in the room (including sender)
        await sio.emit("messages_read", {
            "roomId": room_id,
            "receiverId": receiver_id,
            "messages": updated_messages
        }, room=room_id)
        
        # Also emit to sender's personal room for immediate UI update
        for msg in updated_messages:
            sender_id = msg["senderId"]
            if sender_id != receiver_id:  # Don't send to same person
                await sio.emit("message_read_receipt", {
                    "messageId": msg["id"],
                    "roomId": room_id,
                    "readBy": receiver_id,
                    "readAt": msg["read_at"]
                }, room=f"user:{sender_id}")
                
    except Exception as e:
        await _emit_error(sid, "mark_read", e)

# @sio.on("get_history")
# async def get_history(sid, data):
#     try:
#         room_id = data["roomId"]
#         messages = []
#         cursor = chat_collection.find({"room_id": room_id}).sort("timestamp", 1)
#         async for msg in cursor:
#             messages.append({
#                 "id": str(msg["_id"]),
#                 "roomId": msg["room_id"],
#                 "senderId": msg["sender_id"],
#                 "receiverId": msg["receiver_id"],
#                 "message": msg["message"],
#                 "timestamp": msg["timestamp"].isoformat(),
#                 "delivered": msg.get("delivered", False),
#                 "read": msg.get("read", False)
#             })
#         await sio.emit("history_response", {"roomId": room_id, "messages": messages}, to=sid)
#     except Exception as e:
#         await _emit_error(sid, "get_history", e)


@sio.on("get_message_history")
async def get_message_history(sid, data):
    try:
        session = await sio.get_session(sid)
        user_id = session["userId"]
        
        

        other_user_id = (data or {}).get("other_user_id")
        page = int((data or {}).get("page", 1))
        page_size = min(int((data or {}).get("page_size", 50)), 100)
        
        
        print(user_id,"user_id",other_user_id)
        if not other_user_id:
            raise ValueError("Missing other_user_id")

        # still generate roomId (so payload stays consistent)
        room_id = str(await get_or_create_room(user_id, other_user_id))
        skip = (page - 1) * page_size

        # 🔹 Fetch by sender_id / receiver_id (instead of room_id)
        query = {
            "$or": [
                {"sender_id": user_id, "receiver_id": other_user_id},
                {"sender_id": other_user_id, "receiver_id": user_id},
            ]
        }

        cursor = (
            chat_collection.find(query)
            .sort("timestamp", -1)
            .skip(skip)
            .limit(page_size)
        )

        total_messages = await chat_collection.count_documents(query)

        messages = []
        async for msg in cursor:
            # Convert _id to string
            msg["id"] = str(msg["_id"])
            msg.pop("_id", None)

            safe_msg = make_json_safe(msg)

            # ensure boolean fields
            safe_msg["delivered"] = bool(safe_msg.get("delivered", False))
            safe_msg["read"] = bool(safe_msg.get("read", False))
            safe_msg["deleted"] = bool(safe_msg.get("deleted", False))

            # mark delivered if needed
            if safe_msg["receiver_id"] == user_id and not safe_msg.get("delivered"):
                await mark_messages_delivered(room_id, user_id)
                safe_msg["delivered"] = True

            # 🔹 Always attach roomId for consistency
            safe_msg["roomId"] = room_id

            messages.append(safe_msg)

        # fetch other user and make JSON safe
        other_user = await find_user_by_id_any(other_user_id) or {
            "_id": other_user_id,
            "username": "Unknown",
            "role": "unknown",
        }
        other_user["id"] = str(other_user.get("_id", other_user_id))
        other_user.pop("_id", None)
        other_user["online"] = (
            other_user_id in USER_SIDS and len(USER_SIDS[other_user_id]) > 0
        )
        other_user = make_json_safe(other_user)

        payload = {
            "roomId": room_id,  # still include roomId for frontend grouping
            "messages": messages,
            "otherUser": other_user,
            "pagination": {
                "total": total_messages,
                "page": page,
                "page_size": page_size,
                "total_pages": (total_messages + page_size - 1) // page_size,
            },
        }

        await sio.emit("message_history", make_json_safe(payload), to=sid)

    except Exception as e:
        import traceback
        print(f"Error in get_message_history: {e}")
        traceback.print_exc()
        await sio.emit("error", {"error": str(e)}, to=sid)





@sio.on("get_conversations")
async def get_conversations(sid):
    try:
        session = await sio.get_session(sid)
        user_id = session["userId"]
        print(user_id, "user_id")

        pipeline = [
            {"$match": {"$or": [{"sender_id": user_id}, {"receiver_id": user_id}]}},
            {"$sort": {"timestamp": -1}},
            {"$group": {
                "_id": "$room_id",
                "lastMessage": {"$first": "$$ROOT"},
                "unreadCount": {
                    "$sum": {
                        "$cond": [
                            {"$and": [
                                {"$eq": ["$receiver_id", user_id]},
                                {"$eq": ["$read", False]}
                            ]},
                            1, 0
                        ]
                    }
                }
            }},
            {"$sort": {"lastMessage.timestamp": -1}}
        ]

        cursor = chat_collection.aggregate(pipeline)
        conversations = []

        async for convo in cursor:
            last = convo["lastMessage"]

            # 🔹 Always resolve otherUserId as "the other participant"
            if last["sender_id"] == user_id:
                other_user_id = last["receiver_id"]
            else:
                other_user_id = last["sender_id"]

            # Fetch other user details
            other_user = await find_user_by_id_any(other_user_id)
            if other_user:
                # pick role-specific id if available
                role = other_user.get("role")
                if role == "patient":
                    other_user_id_final = other_user.get("patientId", str(other_user_id))
                elif role == "psychiatrist":
                    other_user_id_final = other_user.get("doctorId", str(other_user_id))
                elif role == "counselor":
                    other_user_id_final = other_user.get("counselorId", str(other_user_id))
                else:
                    other_user_id_final = str(other_user_id)

                other_user["id"] = str(other_user_id_final)
                other_user.pop("_id", None)
                other_user["online"] = (
                    other_user_id in USER_SIDS and len(USER_SIDS[other_user_id]) > 0
                )
            else:
                other_user = {
                    "id": str(other_user_id),
                    "username": "Unknown",
                    "role": "unknown",
                    "online": False
                }

            conversation_obj = {
                "roomId": str(convo["_id"]),
                "lastMessage": {
                    "id": str(last["_id"]),
                    "senderId": last.get("sender_id"),
                    "receiverId": last.get("receiver_id"),
                    "message": last.get("message"),
                    "timestamp": _iso(last.get("timestamp")),
                    "read": bool(last.get("read", False))
                },
                "unreadCount": convo.get("unreadCount", 0),
                "otherUser": other_user
            }

            conversations.append(conversation_obj)

        await sio.emit("conversations", {"conversations": conversations}, to=sid)

    except Exception as e:
        print(f"Error in get_conversations: {e}")
        await sio.emit("error", {"error": "Failed to retrieve conversations"}, to=sid)


import asyncio
@sio.on("get_users")
async def get_users(sid, data=None):
    try:
        session = await sio.get_session(sid)
        viewer_role = session.get("role")
        if not viewer_role:
            await sio.emit("get_users_response", {"status": "error", "message": "Session missing role"}, to=sid)
            return

        def roles_visible_for(role: str) -> list[str]:
            if role in ("patient", "user"):
                return ["psychiatrist", "counselor"]
            if role == "psychiatrist":
                return ["user", "patient"]
            if role == "counselor":
                return ["user", "patient"]
            return []

        targets = roles_visible_for(viewer_role)
        if not targets:
            await sio.emit("get_users_response", {"status": "error", "message": "Invalid role"}, to=sid)
            return

        results: list[dict] = []

        async def load_many(collection_name: str, role_label: str):
            if collection_name not in await db.list_collection_names():
                print(f"Warning: collection {collection_name} does not exist")
                return
            projection = {"password": 0}
            cursor = db[collection_name].find({}, projection)
            async for doc in cursor:
                user = serialize_user(doc, role_hint=role_label)
                if asyncio.iscoroutine(user):
                    user = await user
                results.append(user)

        for role in targets:
            if role not in ROLE_COLLECTIONS:
                print(f"Warning: role {role} not in ROLE_COLLECTIONS")
                continue
            coll, _ = ROLE_COLLECTIONS[role]
            await load_many(coll, role)

       
        safe_results = convert_objectid_to_str(results)

        await sio.emit("get_users_response", {"status": "success", "users": safe_results}, to=sid)

    except Exception as e:
        import traceback
        traceback.print_exc()
        await sio.emit("get_users_response", {"status": "error", "message": str(e)}, to=sid)



# =========================
# Call Events
# =========================
calls_collection = db["calls"]


class CallInitiatePayload(BaseModel):
    callerId: str
    callerRole: Literal["user", "psychiatrist", "counselor"]
    calleeId: str
    calleeRole: Literal["user", "psychiatrist", "counselor"]
    callType: Literal["audio", "video"]
    appointmentId: Optional[str] = None


class CallSessionPayload(BaseModel):
    sessionId: str


class CallEndPayload(BaseModel):
    sessionId: str
    durationSec: Optional[int] = None


class CallHistoryPayload(BaseModel):
    userId: str
    page: int = Field(default=1, ge=1)
    limit: int = Field(default=50, ge=1, le=100)

# remove direct FastAPI startup decorator (avoids circular import).
# Provide a function that app.main can call to register the startup task.
def register_socket_startup(fastapi_app):
    @fastapi_app.on_event("startup")
    async def _startup_event():
        asyncio.create_task(monitor_calls())

# new constants
PER_MINUTE_CHARGE = 5.0
COMMISSION_RATE = 0.10  # 10%
PLATFORM_WALLET_USERID = "platform"  # wallet entry for platform commission fallback
CHAT_MESSAGE_CHARGE = 2.0  # ₹2 per message from user to doctor/counselor
CHAT_FREE_MESSAGES = 5  # First 5 messages are free per day


async def monitor_calls():
    while True:
        now = datetime.utcnow()
        active_calls_cursor = calls_collection.find({"status": "accepted"})
        async for call in active_calls_cursor:
            elapsed = (now - call.get("updatedAt", call.get("createdAt", now))).total_seconds()
            if elapsed >= 60:
                session_id = call["sessionId"]
                caller_id = call["callerId"]
                caller_role = call.get("callerRole", "user")
                callee_id = call["calleeId"]
                callee_role = call.get("calleeRole")

                # refresh call doc
                call = await calls_collection.find_one({"sessionId": session_id})
                if not call:
                    continue

                print("--------------------------------call", call)

                # Determine who pays: Always the user, regardless of who initiated
                user_id = None
                user_role = None
                provider_id = None
                provider_role = None
                
                if caller_role == "user":
                    user_id = caller_id
                    user_role = caller_role
                    provider_id = callee_id
                    provider_role = callee_role
                elif callee_role == "user":
                    user_id = callee_id
                    user_role = callee_role
                    provider_id = caller_id
                    provider_role = caller_role
                
                # If no user in the call (professional-to-professional), no charging
                if not user_id:
                    await calls_collection.update_one(
                        {"sessionId": session_id},
                        {"$set": {"updatedAt": now}, "$inc": {"durationSec": 60}}
                    )
                    continue

                # Prefer stored paidSecRemaining; if missing compute from wallet and persist
                paid_rem = int(call.get("paidSecRemaining") or 0)
                if paid_rem <= 0:
                    wallet_balance = await get_wallet_balance(user_id)
                    paid_minutes = int(wallet_balance // PER_MINUTE_CHARGE)
                    paid_rem = paid_minutes * 60
                    await calls_collection.update_one(
                        {"sessionId": session_id},
                        {"$set": {"paidSecRemaining": paid_rem, "maxPaidMinutes": paid_minutes}}
                    )

                print("--------------------------------paid_rem", paid_rem)

                # if paid seconds available, charge one minute
                if paid_rem >= 60:
                    user_balance = await get_wallet_balance(user_id)
                    print("--------------------------------user_balance", user_balance)
                    if user_balance < PER_MINUTE_CHARGE:
                        await _end_call_by_sessionid(session_id, reason="insufficient_balance")
                        await sio.emit("call_ended_for_insufficient_balance", {
                            "sessionId": session_id,
                            "message": "Call ended: insufficient wallet balance."
                        }, room=f"user:{user_id}")
                        continue

                    
                    # deduct from user (who pays)
                    await update_wallet_balance(user_id, -PER_MINUTE_CHARGE)
                    doctor_rate = PER_MINUTE_CHARGE
                    if provider_role == "psychiatrist":
                        rate_doc = await psychiatrist_call_rates.find_one({"doctorId": provider_id})
                        if rate_doc:
                            doctor_rate = float(rate_doc.get("ratePerMinute", PER_MINUTE_CHARGE))

                    per_minute_charge = doctor_rate

                    # compute commission and provider share
                    commission = round(per_minute_charge * COMMISSION_RATE, 2)
                    provider_amount = round(per_minute_charge - commission, 2)

                    # credit provider (doctor/counselor)
                    await update_wallet_balance(provider_id, provider_amount)

                    # try to credit referrer/clientLink, else platform
                    coll_name, id_field = ROLE_COLLECTIONS.get(provider_role, (None, None))
                    ref_target = None
                    if coll_name:
                        provider_doc = await db[coll_name].find_one({id_field: provider_id})
                        if provider_doc:
                            ref_target = provider_doc.get("clientLink") or provider_doc.get("referrerId")

                    if ref_target:
                        await update_wallet_balance(ref_target, commission)
                    else:
                        await update_wallet_balance(PLATFORM_WALLET_USERID, commission)

                    # update call doc
                    paid_rem -= 60
                    await calls_collection.update_one(
                        {"sessionId": session_id},
                        {"$set": {"paidSecRemaining": paid_rem, "updatedAt": now}, "$inc": {"durationSec": 60}}
                    )

                    # emit events
                    new_user_balance = await get_wallet_balance(user_id)
                    await sio.emit("balance_deducted", {
                        "sessionId": session_id,
                        "amount": PER_MINUTE_CHARGE,
                        "newBalance": new_user_balance,
                        "message": f"Rs {PER_MINUTE_CHARGE} deducted for 1 minute of call."
                    }, room=f"user:{user_id}")

                    await sio.emit("provider_credited", {
                        "sessionId": session_id,
                        "providerId": provider_id,
                        "amount": provider_amount,
                        "commission": commission
                    }, room=f"user:{provider_id}")

                    # low-balance warning if less than 60 seconds left
                    if paid_rem < 60:
                        await sio.emit("low_balance_warning", {
                            "sessionId": session_id,
                            "message": "You have only 1 minute left. Please recharge your wallet."
                        }, room=f"user:{user_id}")

                else:
                    # no paid seconds -> end call
                    await _end_call_by_sessionid(session_id, reason="insufficient_balance")
                    await sio.emit("call_ended_for_insufficient_balance", {
                        "sessionId": session_id,
                        "message": "Call ended: no paid time remaining."
                    }, room=f"user:{user_id}")

        await asyncio.sleep(10)
from app.database.mongo import wallet_collection, patient_collection, db as mongo_db    
async def get_wallet_balance(user_id: str) -> float:
    wallet = await wallet_collection.find_one({"userId": user_id})
    print(f"[DEBUG] get_wallet_balance user={user_id} wallet={wallet}")
    return float(wallet.get("balance", 0)) if wallet else 0.0

async def update_wallet_balance(user_id: str, amount: float, *, from_user_id: str = None, reason: str = None):
    # Update wallet balance
    result = await wallet_collection.update_one(
        {"userId": user_id},
        {"$set": {"userId": user_id}, "$inc": {"balance": amount}},
        upsert=True
    )
    # Fetch new balance
    wallet = await wallet_collection.find_one({"userId": user_id})
    new_balance = float(wallet.get("balance", 0)) if wallet else 0.0

    # Prepare transaction log
    tx_doc = {
        "fromUserId": from_user_id if from_user_id else user_id if amount < 0 else "external",
        "toUserId": user_id if amount > 0 else from_user_id if from_user_id else user_id,
        "amount": abs(amount),
        "type": "credit" if amount > 0 else "debit",
        "reason": reason or ("Wallet recharge" if amount > 0 else "Wallet deduction"),
        "timestamp": datetime.utcnow(),
        "balanceAfter": new_balance,
    }
    await mongo_db["wallet_transactions"].insert_one(tx_doc)
    
    # Emit socket event to notify the user of balance update
    try:
        if amount > 0:
            # Money added (recharge)
            await sio.emit("wallet_recharged", {
                "newBalance": new_balance,
                "amount": amount,
                "message": f"₹{amount} added to your wallet successfully!"
            }, room=f"user:{user_id}")
        else:
            # Money deducted
            await sio.emit("balance_deducted", {
                "newBalance": new_balance,
                "amount": abs(amount),
                "message": f"₹{abs(amount)} deducted from your wallet"
            }, room=f"user:{user_id}")
    except Exception as e:
        print(f"[ERROR] Failed to emit socket event for wallet balance update: {e}")

# helper to gracefully end call from internal logic (no socket sid)
async def _end_call_by_sessionid(session_id: str, reason: str = "ended"):
    doc = await calls_collection.find_one({"sessionId": session_id})
    if not doc:
        return
    now = datetime.utcnow()
    start = doc.get("createdAt")
    duration = int((now - start).total_seconds()) if start else doc.get("durationSec", 0)
    status = "completed" if doc.get("status") == "accepted" else "missed"
    if reason == "insufficient_balance":
        status = "ended_insufficient_balance"

    await calls_collection.update_one(
        {"sessionId": session_id},
        {"$set": {"status": status, "updatedAt": now, "durationSec": duration}}
    )

    payload = {"sessionId": session_id, "status": status, "durationSec": duration, "reason": reason}
    await sio.emit("call_end", payload, room=f"user:{doc['callerId']}")
    await sio.emit("call_end", payload, room=f"user:{doc['calleeId']}")

import app.database.mongo as doctor_call_rates

@sio.on("call_initiate")
async def handle_call_initiate(sid, data: Dict[str, Any]):
    try:
        body = CallInitiatePayload(**(data or {}))
        session = await _get_socket_user(sid)
        if session["userId"] != body.callerId:
            raise ValueError("Forbidden: callerId mismatch")
        await _join_personal_room_if_needed(sid, session["userId"])

        await _ensure_active(body.callerId, body.callerRole)
        await _ensure_active(body.calleeId, body.calleeRole)
        
        # Check if callee is online
        if not await _user_online(body.calleeId):
            raise ValueError(f"{body.calleeRole.capitalize()} is currently offline. Please try again later.")
            
        if await _user_busy(body.callerId) or await _user_busy(body.calleeId):
            raise ValueError("The person you're trying to call is currently busy on another call.")

        # Determine who pays: Always the user in the call, regardless of who initiates
        user_id = None
        user_role = None
        provider_id = None
        provider_role = None
        
        if body.callerRole == "user":
            user_id = body.callerId
            user_role = body.callerRole
            provider_id = body.calleeId
            provider_role = body.calleeRole
        elif body.calleeRole == "user":
            user_id = body.calleeId
            user_role = body.calleeRole
            provider_id = body.callerId
            provider_role = body.callerRole
        else:
            # Both are doctors/counselors - no charging needed
            user_id = None
            
        wallet_balance = 0
        paid_seconds = 0
        paid_minutes = 0
        
        if user_id:
            # Check user's wallet balance
            wallet_balance = await get_wallet_balance(user_id)
            print(f"[DEBUG] handle_call_initiate user={user_id} wallet_balance={wallet_balance}")
            #per_minute_charge = PER_MINUTE_CHARGE
            # If user → provider (doctor/counselor), check if provider has a custom rate

        per_minute_charge = PER_MINUTE_CHARGE
        if user_id and provider_id and provider_role == "psychiatrist":
            rate_doc = await doctor_call_rates.find_one({"doctorId": provider_id})
            if rate_doc:
                doctor_rate = float(rate_doc.get("ratePerMinute", PER_MINUTE_CHARGE))

            per_minute_charge = doctor_rate

            if wallet_balance < per_minute_charge:
                raise ValueError("Insufficient balance to start the call. Please recharge your wallet.")

            paid_minutes = int(wallet_balance // per_minute_charge)
            paid_seconds = paid_minutes * 60
            print(f"[DEBUG] User {user_id} has {paid_minutes} minutes of call time available")
        else:
            # No user in call (doctor-to-doctor or counselor-to-counselor) - unlimited
            paid_minutes = 9999  # Large number for unlimited
            paid_seconds = 9999 * 60
            print(f"[DEBUG] Professional-to-professional call - unlimited duration") 

        session_id = uuid.uuid4().hex
        now = datetime.utcnow()
        record = {
            "sessionId": session_id,
            "callerId": body.callerId,
            "callerRole": body.callerRole,
            "calleeId": body.calleeId,
            "calleeRole": body.calleeRole,
            "callType": body.callType,
            "status": "initiated",
            "appointmentId": body.appointmentId,
            "payingUserId": user_id,  # Track who pays for the call
            "providerId": provider_id,  # Track who provides the service
            "createdAt": now,
            "updatedAt": now,
            "durationSec": 0,
            "paidSecRemaining": paid_seconds,
            "maxPaidMinutes": paid_minutes
        }
        result = await calls_collection.insert_one(record)
        print(f"[DEBUG] calls_collection.insert_one -> inserted_id={result.inserted_id!r} paidSecRemaining={paid_seconds}")

        # Invite callee
        await sio.emit("call_invite", {
            "sessionId": session_id,
            "fromUserId": body.callerId,
            "fromRole": body.callerRole,
            "toUserId": body.calleeId,
            "toRole": body.calleeRole,
            "callType": body.callType,
            "appointmentId": body.appointmentId,
            "createdAt": _iso(now),
        }, room=f"user:{body.calleeId}")

        # Notify caller
        await sio.emit("call_initiated", {
            "success": True, "sessionId": session_id, "zegoAppId": os.getenv("ZEGO_APP_ID")
        }, to=sid)

    except ValidationError as ve:
        await _emit_error(sid, "call_initiate", "Invalid call data provided. Please try again.")
    except Exception as e:
        error_message = str(e)
        
        # Convert technical errors to user-friendly messages
        if "Insufficient balance" in error_message:
            error_message = "💰 Insufficient wallet balance to start the call. Please recharge your wallet and try again."
        elif "currently offline" in error_message:
            error_message = "📱 The person you're trying to call is currently offline. Please try again later."
        elif "busy" in error_message:
            error_message = "📞 The person you're trying to call is currently busy on another call. Please try again later."
        elif "not active" in error_message:
            error_message = "❌ The person you're trying to call is not available. Please try again later."
        elif "Forbidden" in error_message:
            error_message = "🚫 You don't have permission to make this call. Please contact support."
        else:
            error_message = f"❌ Unable to start the call: {error_message}"
            
        await _emit_error(sid, "call_initiate", error_message)


@sio.on("call_accept")
async def handle_call_accept(sid, data: Dict[str, Any]):
    try:
        body = CallSessionPayload(**(data or {}))
        session = await _get_socket_user(sid)
        doc = await _require_session(body.sessionId, calls_collection)
        if doc.get("status") != "initiated":
            raise ValueError("Call cannot be accepted")
        if session["userId"] not in (doc["callerId"], doc["calleeId"]):
            raise ValueError("Forbidden: not a participant")

        # Ensure paidSecRemaining exists at accept time (compute from wallet if missing)
        caller_id = doc["callerId"]
        paid_rem = int(doc.get("paidSecRemaining") or 0)
        if paid_rem <= 0:
            wallet_balance = await get_wallet_balance(caller_id)
            if wallet_balance < PER_MINUTE_CHARGE:
                await _emit_error(sid, "call_accept", "Insufficient balance to accept the call")
                return
            paid_minutes = int(wallet_balance // PER_MINUTE_CHARGE)
            paid_rem = paid_minutes * 60
            await calls_collection.update_one(
                {"sessionId": body.sessionId},
                {"$set": {"paidSecRemaining": paid_rem, "maxPaidMinutes": paid_minutes}}
            )

        await calls_collection.update_one({"sessionId": body.sessionId},
                                         {"$set": {"status": "accepted", "updatedAt": datetime.utcnow()}})

        payload = {"sessionId": body.sessionId, "status": "accepted"}
        await sio.emit("call_accept", payload, room=f"user:{doc['callerId']}")
        await sio.emit("call_accept", payload, room=f"user:{doc['calleeId']}")

    except ValidationError as ve:
        await _emit_error(sid, "call_accept", ve.errors())
    except Exception as e:
        await _emit_error(sid, "call_accept", str(e))


@sio.on("call_reject")
async def handle_call_reject(sid, data: Dict[str, Any]):
    try:
        body = CallSessionPayload(**(data or {}))
        session = await _get_socket_user(sid)
        doc = await _require_session(body.sessionId, calls_collection)
        if doc.get("status") != "initiated":
            raise ValueError("Call cannot be rejected")
        if session["userId"] not in (doc["callerId"], doc["calleeId"]):
            raise ValueError("Forbidden: not a participant")

        await calls_collection.update_one({"sessionId": body.sessionId},
                                         {"$set": {"status": "rejected", "updatedAt": datetime.utcnow()}})

        payload = {"sessionId": body.sessionId, "status": "rejected"}
        await sio.emit("call_reject", payload, room=f"user:{doc['callerId']}")
        await sio.emit("call_reject", payload, room=f"user:{doc['calleeId']}")

    except ValidationError as ve:
        await _emit_error(sid, "call_reject", ve.errors())
    except Exception as e:
        await _emit_error(sid, "call_reject", str(e))


@sio.on("call_end")
async def handle_call_end(sid, data: Dict[str, Any]):
    try:
        body = CallEndPayload(**(data or {}))
        session = await _get_socket_user(sid)
        doc = await _require_session(body.sessionId, calls_collection)
        if session["userId"] not in (doc["callerId"], doc["calleeId"]):
            raise ValueError("Forbidden: not a participant")

        now = datetime.utcnow()
        start = doc.get("createdAt")
        duration = body.durationSec or (int((now - start).total_seconds()) if start else 0)
        status = "completed" if doc.get("status") == "accepted" else "missed"

        # Update call status to completed/missed
        await calls_collection.update_one({"sessionId": body.sessionId},
                                         {"$set": {"status": status, "updatedAt": now, "durationSec": duration}})

        # Notify both participants that call ended
        payload = {"sessionId": body.sessionId, "status": status, "durationSec": duration}
        await sio.emit("call_end", payload, room=f"user:{doc['callerId']}")
        await sio.emit("call_end", payload, room=f"user:{doc['calleeId']}")
        
        print(f"[DEBUG] Call {body.sessionId} ended with status: {status}, duration: {duration}s")

    except ValidationError as ve:
        await _emit_error(sid, "call_end", ve.errors())
    except Exception as e:
        await _emit_error(sid, "call_end", str(e))


@sio.on("call_history")
async def handle_call_history(sid, data: Dict[str, Any]):
    try:
        body = CallHistoryPayload(**(data or {}))
        session = await _get_socket_user(sid)
        if session["userId"] != body.userId:
            raise ValueError("Forbidden: cannot access another user's history")

        skip = (body.page - 1) * body.limit
        q = {"$or": [{"callerId": body.userId}, {"calleeId": body.userId}]}

        items = []
        cursor = calls_collection.find(q).sort("createdAt", -1).skip(skip).limit(body.limit)
        async for d in cursor:
            items.append(_call_doc_to_public(d))

        total = await calls_collection.count_documents(q)
        await sio.emit("call_history_response", {
            "success": True,
            "page": body.page,
            "limit": body.limit,
            "total": total,
            "total_pages": (total + body.limit - 1) // body.limit,
            "items": items
        }, to=sid)

    except ValidationError as ve:
        await _emit_error(sid, "call_history", ve.errors())
    except Exception as e:
        await _emit_error(sid, "call_history", str(e))


@sio.on("check_user_status")
async def handle_check_user_status(sid, data: Dict[str, Any]):
    """Check if a specific user is currently online"""
    try:
        user_id = data.get("userId")
        role = data.get("role", "user")
        
        if not user_id:
            raise ValueError("userId is required")
            
        # Check if user is online using our existing function
        is_online = await _user_online(user_id)
        
        await sio.emit("user_status_response", {
            "userId": user_id,
            "role": role,
            "isOnline": is_online,
            "timestamp": datetime.utcnow().isoformat()
        }, to=sid)
        
    except Exception as e:
        await _emit_error(sid, "check_user_status", str(e))


@sio.on("user_heartbeat")
async def handle_user_heartbeat(sid, data: Dict[str, Any]):
    """Handle periodic heartbeat from users to track activity"""
    try:
        user_id = data.get("userId")
        role = data.get("role")
        timestamp = data.get("timestamp")
        
        if user_id:
            # Update user's last activity timestamp (optional - for future features)
            print(f"[HEARTBEAT] User {user_id} ({role}) is active at {timestamp}")
            
            # Optional: Send acknowledgment back to client
            await sio.emit("heartbeat_ack", {
                "status": "received",
                "timestamp": datetime.utcnow().isoformat()
            }, to=sid)
        
    except Exception as e:
        print(f"[HEARTBEAT ERROR] {str(e)}")
        # Don't emit error for heartbeat to avoid spam

