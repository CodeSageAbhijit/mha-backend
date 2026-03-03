# from datetime import datetime
# from typing import Optional, Literal, List, Any, Dict
# import uuid
# import os

# from pydantic import BaseModel, Field, ValidationError

# from app.database.mongo import db
# from app.utils.jwt_tokens import decrypt_token
# from app.services.chat_routes import sio  # re-use the same Socket.IO server instance
# # Ensure Zego socket events are registered
# from app.services.zego_socket import *  # noqa: F401,F403


# # =========================
# # Call Events
# # =========================
# class CallInitiatePayload(BaseModel):
#     callerId: str
#     callerRole: Literal["user", "doctor", "counselor"]
#     calleeId: str
#     calleeRole: Literal["user", "doctor", "counselor"]
#     callType: Literal["audio", "video"]
#     appointmentId: Optional[str] = None


# class CallSessionPayload(BaseModel):
#     sessionId: str


# class CallEndPayload(BaseModel):
#     sessionId: str
#     durationSec: Optional[int] = None


# class CallHistoryPayload(BaseModel):
#     userId: str
#     page: int = Field(default=1, ge=1)
#     limit: int = Field(default=50, ge=1, le=100)


# # =========================
# # Call Events
# # =========================
# calls_collection = db["calls"]


# class CallInitiatePayload(BaseModel):
#     callerId: str
#     callerRole: Literal["user", "doctor", "counselor"]
#     calleeId: str
#     calleeRole: Literal["user", "doctor", "counselor"]
#     callType: Literal["audio", "video"]
#     appointmentId: Optional[str] = None


# class CallSessionPayload(BaseModel):
#     sessionId: str


# class CallEndPayload(BaseModel):
#     sessionId: str
#     durationSec: Optional[int] = None


# class CallHistoryPayload(BaseModel):
#     userId: str
#     page: int = Field(default=1, ge=1)
#     limit: int = Field(default=50, ge=1, le=100)
    



# @sio.on("call_initiate")
# async def handle_call_initiate(sid, data: Dict[str, Any]):
#     try:
#         body = CallInitiatePayload(**(data or {}))
#         session = await _get_socket_user(sid)
#         if session["userId"] != body.callerId:
#             raise ValueError("Forbidden: callerId mismatch")
#         await _join_personal_room_if_needed(sid, session["userId"])

#         await _ensure_active(body.callerId, body.callerRole)
#         await _ensure_active(body.calleeId, body.calleeRole)
#         if await _user_busy(body.callerId) or await _user_busy(body.calleeId):
#             raise ValueError("One of the users is busy")

#         session_id = uuid.uuid4().hex
#         now = datetime.utcnow()
#         record = {
#             "sessionId": session_id,
#             "callerId": body.callerId,
#             "callerRole": body.callerRole,
#             "calleeId": body.calleeId,
#             "calleeRole": body.calleeRole,
#             "callType": body.callType,
#             "status": "initiated",
#             "appointmentId": body.appointmentId,
#             "createdAt": now,
#             "updatedAt": now,
#             "durationSec": 0,
#         }
#         await calls_collection.insert_one(record)

#         # Invite callee
#         await sio.emit("call_invite", {
#             "sessionId": session_id,
#             "fromUserId": body.callerId,
#             "fromRole": body.callerRole,
#             "toUserId": body.calleeId,
#             "toRole": body.calleeRole,
#             "callType": body.callType,
#             "appointmentId": body.appointmentId,
#             "createdAt": _iso(now),
#         }, room=f"user:{body.calleeId}")

#         # Notify caller
#         await sio.emit("call_initiated", {
#             "success": True, "sessionId": session_id, "zegoAppId": os.getenv("ZEGO_APP_ID")
#         }, to=sid)

#     except ValidationError as ve:
#         await _emit_error(sid, "call_initiate", ve.errors())
#     except Exception as e:
#         await _emit_error(sid, "call_initiate", str(e))


# @sio.on("call_accept")
# async def handle_call_accept(sid, data: Dict[str, Any]):
#     try:
#         body = CallSessionPayload(**(data or {}))
#         session = await _get_socket_user(sid)
#         doc = await _require_session(body.sessionId, calls_collection)
#         if doc.get("status") != "initiated":
#             raise ValueError("Call cannot be accepted")
#         if session["userId"] not in (doc["callerId"], doc["calleeId"]):
#             raise ValueError("Forbidden: not a participant")

