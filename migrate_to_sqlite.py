"""
Migration Script: MongoDB to SQLite
Exports all data from MongoDB and imports to SQLite
"""

import asyncio
import json
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorClient
from sqlalchemy.orm import Session
from app.database.database import SessionLocal, create_tables
from app.models.sqlite_models import *
from app.database.mongo import db as mongo_db
import os
from dotenv import load_dotenv
import uuid

load_dotenv()

MONGO_URI = os.getenv(
    "MONGODB_URI",
    "mongodb+srv://MentalHealth:Manthan%2312345@cluster0.pnbho29.mongodb.net/?tls=true"
)

async def get_mongo_connection():
    """Connect to MongoDB"""
    client = AsyncIOMotorClient(MONGO_URI)
    return client["mental_health"]

def generate_id():
    """Generate unique ID"""
    return str(uuid.uuid4())

async def migrate_users(db_session: Session, mongo_db):
    """Migrate users from MongoDB to SQLite"""
    print("🔄 Migrating Users...")
    
    patients_collection = mongo_db["patients"]
    patients = await patients_collection.find({}).to_list(None)
    
    for patient in patients:
        try:
            user = User(
                id=generate_id(),
                username=patient.get("username"),
                email=patient.get("email"),
                password=patient.get("password"),
                phoneNumber=patient.get("phoneNumber"),
                firstName=patient.get("firstName"),
                lastName=patient.get("lastName"),
                gender=patient.get("gender"),
                role="user",
                termsAccepted=patient.get("termsAccepted", False),
                isActive=patient.get("isActive", True),
                profilePhoto=patient.get("profilePhoto"),
                createdAt=patient.get("createdAt", datetime.utcnow()),
            )
            db_session.add(user)
        except Exception as e:
            print(f"❌ Error migrating user {patient.get('username')}: {e}")
    
    db_session.commit()
    print(f"✅ Migrated {len(patients)} users")
    return patients

async def migrate_patients(db_session: Session, mongo_db, users_map):
    """Migrate patient data"""
    print("🔄 Migrating Patients...")
    
    patients_collection = mongo_db["patients"]
    patients = await patients_collection.find({}).to_list(None)
    
    for patient in patients:
        try:
            user_id = users_map.get(patient.get("username"))
            if not user_id:
                continue
            
            # Convert language list to JSON string for SQLite
            language = patient.get("language", [])
            if isinstance(language, list):
                language = json.dumps(language)
            elif not language:
                language = json.dumps([])
            
            sqlite_patient = Patient(
                id=generate_id(),
                userId=user_id,
                patientId=patient.get("patientId", f"MHA-P{generate_id()[:8]}"),
                dateOfBirth=patient.get("dateOfBirth"),
                age=patient.get("age"),
                addressLine=patient.get("addressLine"),
                maritalStatus=patient.get("maritalStatus"),
                bloodGroup=patient.get("bloodGroup"),
                language=language,
                city=patient.get("city"),
                state=patient.get("state"),
                country=patient.get("country"),
                postalCode=patient.get("postalCode"),
                disease=patient.get("disease"),
                diagnosis=patient.get("diagnosis"),
                isActive=patient.get("isActive", True),
                createdAt=patient.get("createdAt", datetime.utcnow()),
            )
            db_session.add(sqlite_patient)
        except Exception as e:
            print(f"❌ Error migrating patient {patient.get('username')}: {e}")
    
    db_session.commit()
    print(f"✅ Migrated {len(patients)} patient records")

