#!/usr/bin/env python3
"""
Reset Patient Password Script
Sets a patient's password to a known value for testing
"""

import asyncio
import sys
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, 'd:/Vs code/mha/mental_health_backend')

from motor.motor_asyncio import AsyncIOMotorClient
from app.utils.constants import hash_password

# MongoDB connection
MONGO_URI = "mongodb+srv://MentalHealth:Manthan%2312345@cluster0.pnbho29.mongodb.net/?tls=true"
DB_NAME = "mental_health"

async def reset_patient_password():
    """Reset a patient's password to a known value"""
    
    client = AsyncIOMotorClient(MONGO_URI)
    db = client[DB_NAME]
    
    try:
        print("🔄 Connecting to MongoDB...")
        await client.admin.command('ping')
        print("✅ Connected successfully\n")
        
        # Select patient to reset
        patient_email = "rohanchougule090@gmail.com"  # Existing patient
        new_password = "TestPatient@123"
        
        collection = db["patients"]
        
        # Find patient
        patient = await collection.find_one({"email": patient_email})
        
        if not patient:
            print(f"❌ Patient not found: {patient_email}")
            return
        
        print(f"👤 Found Patient: {patient.get('firstName')} {patient.get('lastName')}")
        print(f"   Email: {patient.get('email')}")
        print(f"   Username: {patient.get('username')}")
        print(f"   Patient ID: {patient.get('patientId')}\n")
        
        # Hash new password
        hashed_password = hash_password(new_password)
        
        # Update password
        result = await collection.update_one(
            {"email": patient_email},
            {"$set": {
                "password": hashed_password,
                "updatedAt": datetime.utcnow()
            }}
        )
        
        if result.modified_count > 0:
            print("="*60)
            print("✅ PASSWORD RESET SUCCESSFUL!")
            print("="*60)
            print(f"\n🔐 New Login Credentials:")
            print(f"   Email: {patient_email}")
            print(f"   Username: {patient.get('username')}")
            print(f"   Password: {new_password}")
            print(f"   Role: User/Patient")
            print("\n" + "="*60)
        else:
            print("❌ Failed to update password")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        client.close()

if __name__ == "__main__":
    asyncio.run(reset_patient_password())
