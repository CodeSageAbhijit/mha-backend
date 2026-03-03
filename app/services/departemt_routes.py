from fastapi import APIRouter, HTTPException
from bson import ObjectId
from pymongo.errors import PyMongoError
from app.models.department_schemas import DepartmentCreate, DepartmentUpdate, DepartmentResponse
from app.database.mongo import department_collection
from typing import Optional

router = APIRouter(prefix="/api/departments", tags=["Departments"])


# ---------- Utility Functions ----------
def error_response(
    status_code: int,
    message: str,
    error: Optional[str] = None,
    errors: Optional[list] = None
):
    """Standardized error format."""
    raise HTTPException(
        status_code=status_code,
        detail={
            "success": False,
            "status": status_code,
            "message": message,
            "data": None,
            "error": error,
            "errors": errors or []
        }
    )


def to_response(doc: dict) -> dict:
    """Convert MongoDB document to API-friendly format."""
    if not doc:
        return None
    doc["id"] = str(doc["_id"])
    doc.pop("_id", None)
    return doc


# ---------- Create Department ----------
@router.post("/", status_code=201)
async def create_department(payload: DepartmentCreate):
    try:
        # Insert
        result = await department_collection.insert_one(payload.dict())
        new_department = await department_collection.find_one({"_id": result.inserted_id})

        return {
            "success": True,
            "status": 201,
            "message": "Department created successfully",
            "data": to_response(new_department),
            "error": None,
            "errors": []
        }

    except PyMongoError as e:
        error_response(500, "Database error while creating department", str(e))
    except Exception as e:
        error_response(500, "Unexpected error in create_department", str(e))

# ---------- Get All Departments ----------
@router.get("/", status_code=200)
async def get_all_departments():
    try:
        cursor = department_collection.find()
        departments = []
        async for doc in cursor:
            departments.append(to_response(doc))

        return {
            "success": True,
            "status": 200,
            "message": "Departments retrieved successfully",
            "data": departments,
            "error": None,
            "errors": []
        }

    except PyMongoError as e:
        error_response(500, "Database error while retrieving departments", str(e))
    except Exception as e:
        error_response(500, "Unexpected error in get_all_departments", str(e))


# ---------- Get Department by ID ----------
@router.get("/{id}")
async def get_department(id: str):
    try:
        obj_id = ObjectId(id)
    except:
        error_response(400, "Invalid department ID format", "Invalid ObjectId", [f"Invalid ID: {id}"])

    try:
        department = await department_collection.find_one({"_id": obj_id})
        if not department:
            error_response(404, "Department not found", "No record in database", [f"No department found with ID '{id}'"])

        return {
            "success": True,
            "status": 200,
            "message": "Department retrieved successfully",
            "data": to_response(department),
            "error": None,
            "errors": []
        }

    except Exception as e:
        error_response(500, "Unexpected error in get_department", str(e))


# ---------- Update Department ----------
@router.put("/{id}")
async def update_department(id: str, payload: DepartmentUpdate):
    try:
        obj_id = ObjectId(id)
    except:
        error_response(400, "Invalid department ID format", "Invalid ObjectId", [f"Invalid ID: {id}"])

    try:
        result = await department_collection.update_one({"_id": obj_id}, {"$set": payload.dict()})
        if result.matched_count == 0:
            error_response(404, "Department not found", "No record in database", [f"No department found with ID '{id}'"])

        updated_department = await department_collection.find_one({"_id": obj_id})

        return {
            "success": True,
            "status": 200,
            "message": "Department updated successfully",
            "data": to_response(updated_department),
            "error": None,
            "errors": []
        }

    except Exception as e:
        error_response(500, "Unexpected error in update_department", str(e))


# ---------- Delete Department ----------
@router.delete("/{id}")
async def delete_department(id: str):
    try:
        obj_id = ObjectId(id)
    except:
        error_response(400, "Invalid department ID format", "Invalid ObjectId", [f"Invalid ID: {id}"])

    try:
        result = await department_collection.delete_one({"_id": obj_id})
        if result.deleted_count == 0:
            error_response(404, "Department not found", "No record in database", [f"No department found with ID '{id}'"])

        return {
            "success": True,
            "status": 200,
            "message": "Department deleted successfully",
            "data": None,
            "error": None,
            "errors": []
        }

    except Exception as e:
        error_response(500, "Unexpected error in delete_department", str(e))
