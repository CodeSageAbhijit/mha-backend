from passlib.context import CryptContext
import cloudinary
import cloudinary.uploader
import os
from dotenv import load_dotenv
from bson import ObjectId
from datetime import date, datetime

# Load environment variables from .env
load_dotenv()

# Password hashing utilities
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    # ✅ FIXED: Truncate password to 72 bytes to comply with bcrypt limitation
    # bcrypt can only hash passwords up to 72 bytes
    if password:
        password = password[:72]
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

# Cloudinary configuration
cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME", "dmwswy7oi"),
    api_key=os.getenv("CLOUDINARY_API_KEY", "438673794476621"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET", "6h2BPvHvCgJzit-9qeFlhi0_KrQ"),
    secure=True
)

# Upload profile photo to Cloudinary
def upload_profile_photo(file):
    try:
        result = cloudinary.uploader.upload(file, folder="profile_photos")
        return result.get("secure_url")
    except Exception as e:
        return None  # Let the route handle error formatting

def serialize_dict(doc) -> dict:
    """Convert MongoDB ObjectId to string and maintain camelCase keys."""
    try:
        return {
            key[0].lower() + key[1:] if key and key[0].isupper() else key:
            str(value) if isinstance(value, ObjectId) else
            value.isoformat() if isinstance(value, (datetime, date)) else
            value
            for key, value in doc.items()
        }
    except Exception as e:
        return {"error": f"Error in serialize_dict: {str(e)}"}

def serialize_list(entities) -> list:
    try:
        return [serialize_dict(doc) for doc in entities]
    except Exception as e:
        return [{"error": f"Error in serialize_list: {str(e)}"}]

# ...existing code...

def serialize_patient(patient):
    if not patient or not isinstance(patient, dict):
        return {"error": "Invalid or missing patient data"}  # <-- prevents NoneType error

    try:
        return {
            "id": str(patient.get("_id", "")),
            "patientId": patient.get("patientId"),
            "firstName": patient.get("firstName"),
            "lastName": patient.get("lastName"),
            "dateOfBirth": (
                patient.get("dateOfBirth").isoformat()
                if patient.get("dateOfBirth") else None
            ),
            "gender": patient.get("gender"),
            # "age": patient.get("age"),
            "country": patient.get("country"),
            "state": patient.get("state"),
            "city": patient.get("city"),
            "postalCode": patient.get("postalCode"),
            "language": patient.get("language"),
            "disease": patient.get("disease"),
            "diagnosis": patient.get("diagnosis"),
            "phoneNumber": patient.get("phoneNumber"),
            "email": patient.get("email"),
            "addressLine": patient.get("addressLine"),
            "maritalStatus": patient.get("maritalStatus"),
            "bloodGroup": patient.get("bloodGroup"),
            "profilePhoto": patient.get("profilePhoto"),
            "createdAt": (
                patient.get("createdAt").isoformat()
                if patient.get("createdAt") and isinstance(patient.get("createdAt"), (datetime, date))
                else patient.get("createdAt")
            ),
            "updatedAt": (
                patient.get("updatedAt").isoformat()
                if patient.get("updatedAt") and isinstance(patient.get("updatedAt"), (datetime, date))
                else patient.get("updatedAt")
            ),
            "createdBy": patient.get("createdBy"),
            "updatedBy": patient.get("updatedBy"),
            "role": patient.get("role"),
        }
    except Exception as e:
        print(f"Error serializing patient: {e}")
        return {"error": str(e)}

# ...existing code...