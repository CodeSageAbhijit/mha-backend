from fastapi import APIRouter, HTTPException, Depends
from bson import ObjectId
from bson.errors import InvalidId
from datetime import datetime
from app.database.mongo import assessment_collection, user_assessments_collection, assessment_questions_collection
from app.models.assessment_schemas import AssessmentCreate, AssessmentUpdate, UserAssessmentCreate
from app.utils.dependencies import get_current_user

# Try to import LLM service, but continue if it fails
try:
    from app.services.llm_service import analyze_assessment
except Exception:
    try:
        from app.services.llm_services import analyze_assessment
    except Exception as e:
        print(f"⚠️ LLM service disabled: {e}")
        # Provide fallback function
        async def analyze_assessment(data: dict) -> dict:
            return {
                "anxiety": 0.5,
                "depression": 0.5,
                "stress": 0.5,
                "emotional_health": 0.5,
                "summary": "Assessment completed. LLM analysis temporarily unavailable."
            }

from app.utils.error_response import error_response


router = APIRouter(prefix="/api", tags=["Assessment"])


def to_response(doc) -> dict:
    """Convert MongoDB _id to id and return dict."""
    if not doc:
        return None
    doc["id"] = str(doc["_id"])
    del doc["_id"]
    return doc


# ---------- CRUD ----------
@router.post("/assessments", status_code=201)
async def add_assessment(payload: AssessmentCreate, current_user: dict = Depends(get_current_user)):
    """Create new assessment"""
    try:
        payload_dict = payload.dict()
        payload_dict["created_by"] = current_user["userId"]

        result = await assessment_collection.insert_one(payload_dict)
        if not result.inserted_id:
            error_response(500, "Failed to create assessment", "Insert returned no ID")

        new_assessment = await assessment_collection.find_one({"_id": result.inserted_id})
        return {
            "success": True,
            "status": 201,
            "message": "Assessment created successfully",
            "data": to_response(new_assessment),
            "error": None,
            "errors": []
        }
    except Exception as e:
        error_response(500, "Error in add_assessment", str(e))
from typing import List

