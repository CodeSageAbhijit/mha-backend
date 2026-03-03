from fastapi import APIRouter, HTTPException, status, Depends
from app.database.mongo import review_collection, patient_collection, psychiatrist_collection, counselor_collection
from app.models.review_schemas import ReviewCreate, ReviewUpdate, ReviewResponse
from app.utils.error_response import error_response
from bson import ObjectId
from datetime import datetime
from typing import List, Optional

from app.utils.auth_guard import get_current_user

router = APIRouter(prefix="/api/reviews", tags=["Reviews"])

def review_doc_to_response(doc: dict) -> dict:
    if not doc:
        return None
    return {
        "id": str(doc.get("_id")),
        "reviewer": doc.get("reviewer"),
        "reviewedId": doc.get("reviewedId"),
        "rating": doc.get("rating"),
        "comment": doc.get("comment", ""),
        "createdAt": doc.get("createdAt")
    }

@router.post("/", status_code=201)
async def create_review(payload: ReviewCreate, current_user: dict = Depends(get_current_user)):
    # only patients can create reviews
    if current_user.get("role") != "user":
        raise HTTPException(status_code=403, detail="Only patients can create reviews.")

    # ensure authenticated patient matches reviewer
    # token_candidate_ids = {
    #     str(current_user.get("patientId")) if current_user.get("role") is not None else None,
    #     str(current_user.get("userId")) if current_user.get("userId") is not None else None,
    #     str(current_user.get("id")) if current_user.get("id") is not None else None,
    #     str(current_user.get("_id")) if current_user.get("_id") is not None else None,
    # }
    # token_candidate_ids.discard(None)
    # if payload.reviewer not in token_candidate_ids:
    #     raise HTTPException(status_code=403, detail="Authenticated patient does not match reviewer in payload.")

    # validate patient exists
    patient = await patient_collection.find_one({"patientId": payload.reviewer})
    if not patient:
        return error_response(404, "Not found", f"Patient {payload.reviewer} not found", [{"field":"reviewer","message":"Patient not found","type":"not_found"}])

    # validate reviewed target: must exist as doctor OR counselor (exactly one)
    # reviewed_id = payload.reviewed
    # found_in_doctor = await psychiatrist_collection.find_one({"doctorId": reviewed_id})
    # found_in_counselor = await counselor_collection.find_one({"counselorId": reviewed_id})

    # if not found_in_doctor and not found_in_counselor:
    #     return error_response(404, "Not found", f"Reviewed id {reviewed_id} not found as doctor or counselor", [{"field":"reviewed","message":"Target not found","type":"not_found"}])
    # if found_in_doctor and found_in_counselor:
    #     return error_response(400, "Validation error", f"Reviewed id {reviewed_id} exists as both doctor and counselor (ambiguous)", [{"field":"reviewed","message":"Ambiguous target id","type":"value_error"}])

    doc = {
        "reviewer": payload.reviewer,
        "reviewedId": payload.reviewed,
        "rating": int(payload.rating),
        "comment": payload.comment or "",
        "createdAt": datetime.utcnow()
    }

    result = await review_collection.insert_one(doc)
    saved = await review_collection.find_one({"_id": result.inserted_id})
    return {
        "status": 201,
        "message": "Review created successfully",
        "data": ReviewResponse(**review_doc_to_response(saved))
    }

