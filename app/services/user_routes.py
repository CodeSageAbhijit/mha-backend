# app/services/user_routes.py
from fastapi import APIRouter, Query
from app.database.mongo import db

router = APIRouter(prefix="/api", tags=["Users"])

def serialize_user(u: dict, role_hint: str = None):
    """
    Normalize user object before sending to frontend
    """
    u = dict(u)
    user_id = str(u.get("_id"))

    # Build full name
    first_name = u.get("firstName", "").strip()
    last_name = u.get("lastName", "").strip()
    full_name = (first_name + " " + last_name).strip() or u.get("username") or u.get("email")

    # Base structure
    serialized = {
        "id": user_id,
        "_id": user_id,
        "username": u.get("username") or full_name,
        "fullName": full_name,
        "email": u.get("email"),
        "role": u.get("role") or u.get("type") or role_hint or "",
        "profilePhoto": u.get("profilePhoto"),
       
    }

    # Role-specific IDs
    if serialized["role"] in ("user", "patient"):
        serialized["patientId"] = u.get("patientId")
    elif serialized["role"] == "psychiatrist":
        serialized["doctorId"] = u.get("doctorId")
    elif serialized["role"] == "counselor":
        serialized["counselorId"] = u.get("counselorId")

    return serialized

@router.get("/users")
async def list_users(role: str = Query(None, description="Role filter: psychiatrist|counsellor|patient")):
    results = []
    if role is None or role.lower() in ("user", "patient"):
        docs = await db["patients"].find().to_list(1000)
        for d in docs:
            d.setdefault("role", "user")
            results.append(serialize_user(d))
    if role is None or role.lower() in ("psychiatrist",):
        docs = await db["psychiatrists"].find().to_list(1000)
        for d in docs:
            d.setdefault("role", "psychiatrist")
            results.append(serialize_user(d))
    if role is None or role.lower() in ("counsellor", "counselor"):
        docs = await db["counsellors"].find().to_list(1000)
        for d in docs:
            d.setdefault("role", "counsellor")
            results.append(serialize_user(d))
    return results