async def migrate_psychiatrists(db_session: Session, mongo_db):
    """Migrate psychiatrist data"""
    print("🔄 Migrating Psychiatrists...")
    
    collection = mongo_db["psychiatrists"]
    records = await collection.find({}).to_list(None)
    
    count = 0
    for record in records:
        try:
            # Check if user already exists (by username or email)
            username = record.get("username")
            email = record.get("email")
            
            existing_user = None
            if username:
                existing_user = db_session.query(User).filter(User.username == username).first()
            if not existing_user and email:
                existing_user = db_session.query(User).filter(User.email == email).first()
            
            if existing_user:
                user = existing_user
            else:
                # Create user first
                user = User(
                    id=generate_id(),
                    username=username or email or f"user_{generate_id()[:6]}",
                    email=email or username,
                    password=record.get("password"),
                    phoneNumber=record.get("phoneNumber"),
                    firstName=record.get("firstName"),
                    lastName=record.get("lastName"),
                    gender=record.get("gender"),
                    role="psychiatrist",
                    isActive=record.get("isActive", True),
                    createdAt=record.get("createdAt", datetime.utcnow()),
                )
                db_session.add(user)
                db_session.flush()
            
            # Convert qualifications list to JSON string for SQLite
            qualifications = record.get("qualifications", [])
            if isinstance(qualifications, list):
                qualifications = json.dumps(qualifications)
            elif not qualifications:
                qualifications = json.dumps([])
            
            psychiatrist = Psychiatrist(
                id=generate_id(),
                userId=user.id,
                doctorId=record.get("doctorId", f"DOC-{generate_id()[:6]}"),
                specialization=str(record.get("specialization", "")),
                licenseNumber=record.get("licenseNumber", ""),
                experience=record.get("experience", 0),
                qualifications=qualifications,
                bio=record.get("bio"),
                consultationFee=record.get("consultationFee", 0),
                isAvailable=record.get("isAvailable", True),
                hospital=record.get("hospital"),
                createdAt=record.get("createdAt", datetime.utcnow()),
            )
            db_session.add(psychiatrist)
            count += 1
        except Exception as e:
            print(f"❌ Error migrating psychiatrist {record.get('username')}: {e}")
    
    db_session.commit()
    print(f"✅ Migrated {count} psychiatrists")

async def migrate_counselors(db_session: Session, mongo_db):
    """Migrate counselor data"""
    print("🔄 Migrating Counselors...")
    
    collection = mongo_db["counselors"]
    records = await collection.find({}).to_list(None)
    
    count = 0
    for record in records:
        try:
            # Check if user already exists (by username or email) 
            username = record.get("username")
            email = record.get("email")
            
            existing_user = None
            if username:
                existing_user = db_session.query(User).filter(User.username == username).first()
            if not existing_user and email:
                existing_user = db_session.query(User).filter(User.email == email).first()
            
            if existing_user:
                user = existing_user
            else:
                user = User(
                    id=generate_id(),
                    username=username or email or f"user_{generate_id()[:6]}",
                    email=email or username,
                    password=record.get("password"),
                    phoneNumber=record.get("phoneNumber"),
                    firstName=record.get("firstName"),
                    lastName=record.get("lastName"),
                    gender=record.get("gender"),
                    role="counselor",
                    isActive=record.get("isActive", True),
                    createdAt=record.get("createdAt", datetime.utcnow()),
                )
                db_session.add(user)
                db_session.flush()
            
            # Convert qualifications list to JSON string for SQLite
            qualifications = record.get("qualifications", [])
            if isinstance(qualifications, list):
                qualifications = json.dumps(qualifications)
            elif not qualifications:
                qualifications = json.dumps([])
            
            counselor = Counselor(
                id=generate_id(),
                userId=user.id,
                counselorId=record.get("counselorId", f"COUN-{generate_id()[:6]}"),
                specialization=str(record.get("specialization", "")),
                licenseNumber=record.get("licenseNumber", ""),
                experience=record.get("experience", 0),
                qualifications=qualifications,
                bio=record.get("bio"),
                consultationFee=record.get("consultationFee", 0),
                isAvailable=record.get("isAvailable", True),
                createdAt=record.get("createdAt", datetime.utcnow()),
            )
            db_session.add(counselor)
            count += 1
        except Exception as e:
            print(f"❌ Error migrating counselor {record.get('username')}: {e}")
    
    db_session.commit()
    print(f"✅ Migrated {count} counselors")

