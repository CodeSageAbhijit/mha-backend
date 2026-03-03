# app/services/room_routes.py
from fastapi import APIRouter, HTTPException
from app.database.mongo import rooms_collection
from datetime import datetime
from app.database.mongo import db

router = APIRouter(prefix="/api/rooms", tags=["Rooms"])
async def get_or_create_room(sender_id: str, receiver_id: str, roles: dict = None) -> str:
    sender_id = str(sender_id).strip()
    receiver_id = str(receiver_id).strip()
    room_name = f"{min(sender_id, receiver_id)}_{max(sender_id, receiver_id)}"

    room = await rooms_collection.find_one({"name": room_name})

    if room:
        # Update roles and participants if needed
        update_data = {}

        if roles:
            existing_roles = room.get("roles", {})
            merged_roles = {**existing_roles}
            for uid, r in roles.items():
                if r:  # only update if role is non-empty
                    merged_roles[uid] = r
            update_data["roles"] = merged_roles

        # Ensure both participants are saved
        update_data["participants"] = list(
            set(room.get("participants", []) + [sender_id, receiver_id])
        )

        if update_data:
            await rooms_collection.update_one({"_id": room["_id"]}, {"$set": update_data})

        return str(room["_id"])

    # If room doesn't exist, create new
    room_data = {
        "name": room_name,
        "participants": [sender_id, receiver_id],
        "roles": roles or {},
        "created_at": datetime.utcnow(),
        "description": "",
        "created_by": sender_id,
        "is_private": False
    }

    result = await rooms_collection.insert_one(room_data)
    return str(result.inserted_id)


@router.post("/")
async def create_room(data: dict):
    # optional manual room creation endpoint
    return {"message": "use get_or_create_room or implement full route"}

@router.post("/")
async def create_room(data: dict):
    # optional manual room creation endpoint
    return {"message": "use get_or_create_room or implement full route"}