@router.get("/list", response_model=dict)
async def list_reviews(
    reviewer: Optional[str] = None,
    reviewedId: Optional[str] = None,
    limit: int = 100,
    skip: int = 0,
    current_user: dict = Depends(get_current_user)
):
    """
    Aggregated review list:
      - If reviewedId provided -> returns reviews for that reviewed id (with patient + doctor/counselor details)
      - Role-aware:
          * patient -> only their own reviews (reviewer)
          * doctor/counselor -> reviews where reviewedId matches their roleUserId/userId
          * admin -> can view all or filter by params
    """
    role = (current_user.get("role") or "").lower()
    me_user_id = current_user.get("userId")
    role_user_id = current_user.get("roleUserId") or None
    # enforce patient can only list their own reviews
    if role == "patient":
        token_patient_id = current_user.get("patientId") or current_user.get("userId") or current_user.get("id") or current_user.get("_id")
        if reviewer and reviewer != token_patient_id:
            raise HTTPException(status_code=403, detail="Patients can only list their own reviews.")
        reviewer = token_patient_id

    # if psychiatrist/counselor and no reviewedId provided, default to their id
    if role in ("psychiatrist", "counselor") and not reviewedId:
        reviewedId = role_user_id or me_user_id

    # build match/query
    match_stage = {}
    if reviewer:
        match_stage["reviewer"] = reviewer
    if reviewedId:
        match_stage["reviewedId"] = reviewedId

    pipeline = []
    if match_stage:
        pipeline.append({"$match": match_stage})
    pipeline.extend([
        {"$sort": {"createdAt": -1}},

        # reviewer patient lookup
        {"$lookup": {
            "from": patient_collection.name,
            "localField": "reviewer",
            "foreignField": "patientId",
            "as": "reviewerPatient"
        }},
        {"$unwind": {"path": "$reviewerPatient", "preserveNullAndEmptyArrays": True}},

        # reviewed -> doctor lookup
        {"$lookup": {
            "from": psychiatrist_collection.name,
            "localField": "reviewedId",
            "foreignField": "doctorId",
            "as": "reviewedDoctor"
        }},
        {"$unwind": {"path": "$reviewedDoctor", "preserveNullAndEmptyArrays": True}},

        # reviewed -> counselor lookup
        {"$lookup": {
            "from": counselor_collection.name,
            "localField": "reviewedId",
            "foreignField": "counselorId",
            "as": "reviewedCounselor"
        }},
        {"$unwind": {"path": "$reviewedCounselor", "preserveNullAndEmptyArrays": True}},

        # consolidate reviewed profile (prefer doctor then counselor)
        {"$addFields": {
            "reviewerProfile": {
                "id": "$reviewer",
                "firstName": "$reviewerPatient.firstName",
                "lastName": "$reviewerPatient.lastName",
                "email": "$reviewerPatient.email",
                "phoneNumber": "$reviewerPatient.phoneNumber",
                "profilePhoto": "$reviewerPatient.profilePhoto"
            },
            "reviewedProfile": {
                "id": "$reviewedId",
                "firstName": {"$ifNull": ["$reviewedDoctor.firstName", "$reviewedCounselor.firstName"]},
                "lastName": {"$ifNull": ["$reviewedDoctor.lastName", "$reviewedCounselor.lastName"]},
                "email": {"$ifNull": ["$reviewedDoctor.email", "$reviewedCounselor.email"]},
                "phoneNumber": {"$ifNull": ["$reviewedDoctor.phoneNumber", "$reviewedCounselor.phoneNumber"]},
                "profilePhoto": {"$ifNull": ["$reviewedDoctor.profilePhoto", "$reviewedCounselor.profilePhoto"]}
            }
        }},

        # final projection
        {"$project": {
            "_id": 1,
            "reviewer": 1,
            "reviewedId": 1,
            "rating": 1,
            "comment": 1,
            "createdAt": 1,
            "reviewerProfile": 1,
            "reviewedProfile": 1
        }}
    ])

    # pagination
    pipeline.append({"$skip": int(skip)})
    pipeline.append({"$limit": int(limit)})

    items = await review_collection.aggregate(pipeline).to_list(length=None)

    # convert _id -> id
    for it in items:
        it["id"] = str(it.pop("_id"))

    # total count for matching query
    total = await review_collection.count_documents(match_stage) if match_stage else await review_collection.count_documents({})

    return {
        "success": True,
        "limit": limit,
        "skip": skip,
        "count": len(items),
        "total": total,
        "data": items
    }

