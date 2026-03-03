from fastapi import APIRouter, Depends, HTTPException, status
from app.database.mongo import db
from app.models.login_history_schemas import LoginHistory
from bson import ObjectId
from datetime import datetime
from typing import Optional

router = APIRouter(prefix="/api/login-history", tags=["Login History"])

login_history_collection = db["login_history"]

# POST: Store login event
@router.post("/", status_code=201)
async def store_login_event(payload: LoginHistory):
    try:
        event = payload.dict()
        event["createdAt"] = datetime.utcnow()
        result = await login_history_collection.insert_one(event)
        event["id"] = str(result.inserted_id)
        return {"success": True, "message": "Login event stored", "data": event}
    except Exception as e:
        raise HTTPException(status_code=500, detail={
            "success": False,
            "message": "Failed to store login event",
            "error": str(e),
            "errors": [str(e)]
        })

# GET: Get login history for a user
@router.get("/{userId}", status_code=200)
async def get_login_history(userId: str, role: Optional[str] = None):
    try:
        query = {"userId": userId}
        if role:
            query["role"] = role
        history = await login_history_collection.find(query).to_list(length=100)
        for h in history:
            h["id"] = str(h["_id"])
            h.pop("_id", None)
        return {"success": True, "count": len(history), "data": history}
    except Exception as e:
        raise HTTPException(status_code=500, detail={
            "success": False,
            "message": "Failed to fetch login history",
            "error": str(e),
            "errors": [str(e)]
        })
