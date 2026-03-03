from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from app.database.mongo import (
    psychiatrist_collection,
    mentor_collection,
    business_coach_collection,
    buddy_collection,
)
from bson import ObjectId
from datetime import datetime

router = APIRouter(prefix="/api/professionals", tags=["professionals"])

# ====== GET ALL PROFESSIONALS BY ROLE ======
@router.get("/all")
async def get_all_professionals(
    role: Optional[str] = Query(None, description="Filter by role: psychiatrist, mentor, business_coach, buddy"),
    status: Optional[str] = Query(None, description="Filter by status: online, offline, emergency"),
    problem_type: Optional[str] = Query(None, description="Filter by problem type"),
    skip: int = Query(0),
    limit: int = Query(10),
):
    """
    Get all professionals with optional filters by role, status, and problem type.
    """
    try:
        results = {}
        
        # Map role to collection and field names
        role_config = {
            "psychiatrist": {
                "collection": psychiatrist_collection,
                "label": "Psychiatrists (Medical professionals)"
            },
            "mentor": {
                "collection": mentor_collection,
                "label": "Mentors (Personal coaches)"
            },
            "business_coach": {
                "collection": business_coach_collection,
                "label": "Business Coaches"
            },
            "buddy": {
                "collection": buddy_collection,
                "label": "Buddies (Support companions)"
            },
        }
        
        # If specific role requested
        if role:
            if role not in role_config:
                raise HTTPException(status_code=400, detail=f"Invalid role: {role}")
            
            collection = role_config[role]["collection"]
            filter_query = {}
            
            # Add status filter if provided
            if status:
                filter_query["availability"] = status
            
            # Add problem type filter if provided
            if problem_type:
                filter_query["problemTypes"] = {"$in": [problem_type]}
            
            professionals = await collection.find(filter_query).skip(skip).limit(limit).to_list(length=limit)
            
            # Convert ObjectId to string
            for prof in professionals:
                prof["_id"] = str(prof["_id"])
            
            return {
                "success": True,
                "role": role,
                "label": role_config[role]["label"],
                "count": len(professionals),
                "data": professionals
            }
        
        # If no specific role, get all professionals
        all_professionals = []
        
        for role_key, config in role_config.items():
            filter_query = {}
            
            # Add status filter if provided
            if status:
                filter_query["availability"] = status
            
            # Add problem type filter if provided
            if problem_type:
                filter_query["problemTypes"] = {"$in": [problem_type]}
            
            professionals = await config["collection"].find(filter_query).skip(skip).limit(limit).to_list(length=limit)
            
            # Convert ObjectId to string
            for prof in professionals:
                prof["_id"] = str(prof["_id"])
                prof["role"] = role_key  # Add role field
            
            results[role_key] = {
                "label": config["label"],
                "count": len(professionals),
                "data": professionals
            }
        
        return {
            "success": True,
            "message": "All professionals retrieved",
            "professionals": results
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching professionals: {str(e)}")


# ====== GET PROFESSIONALS BY STATUS ======
@router.get("/by-status/{status}")
async def get_professionals_by_status(
    status: str,
    role: Optional[str] = Query(None),
    skip: int = Query(0),
    limit: int = Query(10),
):
    """
    Get professionals filtered by availability status.
    Status: online, offline, emergency
    """
    try:
        valid_statuses = ["online", "offline", "emergency"]
        
        # Map status to availability field value
        status_map = {
            "online": "available",
            "offline": "offline",
            "emergency": "emergency"
        }
        
        if status not in valid_statuses:
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid status. Must be one of: {', '.join(valid_statuses)}"
            )
        
        filter_query = {"availability": status_map[status]}
        results = {}
        
        role_config = {
            "psychiatrist": psychiatrist_collection,
            "mentor": mentor_collection,
            "business_coach": business_coach_collection,
            "buddy": buddy_collection,
        }
        
        if role:
            if role not in role_config:
                raise HTTPException(status_code=400, detail=f"Invalid role: {role}")
            
            collection = role_config[role]
            professionals = await collection.find(filter_query).skip(skip).limit(limit).to_list(length=limit)
            
            for prof in professionals:
                prof["_id"] = str(prof["_id"])
            
            return {
                "success": True,
                "status": status,
                "role": role,
                "count": len(professionals),
                "data": professionals
            }
        
        # Get from all collections
        for role_key, collection in role_config.items():
            professionals = await collection.find(filter_query).skip(skip).limit(limit).to_list(length=limit)
            
            for prof in professionals:
                prof["_id"] = str(prof["_id"])
                prof["role"] = role_key
            
            results[role_key] = professionals
        
        return {
            "success": True,
            "status": status,
            "data": results
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching professionals: {str(e)}")


# ====== GET PROFESSIONALS BY PROBLEM TYPE ======
@router.get("/by-problem/{problem_type}")
async def get_professionals_by_problem(
    problem_type: str,
    role: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    skip: int = Query(0),
    limit: int = Query(10),
):
    """
    Get professionals filtered by problem type they handle.
    Examples: love_problems, marriage_problems, breakup, divorce, business, career
    """
    try:
        filter_query = {"problemTypes": {"$in": [problem_type]}}
        
        # Add status filter if provided
        if status:
            status_map = {
                "online": "available",
                "offline": "offline",
                "emergency": "emergency"
            }
            if status in status_map:
                filter_query["availability"] = status_map[status]
        
        role_config = {
            "psychiatrist": psychiatrist_collection,
            "mentor": mentor_collection,
            "business_coach": business_coach_collection,
            "buddy": buddy_collection,
        }
        
        results = {}
        
        if role:
            if role not in role_config:
                raise HTTPException(status_code=400, detail=f"Invalid role: {role}")
            
            collection = role_config[role]
            professionals = await collection.find(filter_query).skip(skip).limit(limit).to_list(length=limit)
            
            for prof in professionals:
                prof["_id"] = str(prof["_id"])
            
            return {
                "success": True,
                "problem_type": problem_type,
                "role": role,
                "count": len(professionals),
                "data": professionals
            }
        
        # Get from all collections
        for role_key, collection in role_config.items():
            professionals = await collection.find(filter_query).skip(skip).limit(limit).to_list(length=limit)
            
            for prof in professionals:
                prof["_id"] = str(prof["_id"])
                prof["role"] = role_key
            
            results[role_key] = professionals
        
        return {
            "success": True,
            "problem_type": problem_type,
            "data": results
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching professionals: {str(e)}")


# ====== GET PROFESSIONAL STATISTICS ======
@router.get("/stats/summary")
async def get_professionals_stats():
    """
    Get summary statistics of all professionals by role and status.
    """
    try:
        role_config = {
            "psychiatrist": psychiatrist_collection,
            "mentor": mentor_collection,
            "business_coach": business_coach_collection,
            "buddy": buddy_collection,
        }
        
        stats = {}
        
        for role_key, collection in role_config.items():
            total = await collection.count_documents({})
            online = await collection.count_documents({"availability": "available"})
            offline = await collection.count_documents({"availability": "offline"})
            emergency = await collection.count_documents({"availability": "emergency"})
            
            stats[role_key] = {
                "total": total,
                "online": online,
                "offline": offline,
                "emergency": emergency,
                "average_rating": 0  # Can be computed if needed
            }
        
        return {
            "success": True,
            "stats": stats
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching stats: {str(e)}")