#         await calls_collection.update_one({"sessionId": body.sessionId},
#                                          {"$set": {"status": "accepted", "updatedAt": datetime.utcnow()}})

#         payload = {"sessionId": body.sessionId, "status": "accepted"}
#         await sio.emit("call_accept", payload, room=f"user:{doc['callerId']}")
#         await sio.emit("call_accept", payload, room=f"user:{doc['calleeId']}")

#     except ValidationError as ve:
#         await _emit_error(sid, "call_accept", ve.errors())
#     except Exception as e:
#         await _emit_error(sid, "call_accept", str(e))


# @sio.on("call_reject")
# async def handle_call_reject(sid, data: Dict[str, Any]):
#     try:
#         body = CallSessionPayload(**(data or {}))
#         session = await _get_socket_user(sid)
#         doc = await _require_session(body.sessionId, calls_collection)
#         if doc.get("status") != "initiated":
#             raise ValueError("Call cannot be rejected")
#         if session["userId"] not in (doc["callerId"], doc["calleeId"]):
#             raise ValueError("Forbidden: not a participant")

#         await calls_collection.update_one({"sessionId": body.sessionId},
#                                          {"$set": {"status": "rejected", "updatedAt": datetime.utcnow()}})

#         payload = {"sessionId": body.sessionId, "status": "rejected"}
#         await sio.emit("call_reject", payload, room=f"user:{doc['callerId']}")
#         await sio.emit("call_reject", payload, room=f"user:{doc['calleeId']}")

#     except ValidationError as ve:
#         await _emit_error(sid, "call_reject", ve.errors())
#     except Exception as e:
#         await _emit_error(sid, "call_reject", str(e))


# @sio.on("call_end")
# async def handle_call_end(sid, data: Dict[str, Any]):
#     try:
#         body = CallEndPayload(**(data or {}))
#         session = await _get_socket_user(sid)
#         doc = await _require_session(body.sessionId, calls_collection)
#         if session["userId"] not in (doc["callerId"], doc["calleeId"]):
#             raise ValueError("Forbidden: not a participant")

#         now = datetime.utcnow()
#         start = doc.get("createdAt")
#         duration = body.durationSec or (int((now - start).total_seconds()) if start else 0)
#         status = "completed" if doc.get("status") == "accepted" else "missed"

#         await calls_collection.update_one({"sessionId": body.sessionId},
#                                          {"$set": {"status": status, "updatedAt": now, "durationSec": duration}})

#         payload = {"sessionId": body.sessionId, "status": status, "durationSec": duration}
#         await sio.emit("call_end", payload, room=f"user:{doc['callerId']}")
#         await sio.emit("call_end", payload, room=f"user:{doc['calleeId']}")

#     except ValidationError as ve:
#         await _emit_error(sid, "call_end", ve.errors())
#     except Exception as e:
#         await _emit_error(sid, "call_end", str(e))


# @sio.on("call_history")
# async def handle_call_history(sid, data: Dict[str, Any]):
#     try:
#         body = CallHistoryPayload(**(data or {}))
#         session = await _get_socket_user(sid)
#         if session["userId"] != body.userId:
#             raise ValueError("Forbidden: cannot access another user's history")

#         skip = (body.page - 1) * body.limit
#         q = {"$or": [{"callerId": body.userId}, {"calleeId": body.userId}]}

#         items = []
#         cursor = calls_collection.find(q).sort("createdAt", -1).skip(skip).limit(body.limit)
#         async for d in cursor:
#             items.append(_call_doc_to_public(d))

#         total = await calls_collection.count_documents(q)
#         await sio.emit("call_history_response", {
#             "success": True,
#             "page": body.page,
#             "limit": body.limit,
#             "total": total,
#             "total_pages": (total + body.limit - 1) // body.limit,
#             "items": items
#         }, to=sid)

#     except ValidationError as ve:
#         await _emit_error(sid, "call_history", ve.errors())
#     except Exception as e:
#         await _emit_error(sid, "call_history", str(e))
