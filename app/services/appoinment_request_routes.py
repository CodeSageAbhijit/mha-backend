from fastapi import APIRouter, Body, Depends
from pydantic import BaseModel, Field
from typing import Optional, Tuple
from datetime import datetime, time, timedelta
from pytz import timezone

from app.utils.auth_guard import require_roles
from app.utils.error_response import error_response
from app.database.mongo import (
    appointment_collection,
    patient_collection,
    psychiatrist_collection,
    psychiatrist_availability_collection,
    appointment_request_collection
)

router = APIRouter(prefix="/api", tags=["Appointment Requests"]) 


# ===== Models =====
class AppointmentRequestCreate(BaseModel):
    patientId: str = Field(...)
    doctorId: str = Field(...)
    reasonForVisit: Optional[str] = None
    consultationMode: Optional[str] = Field("online")

class AppointmentDecision(BaseModel):
    action: str = Field(..., description="ACCEPT or REJECT")
    date: Optional[str] = Field(None, description="YYYY-MM-DD if ACCEPT")
    time: Optional[str] = Field(None, description="HH:MM (24h) if ACCEPT")
    durationMinutes: Optional[int] = Field(None, description="One of 15, 30, 60 if ACCEPT")
    rejectNote: Optional[str] = Field(None, description="Required if REJECT")


# ===== Helpers =====
WEEKDAY_NAMES = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

def _parse_hhmm(s: str) -> time:
    return datetime.strptime(s.strip(), "%H:%M").time()

def _overlaps(start_a: time, end_a: time, start_b: time, end_b: time) -> bool:
    return max(start_a, start_b) < min(end_a, end_b)

def _parse_slot(slot: str):
    try:
        part = slot.replace(" ", "")
        st, en = part.split("-")
        return _parse_hhmm(st), _parse_hhmm(en)
    except Exception:
        return None

async def _doctor_is_available(doctor_id: str, dt: datetime, duration_minutes: Optional[int] = None) -> Tuple[bool, Optional[str], Optional[time]]:
    avail = await psychiatrist_availability_collection.find_one({"doctor_id": doctor_id})
    if not avail:
        return False, "Doctor availability not configured", None

    weekday = WEEKDAY_NAMES[dt.weekday()]
    day_av = next((d for d in avail.get("availability", []) if d.get("day") == weekday), None)
    if not day_av:
        return False, f"Doctor not available on {weekday}", None

    # Use doctor-selected duration if provided; otherwise fallback to configured duration or 30
    consultation_duration = int(duration_minutes or avail.get("consultation_duration") or 30)
    start_t = dt.time()
    end_dt = dt + timedelta(minutes=consultation_duration)
    end_t = end_dt.time()

    for slot in day_av.get("slots", []):
        try:
            s = _parse_hhmm(slot.get("start"))
            e = _parse_hhmm(slot.get("end"))
        except Exception:
            continue
        if s <= start_t and end_dt.time() <= e:
            return True, None, end_dt

    return False, "Doctor is not available this time", None

async def _has_conflict(doctor_id: str, req_start: datetime, req_end: datetime) -> bool:
    start_of_day = datetime(req_start.year, req_start.month, req_start.day)
    end_of_day = start_of_day + timedelta(days=1)

    cursor = appointment_request_collection.find({
        "doctorId": doctor_id,
        "date": {"$gte": start_of_day, "$lt": end_of_day},
        "status": {"$in": ["CONFIRMED", "PENDING"]},  # ignore cancelled if needed
    })
    existing = [doc async for doc in cursor]

    for ap in existing:
        slot = ap.get("timeSlot") or ""
        parsed = _parse_slot(slot)

        if parsed:
            st_time, en_time = parsed
            appt_start = datetime.combine(req_start.date(), st_time)
            appt_end = datetime.combine(req_start.date(), en_time)
        else:
            # fallback: use date field if it’s already a datetime
            if isinstance(ap.get("date"), datetime):
                appt_start = ap["date"]
                appt_end = appt_start + timedelta(minutes=ap.get("durationMinutes", 30))
            else:
                continue

        # check overlap
        if not (req_end <= appt_start or req_start >= appt_end):
            return True

    return False


# ===== Routes =====
@router.get("/psychiatrists/{psychiatrist_id}/availability")
async def get_psychiatrist_availability(
    psychiatrist_id: str,
    date: str,
    dur: int
):
    try:
        # Validate duration
        if dur not in (15, 30, 60):
            return error_response(422, "Invalid duration", "ValidationError", ["Use 15, 30, or 60 minutes"])

        # Parse date
        try:
            day = datetime.strptime(date, "%d/%m/%Y")
        except ValueError:
            return error_response(422, "Invalid date format", "ValidationError", ["Expected date DD/MM/YYYY"])

        # Fetch availability
        avail = await psychiatrist_availability_collection.find_one({"doctor_id": doctor_id})
        if not avail:
            return error_response(404, "Doctor availability not configured", "Not Found", [])

        weekday = WEEKDAY_NAMES[day.weekday()]
        day_av = next((d for d in avail.get("availability", []) if d.get("day") == weekday), None)
        if not day_av:
            return {"doctorId": doctor_id, "date": date, "slots": []}

        # Build candidate slots from availability using given duration
        candidate_slots = []  # list of (start_dt, end_dt)
        for slot in day_av.get("slots", []):
            try:
                s = _parse_hhmm(slot.get("start"))
                e = _parse_hhmm(slot.get("end"))
                if not s or not e or s >= e:
                    continue
            except Exception:
                continue

            # Anchor to the requested day
            start_dt = datetime(day.year, day.month, day.day, s.hour, s.minute)
            end_dt = datetime(day.year, day.month, day.day, e.hour, e.minute)

            # Step through the window in increments of 'dur'
            cur = start_dt
            while True:
                cur_end = cur + timedelta(minutes=dur)
                if cur_end > end_dt:
                    break
                candidate_slots.append((cur, cur_end))
                cur = cur + timedelta(minutes=dur)

        # Filter out slots that conflict with existing appointments
        free_slots = []
        for st_dt, en_dt in candidate_slots:
            ok, msg, true_end_dt = await _doctor_is_available(doctor_id, st_dt, dur)
            if not ok:
                continue
            # Reuse existing conflict checker
            if await _has_conflict(doctor_id, st_dt, true_end_dt):
                continue
            free_slots.append({
                "start": st_dt.strftime("%H:%M"),
                "end": en_dt.strftime("%H:%M"),
                "label": f"{st_dt.strftime('%H:%M')}-{en_dt.strftime('%H:%M')}"
            })

        return {"doctorId": doctor_id, "date": date, "durationMinutes": dur, "slots": free_slots}
    except Exception as e:
        return error_response(500, "Unexpected error", str(e), [])

