from fastapi import APIRouter, HTTPException, status, Body
from app.models.patient_review_schema import ReviewCreate, ReviewOut
from app.database.mongo import db
from bson import ObjectId
from typing import List

router = APIRouter(prefix="/api/reviews", tags=["Reviews"])

# Helper to convert MongoDB doc to ReviewOut

def review_doc_to_out(doc):
    return ReviewOut(
        id=str(doc["_id"]),
        reviewer_id=doc["reviewer_id"],
        target_id=doc["target_id"],
        role=doc["role"],
        rating=doc["rating"],
        comment=doc.get("comment"),
        date=doc["date"],
    )

@router.post("/add", response_model=ReviewOut)
async def add_review(review: ReviewCreate = Body(...)):
    # Check if reviewer, target_id, and role are present
    if not review.reviewer_id or not review.target_id or not review.role:
        raise HTTPException(status_code=400, detail="Missing required fields.")
    # Insert review
    review_dict = review.dict()
    review_dict["date"] = review.date.isoformat()
    result = await db.reviews.insert_one(review_dict)
    review_dict["_id"] = result.inserted_id
    return review_doc_to_out(review_dict)

@router.get("/psychiatrist/{psychiatrist_id}", response_model=List[ReviewOut])
async def get_psychiatrist_reviews(psychiatrist_id: str):
    reviews = await db.reviews.find({"target_id": psychiatrist_id, "role": "psychiatrist"}).to_list(100)
    return [review_doc_to_out(r) for r in reviews]

@router.get("/counselor/{counselor_id}", response_model=List[ReviewOut])
async def get_counselor_reviews(counselor_id: str):
    reviews = await db.reviews.find({"target_id": counselor_id, "role": "counselor"}).to_list(100)
    return [review_doc_to_out(r) for r in reviews]