@router.post("/assessments/bulk", status_code=201)
async def add_multiple_assessments(
    payload: List[AssessmentCreate], 
    current_user: dict = Depends(get_current_user)
):
    """
    Create multiple assessments at once
    """
    try:
        # Prepare assessments for insertion
        assessments_to_insert = []
        for item in payload:
            item_dict = item.dict()
            item_dict["created_by"] = current_user["userId"]
            assessments_to_insert.append(item_dict)

        # Insert all assessments
        result = await assessment_collection.insert_many(assessments_to_insert)
        if not result.inserted_ids:
            raise HTTPException(status_code=500, detail="Failed to create assessments")

        # Fetch the inserted assessments
        new_assessments = await assessment_collection.find(
            {"_id": {"$in": result.inserted_ids}}
        ).to_list(length=len(result.inserted_ids))

        return {
            "success": True,
            "status": 201,
            "message": f"{len(result.inserted_ids)} assessments created successfully",
            "data": [to_response(a) for a in new_assessments],
            "error": None,
            "errors": []
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating assessments: {str(e)}")


@router.get("/assessments/{id}")
async def get_assessment(id: str, current_user: dict = Depends(get_current_user)):
    """Get single assessment"""
    try:
        try:
            obj_id = ObjectId(id)
        except InvalidId:
            error_response(400, "Invalid assessment ID", "ObjectId conversion failed")

        assessment = await assessment_collection.find_one({"_id": obj_id})
        if not assessment:
            error_response(404, "Assessment not found", "No document matches given ID")

        return {
            "success": True,
            "status": 200,
            "message": "Assessment retrieved successfully",
            "data": to_response(assessment),
            "error": None,
            "errors": []
        }
    except HTTPException as e:
        raise e
    except Exception as e:
        error_response(500, "Error in get_assessment", str(e))


@router.get("/assessments", status_code=200)
async def get_all_assessments(current_user: dict = Depends(get_current_user)):
    """Get all assessments"""
    try:
        assessments = []
        async for doc in assessment_collection.find():
            assessments.append(to_response(doc))

        return {
            "success": True,
            "status": 200,
            "message": "All assessments fetched successfully",
            "data": assessments,
            "error": None,
            "errors": []
        }
    except Exception as e:
        error_response(500, "Error in get_all_assessments", str(e))


@router.get("/assessments-questions",status_code=200)
async def get_all_assessment_questions(current_user: dict = Depends(get_current_user)):
    """Get all assessment questions only"""
    try:
        assessments = []
        async for doc in assessment_questions_collection.find({}, {"question": 1, "options": 1,"category":1}):
            assessments.append(to_response(doc))

        return {
            "success": True,
            "status": 200,
            "message": "All assessment questions fetched successfully",
            "data": assessments,
            "error": None,
            "errors": []
        }
    except Exception as e:
        error_response(500, "Error in get_all_assessment_questions", str(e))

        
@router.put("/assessments/{id}")
async def update_assessment(id: str, payload: AssessmentUpdate, current_user: dict = Depends(get_current_user)):
    """Update an existing assessment"""
    try:
        try:
            obj_id = ObjectId(id)
        except InvalidId:
            error_response(400, "Invalid assessment ID", "ObjectId conversion failed")

        update_data = payload.dict(exclude_unset=True)
        result = await assessment_collection.update_one({"_id": obj_id}, {"$set": update_data})

        if result.matched_count == 0:
            error_response(404, "Assessment not found", "No document matches given ID")

        updated_assessment = await assessment_collection.find_one({"_id": obj_id})
        return {
            "success": True,
            "status": 200,
            "message": "Assessment updated successfully",
            "data": to_response(updated_assessment),
            "error": None,
            "errors": []
        }
    except HTTPException as e:
        raise e
    except Exception as e:
        error_response(500, "Error in update_assessment", str(e))


@router.delete("/assessments/{id}")
async def delete_assessment(id: str, current_user: dict = Depends(get_current_user)):
    """Delete an assessment"""
    try:
        try:
            obj_id = ObjectId(id)
        except InvalidId:
            error_response(400, "Invalid assessment ID", "ObjectId conversion failed")

        result = await assessment_collection.delete_one({"_id": obj_id})
        if result.deleted_count == 0:
            error_response(404, "Assessment not found", "No document matches given ID")

        return {
            "success": True,
            "status": 200,
            "message": "Assessment deleted successfully",
            "data": None,
            "error": None,
            "errors": []
        }
    except HTTPException as e:
        raise e
    except Exception as e:
        error_response(500, "Error in delete_assessment", str(e))



@router.post("/user-assessments", status_code=201)
async def save_user_assessment(
    payload: UserAssessmentCreate,
    current_user: dict = Depends(get_current_user)
):
    """
    Save user's filled assessment into the user_assessments collection
    with LLM analysis
    """
    try:
        # Step 1: Build enriched answers by mapping with assessment_collection
        enriched_answers = []
        for ans in payload.answers:
            qid = ObjectId(ans.questionId)
            question_doc = await assessment_collection.find_one({"_id": qid})
            if not question_doc:
                continue  # skip invalid ids

            enriched_answers.append({
                "questionId": str(qid),
                "question": question_doc.get("question"),
                "options": question_doc.get("options", []),
                "selectedAnswer": ans.answer
            })

        # Step 2: Prepare data for LLM
        llm_input = {
            "category": payload.category,
            "answers": enriched_answers
        }

        # Step 3: Call LLM service to analyze responses
        llm_result = await analyze_assessment(llm_input)

        # Step 4: Store in DB
        data = {
            "userId": current_user["userId"],
            "category": payload.category,
            "answers": enriched_answers,
            "analysis": llm_result,   # contains anxiety, depression, stress, etc
            "submitted_at": datetime.utcnow()
        }

        result = await user_assessments_collection.insert_one(data)
        saved = await user_assessments_collection.find_one({"_id": result.inserted_id})

        return {
            "success": True,
            "status": 201,
            "message": "User assessment saved & analyzed successfully",
            "data": {
                "id": str(saved["_id"]),
                "category": saved["category"],
                "analysis": saved["analysis"],
                "submitted_at": saved["submitted_at"]
            },
            "error": None,
            "errors": []
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error in save_user_assessment: {str(e)}")

@router.post("/user-assessments", status_code=201)
async def save_user_assessment(
    payload: UserAssessmentCreate,
    current_user: dict = Depends(get_current_user)
):
    """
    Save user's filled assessment into the user_assessments collection
    with LLM analysis
    """
    try:
        # Step 1: Build enriched answers by mapping with assessment_collection
        enriched_answers = []
        for ans in payload.answers:
            qid = ObjectId(ans.questionId)
            question_doc = await assessment_collection.find_one({"_id": qid})
            if not question_doc:
                continue  # skip invalid ids

            enriched_answers.append({
                "questionId": str(qid),
                "question": question_doc.get("question"),
                "options": question_doc.get("options", []),
                "selectedAnswer": ans.answer
            })

        # Step 2: Prepare data for LLM
        llm_input = {
            "category": payload.category,
            "answers": enriched_answers
        }

        # Step 3: Call LLM service to analyze responses
        llm_result = await analyze_assessment(llm_input)

        # Step 4: Store in DB
        data = {
            "userId": current_user["userId"],
            "category": payload.category,
            "answers": enriched_answers,
            "analysis": llm_result,   # contains anxiety, depression, stress, etc
            "submitted_at": datetime.utcnow()
        }

        result = await user_assessments_collection.insert_one(data)
        saved = await user_assessments_collection.find_one({"_id": result.inserted_id})

        return {
            "success": True,
            "status": 201,
            "message": "User assessment saved & analyzed successfully",
            "data": {
                "id": str(saved["_id"]),
                "category": saved["category"],
                "analysis": saved["analysis"],
                "submitted_at": saved["submitted_at"]
            },
            "error": None,
            "errors": []
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error in save_user_assessment: {str(e)}")
