#!/usr/bin/env python3
"""
Verify Patient Password in Database
Checks if the password reset was successful
"""

import asyncio
import sys

# Add parent directory to path
sys.path.insert(0, 'd:/Vs code/mha/mental_health_backend')

from motor.motor_asyncio import AsyncIOMotorClient

# MongoDB connection
MONGO_URI = "mongodb+srv://MentalHealth:Manthan%2312345@cluster0.pnbho29.mongodb.net/?tls=true"
DB_NAME = "mental_health"

async def verify_password():
    """Verify if password is stored in database"""
    
    client = AsyncIOMotorClient(MONGO_URI)
    db = client[DB_NAME]
    
    try:
        print("🔄 Connecting to MongoDB...")
        await client.admin.command('ping')
        print("✅ Connected successfully\n")
        
        patient_email = "rohanchougule090@gmail.com"
        collection = db["patients"]
        
        # Find patient
        patient = await collection.find_one({"email": patient_email})
        
        if not patient:
            print(f"❌ Patient not found: {patient_email}")
            return
        
        print("="*60)
        print("👤 PATIENT DETAILS FROM DATABASE")
        print("="*60)
        print(f"Name: {patient.get('firstName')} {patient.get('lastName')}")
        print(f"Email: {patient.get('email')}")
        print(f"Username: {patient.get('username')}")
        print(f"Patient ID: {patient.get('patientId')}")
        print(f"\n🔐 Password Hash Stored in DB:")
        print(f"{patient.get('password')}")
        print(f"\n✅ Password is STORED in database!")
        print(f"⏰ Last Updated: {patient.get('updatedAt')}")
        print("="*60)
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        client.close()

if __name__ == "__main__":
    asyncio.run(verify_password())
