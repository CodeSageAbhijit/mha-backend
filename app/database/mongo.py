#from pymongo import MongoClient
from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv

load_dotenv()

# ✅ FIXED: Use environment variable for MongoDB URI
MONGO_URI = os.getenv(
    "MONGODB_URI",
    "mongodb+srv://MentalHealth:Manthan%2312345@cluster0.pnbho29.mongodb.net/?tls=true"
)

# Connect to the database
client = AsyncIOMotorClient(MONGO_URI)
db = client["mental_health"]

# Existing collections
counselor_collection = db["counselors"]
psychiatrist_collection = db["psychiatrists"]  # Psychiatrists (can prescribe)
mentor_collection = db["mentors"]  # NEW: Mentors (can heal/support)
business_coach_collection = db["business_coaches"]  # NEW: Business coaches
buddy_collection = db["buddies"]  # NEW: Buddies (support only)
appointment_collection = db["appointments"]
department_collection = db["departments"]
admin_collection = db["admin"]
assessment_collection = db["user_assessments"]
assessment_questions_collection = db["assessments"]
payment_collection = db["payments"]
patient_collection =db["patients"]
refresh_token_collection = db["refresh_tokens"]
counter_collection = db["counters"]
chat_collection = db["chats"]
rooms_collection = db["rooms"]
user_assessments_collection = db["user_assessments"]
prescription_collection = db["prescriptions"]
psychiatrist_availability_collection = db["psychiatrist_availability"]
counselor_availability_collection = db["counselor_availability"]
medicine_collection = db["medicines"]
user_collection = db["users"]
calls_collection = db["calls"]
appointment_request_collection = db["appointment_requests"]
wallet_collection = db["wallet"]
review_collection = db["review"]
psychiatrist_call_rates = db["psychiatrist_call_rates"]
counselor_call_rates = db["counselor_call_rates"]
mentor_call_rates = db["mentor_call_rates"]  # NEW
business_coach_call_rates = db["business_coach_call_rates"]  # NEW
buddy_call_rates = db["buddy_call_rates"]  # NEW
self_talk_collection = db["self_talk"]  # ✅ NEW: Self-talk conversations
professional_privacy_settings = db["professional_privacy_settings"]  # NEW: Hide contact details from users
todo_collection = db["todos"]  # ✅ NEW: TODO management system
otp_collection = db["otps"]  # ✅ NEW: OTP storage for login verification

# Insert sample appointment
# appointment_collection.insert_one({
#     "patientName": "John Doe",
#     "doctorName": "Dr. Asha Sharma",  # or use "counsellorName"
#     "timeSlot": "10:00 AM - 10:30 AM",
#     "date": "2025-08-01",
#     "status": "Pending"
# })



# admin_collection.insert_one({
#     "adminname": "rohan chougule",
#     "username": "rohan99999",
#     "email": "rh99999@gmail.com",
#     "password": "$2b$12$A6lPrZaKknoEqn8JWASODeNnpIYm7XqJYdvp19sqwVlWEnSyaAOKa",  
#     "role": "admin"
# })

# print("Appointments and Admin documents inserted successfully!")n
