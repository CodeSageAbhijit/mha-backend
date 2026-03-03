from fastapi import APIRouter, HTTPException, status, Depends
from bson import ObjectId
from datetime import datetime
from app.database.mongo import todo_collection
from app.models.todo_schema import TodoCreate, TodoUpdate, TodoResponse
from app.utils.auth_guard import get_current_user

router = APIRouter(prefix="/api/todo", tags=["TODO Management"])


# =====================================================================
# CREATE TODO
# =====================================================================

@router.post("", status_code=201)
async def create_todo(todo_data: TodoCreate, current_user: dict = Depends(get_current_user)):
    """
    Create a new TODO item
    
    Request body:
    {
        "title": "Buy groceries",
        "description": "Buy milk, bread, eggs",
        "priority": "high",
        "status": "todo",
        "due_date": "2026-02-28T10:00:00",
        "user_id": "user_id_here"
    }
    """
    try:
        # Create TODO document
        todo_doc = {
            "title": todo_data.title,
            "description": todo_data.description,
            "priority": todo_data.priority,
            "status": todo_data.status,
            "due_date": todo_data.due_date,
            "assignee_id": todo_data.assignee_id,
            "user_id": todo_data.user_id,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        result = await todo_collection.insert_one(todo_doc)
        
        return {
            "success": True,
            "status": 201,
            "message": "TODO created successfully",
            "data": {
                "id": str(result.inserted_id),
                **todo_doc
            },
            "errors": []
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "success": False,
                "status": 500,
                "message": "Error creating TODO",
                "error": str(e),
                "errors": []
            }
        )


# =====================================================================
# GET ALL TODOs (with filters)
# =====================================================================

@router.get("", status_code=200)
async def get_todos(
    current_user: dict = Depends(get_current_user),
    user_id: str = None,
    status_filter: str = None,
    priority: str = None,
    skip: int = 0,
    limit: int = 50
):
    """
    Get all TODOs with optional filters
    
    Query parameters:
    - user_id: Filter by user
    - status_filter: Filter by status (todo, in_progress, completed, archived)
    - priority: Filter by priority (low, medium, high, urgent)
    - skip: Pagination offset
    - limit: Pagination limit (max 100)
    """
    try:
        # Build filter
        filter_dict = {}
        
        if user_id:
            filter_dict["user_id"] = user_id
        if status_filter:
            filter_dict["status"] = status_filter
        if priority:
            filter_dict["priority"] = priority
        
        # Get total count
        total = await todo_collection.count_documents(filter_dict)
        
        # Get TODOs with pagination
        todos = []
        async for todo in todo_collection.find(filter_dict).skip(skip).limit(limit):
            todo["_id"] = str(todo["_id"])
            todos.append(todo)
        
        return {
            "success": True,
            "status": 200,
            "message": f"Retrieved {len(todos)} TODOs",
            "data": {
                "todos": todos,
                "total": total,
                "skip": skip,
                "limit": limit
            },
            "errors": []
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "success": False,
                "status": 500,
                "message": "Error fetching TODOs",
                "error": str(e),
                "errors": []
            }
        )


# =====================================================================
# GET SINGLE TODO
# =====================================================================

@router.get("/{todo_id}", status_code=200)
async def get_todo(todo_id: str, current_user: dict = Depends(get_current_user)):
    """
    Get a single TODO by ID
    """
    try:
        # Validate ObjectId
        if not ObjectId.is_valid(todo_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "success": False,
                    "status": 400,
                    "message": "Invalid TODO ID",
                    "error": "Invalid ObjectId format",
                    "errors": ["Invalid TODO ID format"]
                }
            )
        
        # Find TODO
        todo = await todo_collection.find_one({"_id": ObjectId(todo_id)})
        
        if not todo:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "success": False,
                    "status": 404,
                    "message": "TODO not found",
                    "error": f"No TODO found with ID: {todo_id}",
                    "errors": ["TODO not found"]
                }
            )
        
        todo["_id"] = str(todo["_id"])
        
        return {
            "success": True,
            "status": 200,
            "message": "TODO retrieved successfully",
            "data": todo,
            "errors": []
        }
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "success": False,
                "status": 500,
                "message": "Error fetching TODO",
                "error": str(e),
                "errors": []
            }
        )


# =====================================================================
# UPDATE TODO
# =====================================================================