async def migrate_appointments(db_session: Session, mongo_db):
    """Migrate appointments"""
    print("🔄 Migrating Appointments...")
    
    collection = mongo_db["appointments"]
    records = await collection.find({}).to_list(None)
    
    count = 0
    for record in records:
        try:
            appointment = Appointment(
                id=generate_id(),
                appointmentId=record.get("appointmentId", f"APT-{generate_id()[:6]}"),
                patientId=record.get("patientId"),
                doctorId=record.get("doctorId"),
                counselorId=record.get("counselorId"),
                appointmentDate=record.get("appointmentDate"),
                appointmentTime=record.get("appointmentTime", ""),
                duration=record.get("duration", 30),
                reason=record.get("reason", ""),
                status=record.get("status", "pending"),
                notes=record.get("notes"),
                createdAt=record.get("createdAt", datetime.utcnow()),
            )
            db_session.add(appointment)
            count += 1
        except Exception as e:
            print(f"❌ Error migrating appointment: {e}")
    
    db_session.commit()
    print(f"✅ Migrated {count} appointments")

async def migrate_todos(db_session: Session, mongo_db):
    """Migrate TODOs"""
    print("🔄 Migrating TODOs...")
    
    collection = mongo_db["todos"]
    records = await collection.find({}).to_list(None)
    
    count = 0
    for record in records:
        try:
            todo = Todo(
                id=generate_id(),
                todoId=record.get("todoId", f"TODO-{generate_id()[:6]}"),
                userId=record.get("userId"),
                patientId=record.get("patientId"),
                title=record.get("title", ""),
                description=record.get("description"),
                priority=record.get("priority", "medium"),
                status=record.get("status", "todo"),
                dueDate=record.get("dueDate"),
                assigneeId=record.get("assigneeId"),
                createdAt=record.get("createdAt", datetime.utcnow()),
            )
            db_session.add(todo)
            count += 1
        except Exception as e:
            print(f"❌ Error migrating TODO: {e}")
    
    db_session.commit()
    print(f"✅ Migrated {count} TODOs")

async def migrate_otps(db_session: Session, mongo_db):
    """Migrate OTP records"""
    print("🔄 Migrating OTPs...")
    
    collection = mongo_db["otps"]
    records = await collection.find({}).to_list(None)
    
    count = 0
    for record in records:
        try:
            otp = OTP(
                id=generate_id(),
                username=record.get("username", ""),
                role=record.get("role", ""),
                userId=record.get("userId", ""),
                otp=record.get("otp", ""),
                email=record.get("email", ""),
                isUsed=record.get("isUsed", False),
                createdAt=record.get("createdAt", datetime.utcnow()),
                expiresAt=record.get("expiresAt", datetime.utcnow()),
            )
            db_session.add(otp)
            count += 1
        except Exception as e:
            print(f"❌ Error migrating OTP: {e}")
    
    db_session.commit()
    print(f"✅ Migrated {count} OTP records")

async def run_migration():
    """Run complete migration"""
    print("\n" + "="*60)
    print("🔄 STARTING MONGODB TO SQLITE MIGRATION")
    print("="*60 + "\n")
    
    try:
        # Create SQLite tables
        print("📦 Creating SQLite tables...")
        create_tables()
        print("✅ SQLite tables created\n")
        
        # Connect to MongoDB
        print("🔗 Connecting to MongoDB...")
        mongo_db = await get_mongo_connection()
        print("✅ Connected to MongoDB\n")
        
        # Create session
        db_session = SessionLocal()
        
        # Run migrations in order
        await migrate_psychiatrists(db_session, mongo_db)
        await migrate_counselors(db_session, mongo_db)
        
        # Get users map for patient migration
        users = db_session.query(User).all()
        users_map = {u.username: u.id for u in users}
        
        await migrate_users(db_session, mongo_db)
        await migrate_patients(db_session, mongo_db, users_map)
        await migrate_appointments(db_session, mongo_db)
        await migrate_todos(db_session, mongo_db)
        await migrate_otps(db_session, mongo_db)
        
        db_session.close()
        
        print("\n" + "="*60)
        print("✅ MIGRATION COMPLETED SUCCESSFULLY!")
        print("="*60 + "\n")
        print("📌 Next steps:")
        print("   1. Update environment: DATABASE_URL=sqlite:///./mental_health.db")
        print("   2. Remove MongoDB code from services")
        print("   3. Update dependency imports to use SQLAlchemy")
        print("   4. Test all API endpoints")
        print("\n")
        
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(run_migration())
