from fastapi import APIRouter, HTTPException, status
from app.database.mongo import db
from app.models.payment_schema import PaymentCreate

router = APIRouter(prefix="/api/payments", tags=["Payments"])


# Helper for uniform error handling
def error_response(status_code: int, message: str, error: str, errors: list):
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


# Utility: Convert ObjectId to str and use camelCase
def serialize_doc(doc):
    doc["id"] = str(doc["_id"])
    del doc["_id"]
    return doc


# POST: Create a payment
@router.post("/")
async def create_payment(payment: PaymentCreate):
    try:
        # Check if patient exists for the given admissionId
        patient = await db.patients.find_one({"admissionId": payment.admissionId})
        if not patient:
            error_response(
                status.HTTP_404_NOT_FOUND,
                "Invalid admissionId",
                "Admission ID not found",
                [f"No patient found for admissionId '{payment.admissionId}'"]
            )

        # Insert payment data
        payment_data = payment.dict(by_alias=True)  # camelCase keys from schema
        result = await db.payments.insert_one(payment_data)
        payment_data["id"] = str(result.inserted_id)

        return {
            "success": True,
            "status": status.HTTP_201_CREATED,
            "message": "Payment recorded successfully",
            "data": payment_data,
            "error": None,
            "errors": []
        }

    except HTTPException:
        raise
    except Exception as e:
        error_response(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            "Error creating payment",
            str(e),
            ["Unexpected server error"]
        )


# GET: Retrieve payment(s) by admissionId
@router.get("/{admissionId}")
async def get_payment(admissionId: str):
    try:
        payments_raw = await db.payments.find({"admissionId": admissionId}).to_list(length=100)
        payments = [serialize_doc(p) for p in payments_raw]

        if not payments:
            error_response(
                status.HTTP_404_NOT_FOUND,
                "No payments found",
                "No payment records match the given admissionId",
                [f"No payments found for admissionId '{admissionId}'"]
            )

        return {
            "success": True,
            "status": status.HTTP_200_OK,
            "message": "Payments fetched successfully",
            "data": payments,
            "error": None,
            "errors": []
        }

    except HTTPException:
        raise
    except Exception as e:
        error_response(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            "Error fetching payments",
            str(e),
            ["Unexpected server error"]
        )