@router.put("/{todo_id}", status_code=200)
async def update_todo(todo_id: str, todo_data: TodoUpdate, current_user: dict = Depends(get_current_user)):
    """
    Update a TODO item
    """
    try:
        # Validate ObjectId
        if not ObjectId.is_valid(todo_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "success": False,
                    "status": 400,
                    "message": "Invalid TODO ID",
                    "error": "Invalid ObjectId format",
                    "errors": ["Invalid TODO ID format"]
                }
            )
        
        # Find existing TODO
        existing_todo = await todo_collection.find_one({"_id": ObjectId(todo_id)})
        
        if not existing_todo:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "success": False,
                    "status": 404,
                    "message": "TODO not found",
                    "error": f"No TODO found with ID: {todo_id}",
                    "errors": ["TODO not found"]
                }
            )
        
        # Prepare update data
        update_dict = {k: v for k, v in todo_data.dict().items() if v is not None}
        update_dict["updated_at"] = datetime.utcnow()
        
        # Update TODO
        result = await todo_collection.update_one(
            {"_id": ObjectId(todo_id)},
            {"$set": update_dict}
        )
        
        # Get updated TODO
        updated_todo = await todo_collection.find_one({"_id": ObjectId(todo_id)})
        updated_todo["_id"] = str(updated_todo["_id"])
        
        return {
            "success": True,
            "status": 200,
            "message": "TODO updated successfully",
            "data": updated_todo,
            "errors": []
        }
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "success": False,
                "status": 500,
                "message": "Error updating TODO",
                "error": str(e),
                "errors": []
            }
        )


# =====================================================================
# DELETE TODO
# =====================================================================

@router.delete("/{todo_id}", status_code=200)
async def delete_todo(todo_id: str, current_user: dict = Depends(get_current_user)):
    """
    Delete a TODO item
    """
    try:
        # Validate ObjectId
        if not ObjectId.is_valid(todo_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "success": False,
                    "status": 400,
                    "message": "Invalid TODO ID",
                    "error": "Invalid ObjectId format",
                    "errors": ["Invalid TODO ID format"]
                }
            )
        
        # Delete TODO
        result = await todo_collection.delete_one({"_id": ObjectId(todo_id)})
        
        if result.deleted_count == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "success": False,
                    "status": 404,
                    "message": "TODO not found",
                    "error": f"No TODO found with ID: {todo_id}",
                    "errors": ["TODO not found"]
                }
            )
        
        return {
            "success": True,
            "status": 200,
            "message": "TODO deleted successfully",
            "data": {"id": todo_id},
            "errors": []
        }
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "success": False,
                "status": 500,
                "message": "Error deleting TODO",
                "error": str(e),
                "errors": []
            }
        )


# =====================================================================
# BULK OPERATIONS
# =====================================================================

@router.post("/bulk/update-status", status_code=200)
async def bulk_update_status(
    bulk_data: dict,
    current_user: dict = Depends(get_current_user)
):
    """
    Update status for multiple TODOs at once
    
    Request body:
    {
        "todo_ids": ["id1", "id2", "id3"],
        "new_status": "completed"
    }
    """
    try:
        todo_ids = bulk_data.get("todo_ids", [])
        new_status = bulk_data.get("new_status")
        
        # Validate ObjectIds
        valid_ids = []
        for tid in todo_ids:
            if ObjectId.is_valid(tid):
                valid_ids.append(ObjectId(tid))
        
        if not valid_ids:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "success": False,
                    "status": 400,
                    "message": "No valid TODO IDs provided",
                    "error": "All provided IDs are invalid",
                    "errors": ["Invalid TODO IDs"]
                }
            )
        
        # Bulk update
        result = await todo_collection.update_many(
            {"_id": {"$in": valid_ids}},
            {
                "$set": {
                    "status": new_status,
                    "updated_at": datetime.utcnow()
                }
            }
        )
        
        return {
            "success": True,
            "status": 200,
            "message": f"Updated {result.modified_count} TODOs",
            "data": {
                "modified": result.modified_count,
                "matched": result.matched_count
            },
            "errors": []
        }
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "success": False,
                "status": 500,
                "message": "Error updating TODOs",
                "error": str(e),
                "errors": []
            }
        )


# =====================================================================
# GET TODO STATS
# =====================================================================

@router.get("/stats/summary", status_code=200)
async def get_todo_stats(current_user: dict = Depends(get_current_user), user_id: str = None):
    """
    Get TODO statistics/summary
    """
    try:
        # Build filter
        filter_dict = {}
        if user_id:
            filter_dict["user_id"] = user_id
        
        # Get counts by status
        stats = {
            "total": await todo_collection.count_documents(filter_dict),
            "todo": await todo_collection.count_documents({**filter_dict, "status": "todo"}),
            "in_progress": await todo_collection.count_documents({**filter_dict, "status": "in_progress"}),
            "completed": await todo_collection.count_documents({**filter_dict, "status": "completed"}),
            "archived": await todo_collection.count_documents({**filter_dict, "status": "archived"})
        }
        
        # Get counts by priority
        stats["priority"] = {
            "low": await todo_collection.count_documents({**filter_dict, "priority": "low"}),
            "medium": await todo_collection.count_documents({**filter_dict, "priority": "medium"}),
            "high": await todo_collection.count_documents({**filter_dict, "priority": "high"}),
            "urgent": await todo_collection.count_documents({**filter_dict, "priority": "urgent"})
        }
        
        return {
            "success": True,
            "status": 200,
            "message": "TODO statistics retrieved",
            "data": stats,
            "errors": []
        }
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "success": False,
                "status": 500,
                "message": "Error retrieving statistics",
                "error": str(e),
                "errors": []
            }
        )
