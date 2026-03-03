from fastapi import APIRouter, Depends
from app.database.mongo import prescription_collection, appointment_collection, counselor_collection
from app.utils.dependencies import get_current_user
from datetime import datetime, timedelta
from app.utils.error_response import error_response
from bson import ObjectId

router = APIRouter(prefix="/api/counselor", tags=["Counselor History"])

def calculate_percentage(current: int, previous: int) -> dict:
    if previous == 0:
        if current == 0:
            return {"percentage": 0, "status": "no change"}
        return {"percentage": 100, "status": "increased"}
    change = ((current - previous) / previous) * 100
    return {"percentage": round(abs(change), 2), "status": "increased" if change > 0 else "decreased"}

@router.get("/history/{counselorId}")
async def get_counselor_history(counselorId: str):
    try:
        counselor = await counselor_collection.find_one({"counselorId": counselorId})
        if not counselor:
            return error_response(
                404,
                "Counselor not found",
                "Counselor not found",
                errors=[{
                    "field": "counselorId",
                    "message": "Counselor not found",
                    "type": "not_found"
                }]
            )
        counselor_id = counselor.get("counselorId")
        if not counselor_id:
            return error_response(
                404,
                "counselorId not found in counselor document",
                "counselorId missing",
                errors=[{
                    "field": "counselorId",
                    "message": "counselorId not found in counselor document",
                    "type": "not_found"
                }]
            )

        today = datetime.utcnow()
        start_of_day = datetime.combine(today.date(), datetime.min.time())
        start_of_week = today - timedelta(days=today.weekday())
        start_of_last_week = start_of_week - timedelta(days=7)
        end_of_last_week = start_of_week - timedelta(seconds=1)

        current_week_patients = await prescription_collection.distinct(
            "userId",
            {
                "prescribedBy.doctorId": counselor_id,
                "prescribedBy.role": "counselor",
                "createdAt": {"$gte": start_of_week, "$lte": today}
            }
        )

        last_week_patients = await prescription_collection.distinct(
            "userId",
            {
                "prescribedBy.doctorId": counselor_id,
                "prescribedBy.role": "counselor",
                "createdAt": {"$gte": start_of_last_week, "$lte": end_of_last_week}
            }
        )

        total_current_week_patients = len(current_week_patients)
        total_last_week_patients = len(last_week_patients)
        consult_trend = calculate_percentage(total_current_week_patients, total_last_week_patients)

        current_week_bookings = await appointment_collection.count_documents({
            "doctorId": counselor_id,
            "status": "PENDING",
            "createdAt": {"$gte": start_of_week, "$lte": today}
        })

        last_week_bookings = await appointment_collection.count_documents({
            "doctorId": counselor_id,
            "status": "PENDING",
            "createdAt": {"$gte": start_of_last_week, "$lte": end_of_last_week}
        })

        booking_trend = calculate_percentage(current_week_bookings, last_week_bookings)

        today_new_appointments = await appointment_collection.count_documents({
            "doctorId": counselor_id,
            "createdAt": {"$gte": start_of_day, "$lte": today}
        })

        this_week_new_appointments = await appointment_collection.count_documents({
            "doctorId": counselor_id,
            "createdAt": {"$gte": start_of_week, "$lte": today}
        })

        last_week_new_appointments = await appointment_collection.count_documents({
            "doctorId": counselor_id,
            "createdAt": {"$gte": start_of_last_week, "$lte": end_of_last_week}
        })

        new_appointments_trend = calculate_percentage(this_week_new_appointments, last_week_new_appointments)

        current_week_cancelled = await appointment_collection.count_documents({
            "doctorId": counselor_id,
            "status": "CANCELLED",
            "createdAt": {"$gte": start_of_week, "$lte": today}
        })

        last_week_cancelled = await appointment_collection.count_documents({
            "doctorId": counselor_id,
            "status": "CANCELLED",
            "createdAt": {"$gte": start_of_last_week, "$lte": end_of_last_week}
        })

        cancelled_trend = calculate_percentage(current_week_cancelled, last_week_cancelled)
        def serialize_doc(doc):
            return {k: str(v) if isinstance(v, ObjectId) else v for k, v in doc.items()}
        history_data = {
            # "counselor": serialize_doc(counselor),
           
            "consultations": {
                "thisWeek": total_current_week_patients,
                "lastWeek": total_last_week_patients,
                "trend": consult_trend
            },
            "bookings": {
                "thisWeek": current_week_bookings,
                "lastWeek": last_week_bookings,
                "trend": booking_trend
            },
            "newAppointments": {
                "today": today_new_appointments,
                "thisWeek": this_week_new_appointments,
                "lastWeek": last_week_new_appointments,
                "trend": new_appointments_trend
            },
            "cancelledAppointments": {
                "thisWeek": current_week_cancelled,
                "lastWeek": last_week_cancelled,
                "trend": cancelled_trend
            }
        }

        return {
            "success": True,
            "message": "Counselor history fetched successfully",
            "data": history_data
        }

    except Exception as e:
        return error_response(
            500,
            "Internal server error",
            str(e),
            errors=[{
                "field": "server",
                "message": str(e),
                "type": "server_error"
            }]
        )