@router.post("/appointments/request")
async def request_appointment(
    body: AppointmentRequestCreate = Body(...),
    current_user: dict = Depends(require_roles(["user"]))
):
    try:
        if not await patient_collection.find_one({"patientId": body.patientId}):
            return error_response(404, "Patient does not exist.", "Not Found", ["patientId invalid"])
        if not await psychiatrist_collection.find_one({"doctorId": body.doctorId}):
            return error_response(404, "Doctor does not exist.", "Not Found", ["doctorId invalid"])

        
        doc = {
            "appointmentId": f"APPT-{int(datetime.utcnow().timestamp())}",
            "patientId": body.patientId,
            "doctorId": body.doctorId,
            "timeSlot": None,  
            "date": None,      
            "reasonForVisit": body.reasonForVisit,
            "status": "PENDING",
            "consultationMode": (body.consultationMode or "online").lower(),
            "createdAt": datetime.now(timezone("Asia/Kolkata")),
            "updatedAt": datetime.now(timezone("Asia/Kolkata")),
            "createdBy": {"userId": current_user.get("userId"), "role": current_user.get("role")},
            "updatedBy": None,
        }

        res = await appointment_request_collection.insert_one(doc)
        if not res.acknowledged:
            return error_response(500, "Failed to create appointment request", "Database Error", [])

        saved = await appointment_request_collection.find_one({"_id": res.inserted_id})
        saved["_id"] = str(saved["_id"])
        return {"message": "Appointment request created", "appointmentId": saved.get("appointmentId"), "details": saved}
    except Exception as e:
        return error_response(500, "Unexpected error", str(e), [])


@router.post("/appointments/{appointment_id}/decision")
async def decide_appointment(
    appointment_id: str,
    body: AppointmentDecision = Body(...),
    current_user: dict = Depends(require_roles(["psychiatrist"]))
):
    try:
        ap = await appointment_request_collection.find_one({"appointmentId": appointment_id})
        if not ap:
            return error_response(404, "Appointment not found", "Not Found", [])
        if ap.get("doctorId") != current_user.get("roleUserId"):
            return error_response(403, "You can only act on your own appointments", "Forbidden", [])

        action = (body.action or "").strip().upper()
        if action not in ("ACCEPT", "REJECT"):
            return error_response(422, "Invalid action", "ValidationError", ["Use ACCEPT or REJECT"])

        # Validate action-specific payload
        if action == "ACCEPT":
            if not body.date or not body.time:
                return error_response(422, "date and time are required when ACCEPTing", "ValidationError", [])
            try:
                dt = datetime.strptime(f"{body.date} {body.time}", "%Y-%m-%d %H:%M")
            except ValueError:
                return error_response(422, "Invalid date or time format", "ValidationError", ["Expected date YYYY-MM-DD and time HH:MM"])

            # Duration must be 15, 30, or 60
            if body.durationMinutes not in (15, 30, 60):
                return error_response(422, "Invalid duration", "ValidationError", ["Use 15, 30, or 60 minutes"])

            ok, msg, end_t = await _doctor_is_available(ap.get("doctorId"), dt, body.durationMinutes)
            if not ok:
                return error_response(400, msg or "Doctor is not available this time", "AvailabilityError", [])

            if await _has_conflict(ap.get("doctorId"), dt, end_t):
                return error_response(409, "Requested time conflicts with another appointment", "Conflict", [])

            time_slot_str = f"{body.time}-{end_t.strftime('%H:%M')}"

            new_status = "CONFIRMED"
            upd = {
                "status": new_status,
                "date": dt,
                "timeSlot": time_slot_str,
                "start": time_slot_str.split("-")[0],
                "end":time_slot_str.split("-")[1],
                "durationMinutes": body.durationMinutes,
                "updatedAt": datetime.now(timezone("Asia/Kolkata")),
                "updatedBy": {"userId": current_user.get("userId"), "role": current_user.get("role")},
            }
        else:  # REJECT
            if not body.rejectNote or not body.rejectNote.strip():
                return error_response(422, "rejectNote is required when REJECTing", "ValidationError", [])
            new_status = "REJECTED"
            upd = {
                "status": new_status,
                "rejectNote": body.rejectNote.strip(),
                "updatedAt": datetime.now(timezone("Asia/Kolkata")),
                "updatedBy": {"userId": current_user.get("userId"), "role": current_user.get("role")},
            }

        await appointment_request_collection.update_one({"_id": ap["_id"]}, {"$set": upd})
        ap.update(upd)
        ap["_id"] = str(ap["_id"])
        return {"message": f"Appointment {new_status.lower()}", "details": ap}
    except Exception as e:
        return error_response(500, "Unexpected error", str(e), [])
