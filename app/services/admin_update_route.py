from fastapi import APIRouter, Form, Depends, UploadFile, File
from app.database.mongo import admin_collection
from app.utils.dependencies import get_admin_user
from app.utils.error_response import error_response
from app.utils.constants import upload_profile_photo
from bson import ObjectId


router = APIRouter(prefix="/api/admin", tags=["Admin Update"])

@router.put("/update-profile")
async def update_admin_profile(
    firstName:str=Form(None),
    lastName:str=Form(None),
    username: str = Form(None),
    dateOfBirth: str = Form(None),
    phoneNumber:str=Form(None),
    age: str=Form(None),
    gender:str=Form(None),
    bloodGroup:str=Form(None),
    maritalStatus:str=Form(None),
    address: str = Form(None),
    email: str = Form(None),

    profilePhoto: UploadFile = File(None),
    current_user: dict = Depends(get_admin_user)
):
    try:
        adminid= current_user.get("userId")
        admin_id=ObjectId(adminid)
        print("adminID",admin_id)
        if not admin_id:
            return error_response(401, "Unauthorized", "Admin not found")

        update_data = {
            "username": username,
            "firstName": firstName,
            "lastName":lastName,
            "gender":gender,
            "age":age,
            "dateOfBirth":dateOfBirth,
            "bloodGroup":bloodGroup,
            "phoneNumber":phoneNumber,
            "maritalStatus":maritalStatus,
            "address":address,
            "email":email
        }

        if profilePhoto:
            try:
                contents = await profilePhoto.read()
                photo_url = upload_profile_photo(contents)
                if photo_url:
                    update_data["profilePhoto"] = photo_url
                else:
                    return error_response(
                        500,
                        "Error uploading profile photo",
                        "Upload returned null/empty",
                        errors=[{
                            "field": "profilePhoto",
                            "message": "Profile photo upload failed",
                            "type": "upload_error"
                        }]
                    )
            except Exception as e:
                return error_response(400, "Profile photo upload failed", str(e))

        result = await admin_collection.update_one(
            {"_id": admin_id},
            {"$set": update_data}
        )
        print("result",result.modified_count)
        if result.modified_count == 0:
            return error_response(404, "Admin not found or no changes made", "UpdateError")
        return {
            "success": True,
            "status": 200,
            "message": "Admin profile updated successfully",
            "data": {"username": username, "profilePhoto": update_data.get("profilePhoto")},
            "error": None,
            "errors": []
        }
    except Exception as e:
        return error_response(500, "Error updating admin profile", str(e))
