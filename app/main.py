from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
import os

# ----------------- Internal Imports -----------------
from app.database.mongo import db  
from app.utils import error_response

# Socket.IO setup
from app.services.chat_routes import socket_app, register_socket_startup

# Routers
from app.services.register_routes import router as register_router
from app.services.login_routes import router as login_router
from app.services.return_response import router as return_response
from app.services.doctor_routes import router as psychiatrist_router
from app.services.assesment_routes import router as assesment_router
from app.services.appointment_routes import router as appointment_router
from app.services.appointment_request_routes import router as appointment_request_router
from app.services.departemt_routes import router as department_router
from app.services.payment_routes import router as payment_router
from app.services.patient_route import router as patient_router
from app.services.counselor_routes import router as counselor_router
from app.services.auth_routes import router as auth_router
from app.services.counselor_earning import router as counselor_earning
from app.services.doctor_earning import router as psychiatrist_earning
from app.services.room_routes import router as room_router
from app.services.prescription_routes import router as prescription_routes
from app.services.medicine_route import router as medicine_routes
from app.services.admin_history_routes import router as adminhistory
from app.services.user_routes import router as user_routes
from app.services.status_route import router as status_routes
from app.services.call_meet_routes import router as call_meet_router
from app.services.googlemeet_routes import router as googlemeet_router
from app.services.reset_password_user import router as reset_password_user
from app.services.doctor_history_routes import router as psychiatrist_history_router
from app.services.counselor_history_routes import router as counselor_history_router
from app.services.address import router as address_router
from app.services.doctor_availability_routes import router as psychiatrist_availability_router
from app.services.counselor_availability_route import router as counselor_availability_router
from app.services.wallet_routes import router as wallet_router
from app.services.video_call_history_routes import router as video_call_history_router
from app.services.google_route import router as google_router
from app.services.reset_password_user import router as change_password_user
from app.services.admin_update_route import router as admin_update_router
from app.services.review_routes import router as review_router
from app.services.consultation_rate_routes import router as consultation_rate_router
from app.services.self_talk_routes import router as self_talk_router  # ✅ NEW: Self-talk AI feature
from app.services.professionals_routes import router as professionals_router  # ✅ NEW: Unified professionals endpoint
from app.services.todo_routes import router as todo_router  # ✅ NEW: TODO management system

#---------------------------------------------------------
from pydantic import ValidationError
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from app.utils import error_response
from starlette.middleware.sessions import SessionMiddleware
import os
#---------------------------------------------------------

# -----------------------
# App setup
# -----------------------
app = FastAPI(title="Mental Health API")

# Mount Socket.IO
app.mount("/socket.io", socket_app)
register_socket_startup(app)

# -----------------------
# Session Middleware
# -----------------------
app.add_middleware(
    SessionMiddleware,
    secret_key=os.getenv("SESSION_SECRET", "fallback-secret")  # change this in production
)

# -----------------------
# CORS Configuration (SECURITY: Whitelist only required origins)
# -----------------------
allowed_origins = [
    "*",  # Allow all origins (for development/testing)
]

# Allow additional origins from environment variable for flexibility
if os.getenv("ALLOWED_ORIGINS"):
    allowed_origins.extend(os.getenv("ALLOWED_ORIGINS", "").split(","))

# ✅ CORS Middleware - Added before other middlewares
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,  # ✅ FIXED: Whitelist only required origins
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],  # ✅ FIXED: Added OPTIONS for preflight
    allow_headers=["Content-Type", "Authorization", "Accept"],  # ✅ FIXED: Added Accept header
    expose_headers=["Content-Type", "Authorization"],
    max_age=3600,  # Cache preflight for 1 hour
)

# ✅ FIXED: Add rate limiting with CORS preflight skip
from app.utils.rate_limiter import limiter
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from app.utils.rate_limiter import rate_limit_error_handler

app.state.limiter = limiter

# Add SlowAPI middleware to handle rate limiting
app.add_middleware(SlowAPIMiddleware)

# -----------------------
# Exception Handlers
# -----------------------
app.add_exception_handler(RateLimitExceeded, rate_limit_error_handler)
app.add_exception_handler(RequestValidationError, error_response.validation_exception_handler)
app.add_exception_handler(ValidationError, error_response.validation_exception_handler)
app.add_exception_handler(StarletteHTTPException, error_response.http_exception_handler)
app.add_exception_handler(Exception, error_response.generic_exception_handler)

# -----------------------
# Startup Event
# -----------------------
@app.on_event("startup")
async def startup_event():
    try:
        collections = await db.list_collection_names()
        print(f"✅ Connected to MongoDB database: '{db.name}'")
        print("   Existing collections:", collections)
    except Exception as e:
        print("❌ Failed to connect to MongoDB:", str(e))

# -----------------------
# Root Route
# -----------------------
@app.get("/")
async def root():
    return {"status": 200, "message": "Welcome to the Mental Health Management API!"}


app.include_router(register_router)
app.include_router(login_router)
app.include_router(return_response)
app.include_router(psychiatrist_router)
app.include_router(assesment_router)
app.include_router(appointment_router)
app.include_router(appointment_request_router)
app.include_router(department_router)
app.include_router(patient_router)
app.include_router(payment_router)
app.include_router(counselor_router)
app.include_router(auth_router)
app.include_router(psychiatrist_earning)
app.include_router(counselor_earning)
app.include_router(room_router)
app.include_router(prescription_routes)
app.include_router(medicine_routes)
app.include_router(adminhistory)
app.include_router(admin_update_router)
app.include_router(user_routes)
app.include_router(status_routes)
app.include_router(call_meet_router)
app.include_router(video_call_history_router)
app.include_router(googlemeet_router)
app.include_router(reset_password_user)
app.include_router(psychiatrist_history_router)
app.include_router(counselor_history_router)
app.include_router(address_router)
app.include_router(psychiatrist_availability_router)
app.include_router(counselor_availability_router)
app.include_router(wallet_router)
app.include_router(google_router)
app.include_router(change_password_user)
app.include_router(self_talk_router)  # ✅ NEW: Self-talk AI endpoint
app.include_router(professionals_router)  # ✅ NEW: Unified professionals endpoint
app.include_router(review_router)
app.include_router(consultation_rate_router)
app.include_router(todo_router)  # ✅ NEW: TODO management system
