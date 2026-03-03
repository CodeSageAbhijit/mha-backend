import asyncio
from app.services.chat_routes import monitor_calls
from app.services.chat_routes import get_wallet_balance, update_wallet_balance
from fastapi import APIRouter, Form, Depends, UploadFile, File, Query
from app.database.mongo import db, wallet_collection
from fastapi import Query
from app.utils.dependencies import get_admin_user
from app.utils.error_response import error_response
from app.utils.constants import upload_profile_photo
from bson import ObjectId
from datetime import datetime


router = APIRouter(prefix="/api/wallet", tags=["Wallet System"])



@router.post("/recharge_wallet")
async def recharge_wallet(user_id: str, amount: float):
    # Integrate payment gateway logic here
    await update_wallet_balance(user_id, amount)
    return {"success": True, "message": "Wallet recharged successfully"}


@router.get("/call")
async def debug_get_call(session_id: str = Query(...)):
    doc = await db["calls"].find_one({"sessionId": session_id})
    if not doc:
        return {"found": False}
    # normalize datetimes/ids
    doc["_id"] = str(doc["_id"])
    if isinstance(doc.get("createdAt"), datetime):
        doc["createdAt"] = doc["createdAt"].isoformat()
    if isinstance(doc.get("updatedAt"), datetime):
        doc["updatedAt"] = doc["updatedAt"].isoformat()
    return {"found": True, "call": doc}


@router.get("/balance")
async def get_balance(user_id: str = Query(...)):
    doc = await wallet_collection.find_one({"userId": user_id})
    return {"userId": user_id, "balance": float(doc.get("balance", 0)) if doc else 0.0}
