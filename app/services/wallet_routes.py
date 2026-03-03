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
from app.utils.dependencies import get_current_user


router = APIRouter(prefix="/api/wallet", tags=["Wallet System"])



@router.post("/recharge_wallet")
async def recharge_wallet(
    user_id: str,
    amount: float,
    current_user: dict = Depends(get_current_user)
):
    """
    Recharge wallet for `user_id`. The authenticated user will be recorded as the initiator
    (fromUserId) in the wallet transaction. If payment gateway is used, integrate it here
    before calling update_wallet_balance.
    """
    # perform recharge and persist transaction
    await update_wallet_balance(user_id, amount, from_user_id=current_user.get("userId"), reason="Wallet recharge")
    new_balance = await get_wallet_balance(user_id)
    return {"success": True, "message": "Wallet recharged successfully", "userId": user_id, "newBalance": new_balance}


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


@router.get("/transaction_history")
async def transaction_history(
    user_id: str = Query(..., description="User ID to fetch transaction history for"),
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=100)
):
    """
    Get all wallet transactions for a user (money added or deducted).
    Shows who gave to whom, amount, type, and timestamp.
    """
    skip = (page - 1) * limit
    collection = db["wallet_transactions"]

    # Find transactions where user is sender or receiver
    query = {
        "$or": [
            {"fromUserId": user_id},
            {"toUserId": user_id}
        ]
    }
    cursor = (
        collection.find(query)
        .sort("timestamp", -1)
        .skip(skip)
        .limit(limit)
    )
    items = []
    async for tx in cursor:
        items.append({
            "id": str(tx.get("_id")),
            "fromUserId": tx.get("fromUserId"),
            "toUserId": tx.get("toUserId"),
            "amount": tx.get("amount"),
            "type": tx.get("type"),  # "credit" or "debit"
            "reason": tx.get("reason"),
            "timestamp": tx.get("timestamp").isoformat() if isinstance(tx.get("timestamp"), datetime) else tx.get("timestamp"),
            "balanceAfter": tx.get("balanceAfter"),
        })
    total = await collection.count_documents(query)
    return {
        "success": True,
        "userId": user_id,
        "page": page,
        "limit": limit,
        "total": total,
        "transactions": items
    }