@router.get("/{review_id}")
async def get_review(review_id: str, current_user: dict = Depends(get_current_user)):
    try:
        obj_id = ObjectId(review_id)
    except Exception:
        return error_response(400, "Invalid id", "Invalid review id format", [{"field":"id","message":"Invalid ObjectId","type":"value_error"}])
    review = await review_collection.find_one({"_id": obj_id})
    if not review:
        return error_response(404, "Not found", "Review not found", [{"field":"id","message":"Not found","type":"not_found"}])

    # allow admin or owner patient to fetch
    if current_user.get("role") == "patient":
        token_patient_id = current_user.get("patientId") or current_user.get("userId") or current_user.get("id") or current_user.get("_id")
        if review.get("reviewer") != token_patient_id:
            raise HTTPException(status_code=403, detail="Not authorized to view this review.")

    return {"status":200, "message":"Review fetched", "data": ReviewResponse(**review_doc_to_response(review))}

@router.put("/{review_id}")
async def update_review(review_id: str, payload: ReviewUpdate, current_user: dict = Depends(get_current_user)):
    try:
        obj_id = ObjectId(review_id)
    except Exception:
        return error_response(400, "Invalid id", "Invalid review id format", [{"field":"id","message":"Invalid ObjectId","type":"value_error"}])

    review = await review_collection.find_one({"_id": obj_id})
    if not review:
        return error_response(404, "Not found", "Review not found", [{"field":"id","message":"Review not found","type":"not_found"}])

    # only owner patient or admin can update
    if current_user.get("role") == "patient":
        token_patient_id = current_user.get("patientId") or current_user.get("userId") or current_user.get("id") or current_user.get("_id")
        if review.get("reviewer") != token_patient_id:
            raise HTTPException(status_code=403, detail="Not authorized to update this review.")
    elif current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Not authorized to update this review.")

    update_data = {}
    if payload.rating is not None:
        if not (1 <= payload.rating <= 5):
            return error_response(422, "Validation error", "rating must be between 1 and 5", [{"field":"rating","message":"rating 1-5","type":"value_error"}])
        update_data["rating"] = int(payload.rating)
    if payload.comment is not None:
        update_data["comment"] = payload.comment

    if not update_data:
        return error_response(400, "Validation error", "No update fields provided", [{"field":"payload","message":"Provide rating or comment","type":"value_error"}])

    result = await review_collection.update_one({"_id": obj_id}, {"$set": update_data})
    if result.matched_count == 0:
        return error_response(404, "Not found", "Review not found", [{"field":"id","message":"Review not found","type":"not_found"}])

    updated = await review_collection.find_one({"_id": obj_id})
    return {"status":200, "message":"Review updated", "data": ReviewResponse(**review_doc_to_response(updated))}

@router.delete("/{review_id}")
async def delete_review(review_id: str, current_user: dict = Depends(get_current_user)):
    try:
        obj_id = ObjectId(review_id)
    except Exception:
        return error_response(400, "Invalid id", "Invalid review id format", [{"field":"id","message":"Invalid ObjectId","type":"value_error"}])
    review = await review_collection.find_one({"_id": obj_id})
    if not review:
        return error_response(404, "Not found", "Review not found", [{"field":"id","message":"Review not found","type":"not_found"}])

    # only owner patient or admin can delete
    if current_user.get("role") == "patient":
        token_patient_id = current_user.get("patientId") or current_user.get("userId") or current_user.get("id") or current_user.get("_id")
        if review.get("reviewer") != token_patient_id:
            raise HTTPException(status_code=403, detail="Not authorized to delete this review.")
    elif current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Not authorized to delete this review.")

    result = await review_collection.delete_one({"_id": obj_id})
    if result.deleted_count == 0:
        return error_response(404, "Not found", "Review not found", [{"field":"id","message":"Review not found","type":"not_found"}])
    return {"status":200, "message":"Review deleted successfully", "data": None}
