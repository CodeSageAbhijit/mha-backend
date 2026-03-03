from fastapi import APIRouter, HTTPException, Depends
from app.database.mongo import patient_collection, psychiatrist_collection, counselor_collection, appointment_collection
from app.utils.dependencies import get_current_user
from datetime import datetime, timedelta

router = APIRouter(prefix="/api/admin", tags=["Admin History"])

def calculate_percentage(current: int, previous: int) -> dict:
    if previous == 0:
        if current == 0:
            return {"percentage": 0, "status": "no change"}
        return {"percentage": None, "status": "new"}  # Or "N/A" for new entries
    change = ((current - previous) / previous) * 100
    status = "increased" if change > 0 else ("decreased" if change < 0 else "no change")
    return {
        "percentage": round(change, 2),
        "status": status
    }

@router.get("/history")
async def get_admin_history(current_user: dict = Depends(get_current_user)):
    try:
        if current_user["role"] != "admin":
            raise HTTPException(status_code=403, detail="Access denied. Only admins can view history")

        today = datetime.utcnow().date()
        yesterday = today - timedelta(days=1)

        today_start = datetime.combine(today, datetime.min.time())
        yesterday_start = datetime.combine(yesterday, datetime.min.time())

        # ---------------- Patients ----------------
        total_patients = await patient_collection.count_documents({})
        previous_total_patients = await patient_collection.count_documents(
            {"createdAt": {"$lt": today_start}}
        )
        patients_trend = calculate_percentage(total_patients, previous_total_patients)

        # ---------- Male and Female Patients (Month-wise) ----------
        current_month_start = datetime(today.year, today.month, 1)
        previous_month_end = current_month_start - timedelta(days=1)
        previous_month_start = datetime(previous_month_end.year, previous_month_end.month, 1)

        # Current month male/female
        current_month_male = await patient_collection.count_documents({
            "createdAt": {"$gte": current_month_start, "$lt": today_start},
            "gender": "male"
        })
        current_month_female = await patient_collection.count_documents({
            "createdAt": {"$gte": current_month_start, "$lt": today_start},
            "gender": "female"
        })

        # Previous month male/female
        prev_month_male = await patient_collection.count_documents({
            "createdAt": {"$gte": previous_month_start, "$lt": previous_month_end},
            "gender": "male"
        })
        prev_month_female = await patient_collection.count_documents({
            "createdAt": {"$gte": previous_month_start, "$lt": previous_month_end},
            "gender": "female"
        })

        male_trend = calculate_percentage(current_month_male, prev_month_male)
        female_trend = calculate_percentage(current_month_female, prev_month_female)

        # ---------------- Doctors ----------------
        total_doctors = await psychiatrist_collection.count_documents({})
        previous_total_doctors = await psychiatrist_collection.count_documents(
            {"createdAt": {"$lt": today_start}}
        )
        doctors_trend = calculate_percentage(total_doctors, previous_total_doctors)

        # ---------------- Counselors ----------------
        total_counselors = await counselor_collection.count_documents({})
        previous_total_counselors = await counselor_collection.count_documents(
            {"createdAt": {"$lt": today_start}}
        )
        counselors_trend = calculate_percentage(total_counselors, previous_total_counselors)

        # ---------------- Appointments ----------------
        total_appointments = await appointment_collection.count_documents({})
        previous_total_appointments = await appointment_collection.count_documents(
            {"createdAt": {"$lt": today_start}}
        )
        appointments_trend = calculate_percentage(total_appointments, previous_total_appointments)

        # ---------------- Appointment Status ----------------
        appointment_status_pipeline = [
            {"$group": {"_id": {"$toUpper": "$status"}, "count": {"$sum": 1}}}
        ]
        status_results = await appointment_collection.aggregate(appointment_status_pipeline).to_list(length=None)

        status_counts = {key: 0 for key in ["COMPLETED", "PENDING", "RESCHEDULED", "CANCELLED", "CONFIRMED"]}
        for r in status_results:
            if r["_id"] in status_counts:
                status_counts[r["_id"]] = r["count"]

        # Final response
        history_data = {
            "patients": {
                "total": total_patients,
                "trend": patients_trend,
                "male": {
                    "total": current_month_male,
                    "trend": male_trend
                },
                "female": {
                    "total": current_month_female,
                    "trend": female_trend
                }
            },
            "doctors": {
                "total": total_doctors,
                "trend": doctors_trend
            },
            "counselors": {
                "total": total_counselors,
                "trend": counselors_trend
            },
            "appointments": {
                "total": total_appointments,
                "trend": appointments_trend,
                "statusCounts": status_counts
            }
        }

        return {
            "success": True,
            "message": "Admin history fetched successfully",
            "data": history_data
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
