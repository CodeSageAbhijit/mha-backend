from fastapi import APIRouter, Depends
from app.database.mongo import prescription_collection, appointment_collection, psychiatrist_collection
from app.utils.dependencies import get_current_user
from datetime import datetime, timedelta
from app.utils.error_response import error_response  # <-- import your error response

router = APIRouter(prefix="/api/doctor", tags=["Doctor History"])

def calculate_percentage(current: int, previous: int) -> dict:
    if previous == 0:
        if current == 0:
            return {"percentage": 0, "status": "no change"}
        return {"percentage": 100, "status": "increased"}
    change = ((current - previous) / previous) * 100
    return {
        "percentage": round(abs(change), 2),
        "status": "increased" if change > 0 else "decreased"
    }

@router.get("/history/{doctorId}")
async def get_doctor_history(doctorId: str):
    try:
        doctor = await psychiatrist_collection.find_one({"doctorId": doctorId})
        if not doctor:
            return error_response(
                404,
                "Doctor not found",
                "Doctor not found",
                errors=[{
                    "field": "doctorId",
                    "message": "Doctor not found",
                    "type": "not_found"
                }]
            )

        doctor_id = doctor.get("doctorId")
        if not doctor_id:
            return error_response(
                404,
                "doctorId not found in doctor document",
                "doctorId missing",
                errors=[{
                    "field": "doctorId",
                    "message": "doctorId not found in doctor document",
                    "type": "not_found"
                }]
            )

        today = datetime.utcnow()
        start_of_day = datetime.combine(today.date(), datetime.min.time())
        start_of_week = today - timedelta(days=today.weekday())
        start_of_last_week = start_of_week - timedelta(days=7)
        end_of_last_week = start_of_week - timedelta(seconds=1)

        current_week_patients = await prescription_collection.distinct(
            "patientId",
            {
                "updatedBy.userId": doctor_id,
                "updatedBy.role": "psychiatrist",
                "createdAt": {"$gte": start_of_week, "$lte": today}
            }
        )
        last_week_patients = await prescription_collection.distinct(
            "patientId",
            {
                "updatedBy.userId": doctor_id,
                "updatedBy.role": "psychiatrist",
                "createdAt": {"$gte": start_of_last_week, "$lte": end_of_last_week}
            }
        )
        total_current_week_patients = len(current_week_patients)
        total_last_week_patients = len(last_week_patients)
        consult_trend = calculate_percentage(total_current_week_patients, total_last_week_patients)

        current_week_bookings = await appointment_collection.count_documents({
            "doctorId": doctor_id,
            "status": "PENDING",
            "createdAt": {"$gte": start_of_week, "$lte": today}
        })
        last_week_bookings = await appointment_collection.count_documents({
            "doctorId": doctor_id,
            "status": "PENDING",
            "createdAt": {"$gte": start_of_last_week, "$lte": end_of_last_week}
        })
        booking_trend = calculate_percentage(current_week_bookings, last_week_bookings)

        today_new_appointments = await appointment_collection.count_documents({
            "doctorId": doctor_id,
            "createdAt": {"$gte": start_of_day, "$lte": today}
        })
        this_week_new_appointments = await appointment_collection.count_documents({
            "doctorId": doctor_id,
            "createdAt": {"$gte": start_of_week, "$lte": today}
        })
        last_week_new_appointments = await appointment_collection.count_documents({
            "doctorId": doctor_id,
            "createdAt": {"$gte": start_of_last_week, "$lte": end_of_last_week}
        })
        new_appointments_trend = calculate_percentage(this_week_new_appointments, last_week_new_appointments)

        current_week_cancelled = await appointment_collection.count_documents({
            "doctorId": doctor_id,
            "status": "CANCELLED",
            "createdAt": {"$gte": start_of_week, "$lte": today}
        })
        last_week_cancelled = await appointment_collection.count_documents({
            "doctorId": doctor_id,
            "status": "CANCELLED",
            "createdAt": {"$gte": start_of_last_week, "$lte": end_of_last_week}
        })
        cancelled_trend = calculate_percentage(current_week_cancelled, last_week_cancelled)

        history_data = {
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
            "message": "Doctor history fetched successfully",
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
