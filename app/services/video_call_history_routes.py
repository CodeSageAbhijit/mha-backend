from fastapi import APIRouter, Depends, Query, status
from typing import Optional
from datetime import datetime, timedelta

from app.database.mongo import db, patient_collection, psychiatrist_collection, counselor_collection, admin_collection
from app.utils.dependencies import get_current_user
from app.utils.error_response import error_response

router = APIRouter(prefix="/api/calls", tags=["Calls"])


@router.get("/list", response_model=dict)
async def list_call_history(
    user_id: Optional[str] = Query(None, description="Filter history for this user id (admin only)"),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    status_filter: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(100, ge=1, le=1000),
    current_user: dict = Depends(get_current_user),
):
    """
    Return call history for the current user (or for a specified user if admin).
    Each call entry includes caller and callee details (user / doctor / counselor).
    """
    try:
        calls_collection = db["calls"]

        # Build match stage
        role = (current_user.get("role") or "").lower()
        me_user_id = current_user.get("userId")
        role_user_id = current_user.get("roleUserId") or None

        # Determine the target id to match against callerId/calleeId
        if role == "admin":
            if user_id:
                target_id = user_id
                match_stage = {"$or": [{"callerId": target_id}, {"calleeId": target_id}]}
            else:
                match_stage = {}  # admin sees all
        else:
            # for patients there might be role_user_id mapping; prefer that if present
            if role == "patient" or role == "user":
                pid = role_user_id or me_user_id
                match_stage = {"$or": [{"callerId": pid}, {"calleeId": pid}]}
            else:
                # doctor/counselor -> match where their id appears as caller or callee
                did = role_user_id or me_user_id
                match_stage = {"$or": [{"callerId": did}, {"calleeId": did}]}
                #match_stage = {"$or": [{"callerId": me_user_id}, {"calleeId": me_user_id}]}

        # status filter
        if status_filter:
            match_stage["status"] = status_filter

        # date filters
        try:
            if start_date:
                sd = datetime.strptime(start_date, "%Y-%m-%d") if len(start_date) == 10 else datetime.fromisoformat(start_date.replace("Z", "+00:00"))
                match_stage.setdefault("createdAt", {})
                match_stage["createdAt"]["$gte"] = sd
            if end_date:
                ed = (datetime.strptime(end_date, "%Y-%m-%d") + timedelta(days=1)) if len(end_date) == 10 else datetime.fromisoformat(end_date.replace("Z", "+00:00"))
                match_stage.setdefault("createdAt", {})
                match_stage["createdAt"]["$lt"] = ed
        except Exception:
            return error_response(
                status_code=status.HTTP_400_BAD_REQUEST,
                message="Invalid date format. Use YYYY-MM-DD or ISO 8601",
                error="Date parsing failed"
            )

        pipeline = []

        if match_stage:
            pipeline.append({"$match": match_stage})

        pipeline += [
            {"$sort": {"createdAt": -1}},

            # Caller lookups
            {"$lookup": {
                "from": patient_collection.name,
                "localField": "callerId",
                "foreignField": "patientId",
                "as": "callerPatient"
            }},
            {"$unwind": {"path": "$callerPatient", "preserveNullAndEmptyArrays": True}},
            {"$lookup": {
                "from": psychiatrist_collection.name,
                "localField": "callerId",
                "foreignField": "doctorId",
                "as": "callerDoctor"
            }},
            {"$unwind": {"path": "$callerDoctor", "preserveNullAndEmptyArrays": True}},
            {"$lookup": {
                "from": counselor_collection.name,
                "localField": "callerId",
                "foreignField": "counselorId",
                "as": "callerCounselor"
            }},
            {"$unwind": {"path": "$callerCounselor", "preserveNullAndEmptyArrays": True}},

            # Callee lookups
            {"$lookup": {
                "from": patient_collection.name,
                "localField": "calleeId",
                "foreignField": "patientId",
                "as": "calleePatient"
            }},
            {"$unwind": {"path": "$calleePatient", "preserveNullAndEmptyArrays": True}},
            {"$lookup": {
                "from": psychiatrist_collection.name,
                "localField": "calleeId",
                "foreignField": "doctorId",
                "as": "calleeDoctor"
            }},
            {"$unwind": {"path": "$calleeDoctor", "preserveNullAndEmptyArrays": True}},
            {"$lookup": {
                "from": counselor_collection.name,
                "localField": "calleeId",
                "foreignField": "counselorId",
                "as": "calleeCounselor"
            }},
            {"$unwind": {"path": "$calleeCounselor", "preserveNullAndEmptyArrays": True}},

            # Build consolidated caller & callee public profiles
            {"$addFields": {
                "caller": {
                    "id": "$callerId",
                    "role": "$callerRole",
                    "firstName": {"$ifNull": ["$callerPatient.firstName", "$callerDoctor.firstName", "$callerCounselor.firstName"]},
                    "lastName": {"$ifNull": ["$callerPatient.lastName", "$callerDoctor.lastName", "$callerCounselor.lastName"]},
                    "email": {"$ifNull": ["$callerPatient.email", "$callerDoctor.email", "$callerCounselor.email"]},
                    "phoneNumber": {"$ifNull": ["$callerPatient.phoneNumber", "$callerDoctor.phoneNumber", "$callerCounselor.phoneNumber"]},
                    "profilePhoto": {"$ifNull": ["$callerPatient.profilePhoto", "$callerDoctor.profilePhoto", "$callerCounselor.profilePhoto"]},
                },
                "callee": {
                    "id": "$calleeId",
                    "role": "$calleeRole",
                    "firstName": {"$ifNull": ["$calleePatient.firstName", "$calleeDoctor.firstName", "$calleeCounselor.firstName"]},
                    "lastName": {"$ifNull": ["$calleePatient.lastName", "$calleeDoctor.lastName", "$calleeCounselor.lastName"]},
                    "email": {"$ifNull": ["$calleePatient.email", "$calleeDoctor.email", "$calleeCounselor.email"]},
                    "phoneNumber": {"$ifNull": ["$calleePatient.phoneNumber", "$calleeDoctor.phoneNumber", "$calleeCounselor.phoneNumber"]},
                    "profilePhoto": {"$ifNull": ["$calleePatient.profilePhoto", "$calleeDoctor.profilePhoto", "$calleeCounselor.profilePhoto"]},
                }
            }},

            # Final projection
            {"$project": {
                "_id": 1,
                "sessionId": 1,
                "callType": 1,
                "status": 1,
                "appointmentId": 1,
                "createdAt": 1,
                "updatedAt": 1,
                "durationSec": 1,
                "caller": 1,
                "callee": 1
            }}
        ]

        # Pagination
        skip = (page - 1) * limit
        pipeline.append({"$skip": skip})
        pipeline.append({"$limit": limit})

        items = await calls_collection.aggregate(pipeline).to_list(length=None)

        # convert _id -> id
        for it in items:
            it["id"] = str(it.pop("_id"))

        # total count for matching query
        total = await calls_collection.count_documents(match_stage) if match_stage else await calls_collection.count_documents({})

        return {
            "success": True,
            "page": page,
            "limit": limit,
            "count": len(items),
            "total": total,
            "data": items
        }

    except Exception as e:
        return error_response(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message="Failed to fetch call history",
            error=str(e)
        )
