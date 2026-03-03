from fastapi import APIRouter, HTTPException
from bson import ObjectId
from datetime import datetime
from app.database.mongo import psychiatrist_collection, patient_collection, db

router = APIRouter(prefix="/api", tags=["Earnings"])


def error_response(status_code: int, message: str, error: str, errors: list):
    """Standardized error format."""
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


@router.get("/doctor/{id}/earnings")
async def get_doctor_earnings(id: str):
    # Validate doctor ID
    try:
        doctor_id = ObjectId(id)
    except:
        error_response(400, "Invalid doctor ID", "ObjectId parsing error", [f"Provided ID '{id}' is not a valid ObjectId"])

    # Fetch doctor
    doctor = await psychiatrist_collection.find_one({"_id": doctor_id})
    if not doctor:
        error_response(404, "Doctor not found", "No record in database", [f"No doctor found with ID '{id}'"])

    doctor_name = doctor.get("fullName", "Unknown")
    rate = doctor.get("ratePerMinute", 10)

    # Get all patients linked to this doctor
    patients = await patient_collection.find({"doctorId": doctor_id}).to_list(length=None)

    earnings = []
    for patient in patients:
        admission_id = patient.get("admissionId")
        patient_name = f"{patient.get('firstName', '')} {patient.get('lastName', '')}".strip()

        # Find payments for each patient by Admission ID
        payments = await db.payments.find({"admissionId": admission_id}).to_list(length=None)

        for payment in payments:
            amount = payment.get("amount", 0)
            payment_date = payment.get("date", datetime.utcnow())
            status = payment.get("status", "Pending")

            commission = round(amount * 0.2)
            net_payout = amount - commission

            earnings.append({
                "date": payment_date.date().isoformat() if isinstance(payment_date, datetime) else payment_date,
                "patient": patient_name,
                "duration": "N/A",  # Placeholder until session tracking is implemented
                "rate": f"N/A",     # Placeholder unless stored in session
                "total": f"₹{amount}",
                "commission": f"₹{commission} (20%)",
                "netPayout": f"₹{net_payout}",
                "status": status
            })

    return {
        "success": True,
        "status": 200,
        "message": f"Earnings fetched for doctor {doctor_name}",
        "data": earnings,
        "error": None,
        "errors": []
    }
