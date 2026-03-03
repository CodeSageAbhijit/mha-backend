from fastapi import APIRouter, HTTPException
from bson import ObjectId
from bson.errors import InvalidId
from datetime import datetime
from app.database.mongo import counselor_collection, patient_collection, db

router = APIRouter(prefix="/api", tags=["Earnings"])


def error_response(status_code: int, message: str, error: str, errors: list):
    """Standardized error response."""
    raise HTTPException(
        status_code=status_code,
        detail={
            "success": False,
            "status": status_code,
            "message": message,
            "data": None,
            "error": error,
            "errors": errors
        }
    )


@router.get("/counselor/{id}/earnings")
async def get_counselor_earnings(id: str):
    # Validate ObjectId
    try:
        counselor_id = ObjectId(id)
    except InvalidId:
        error_response(400, "Invalid counselor ID format", "ObjectId parsing error", [f"Invalid ID: {id}"])

    # Fetch counselor
    try:
        counselor = await counselor_collection.find_one({"_id": counselor_id})
    except Exception as e:
        error_response(500, "Error fetching counselor", str(e), [])

    if not counselor:
        error_response(404, "Counselor not found", "No record in database", [f"No counselor found with ID '{id}'"])

    counselor_name = counselor.get("fullName", "Unknown")

    # Get patients linked to counselor
    try:
        patients = await patient_collection.find({"counselor_id": counselor_id}).to_list(length=None)
    except Exception as e:
        error_response(500, "Error fetching patients for counselor", str(e), [])

    earnings = []
    for patient in patients:
        admission_id = patient.get("Admission_id")
        patient_name = f"{patient.get('firstName', '')} {patient.get('lastName', '')}".strip()

        # Fetch payments for patient
        try:
            payments = await db.payments.find({"admissionID": admission_id}).to_list(length=None)
        except Exception as e:
            error_response(500, f"Error fetching payments for patient {patient_name}", str(e), [])

        for payment in payments:
            amount = payment.get("amount", 0)
            date = payment.get("date", datetime.utcnow())
            status = payment.get("status", "Pending")

            commission = round(amount * 0.2)
            net_payout = amount - commission

            earnings.append({
                "date": date.date() if isinstance(date, datetime) else date,
                "patient": patient_name,
                "duration": "N/A",  # optional
                "rate": "N/A",      # optional
                "total": f"₹{amount}",
                "commission": f"₹{commission} (20%)",
                "net_payout": f"₹{net_payout}",
                "status": status
            })

    return {
        "success": True,
        "status": 200,
        "message": f"Earnings fetched for counselor {counselor_name}",
        "data": earnings,
        "error": None,
        "errors": []
    }
