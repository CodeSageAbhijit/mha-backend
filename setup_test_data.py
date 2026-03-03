#!/usr/bin/env python3
"""
Test Data Setup Script for Mental Health Application
Creates test users for all roles to enable comprehensive testing
"""

import asyncio
import sys
from datetime import datetime
from bson import ObjectId

# Add parent directory to path
sys.path.insert(0, '/d/Vs code/mha/mental_health_backend')

from motor.motor_asyncio import AsyncIOMotorClient
from app.utils.constants import hash_password

# MongoDB connection
MONGO_URI = "mongodb+srv://auroajnish05:Vnk6Rv8jlmvEJFH@cluster0.z5mvy0j.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
DB_NAME = "mental_health"

async def setup_test_data():
    """Create test user accounts for testing"""
    
    client = AsyncIOMotorClient(MONGO_URI)
    db = client[DB_NAME]
    
    try:
        print("🔄 Connecting to MongoDB...")
        await client.admin.command('ping')
        print("✅ Connected successfully")
        
        # Test users data
        test_users = {
            "psychiatrist": {
                "username": "psychiatrist",
                "email": "psychiatrist@mentalhealth.app",
                "password": "Psychiatrist@123456",  # Will be hashed
                "phoneNumber": "9876543210",
                "role": "psychiatrist",
                "fullName": "Dr. Test Psychiatrist",
                "gender": "male",
                "qualification": "MBBS",
                "specialization": "General",
                "experienceYears": 5,
                "licenseNumber": "PSY123456",
                "shortBio": "Test psychiatrist account",
                "isVerified": True,
                "createdAt": datetime.utcnow(),
            },
            "patient": {
                "username": "patient1",
                "email": "patient1@mentalhealth.app",
                "password": "Patient@123456",  # Will be hashed
                "phoneNumber": "8765432109",
                "role": "user",
                "fullName": "Test Patient",
                "gender": "female",
                "dateOfBirth": "1995-01-15",
                "isVerified": True,
                "createdAt": datetime.utcnow(),
            },
            "counselor": {
                "username": "counselor",
                "email": "counselor@mentalhealth.app",
                "password": "Counselor@123456",  # Will be hashed
                "phoneNumber": "7654321098",
                "role": "counselor",
                "fullName": "Test Counselor",
                "gender": "male",
                "qualification": "M.Sc Psychology",
                "specialization": "Mental Health Counseling",
                "experienceYears": 3,
                "licenseNumber": "COUN123456",
                "shortBio": "Test counselor account",
                "isVerified": True,
                "createdAt": datetime.utcnow(),
            },
            "admin": {
                "username": "admin",
                "email": "admin@mentalhealth.app",
                "password": "Admin@123456",  # Will be hashed
                "phoneNumber": "6543210987",
                "role": "admin",
                "fullName": "Test Admin",
                "gender": "male",
                "isVerified": True,
                "createdAt": datetime.utcnow(),
            },
        }
        
        # Collection mappings
        collections = {
            "doctor": "psychiatrists",
            "patient": "patients",
            "counselor": "counselors",
            "admin": "admins",
        }
        
        # Insert test users
        for key, user_data in test_users.items():
            collection_name = collections[key]
            collection = db[collection_name]
            
            # Hash password
            user_data["password"] = hash_password(user_data["password"])
            
            # Check if user exists
            existing = await collection.find_one({"email": user_data["email"]})
            
            if existing:
                print(f"⚠️  {key.upper()} already exists: {user_data['email']}")
                # Update the password hash just to be sure
                await collection.update_one(
                    {"email": user_data["email"]},
                    {"$set": {"password": user_data["password"]}}
                )
                print(f"✅ Updated {key.upper()} password hash")
            else:
                result = await collection.insert_one(user_data)
                print(f"✅ Created {key.upper()}: {user_data['email']} (ID: {result.inserted_id})")
        
        print("\n" + "="*60)
        print("📋 TEST CREDENTIALS READY")
        print("="*60)
        print("\n🔐 Login Credentials:")
        print(f"\n👨‍⚕️  PSYCHIATRIST:")
        print(f"   Email: psychiatrist@mentalhealth.app")
        print(f"   Password: Psychiatrist@123456")
        print(f"   Role: Psychiatrist")
        
        print(f"\n👤 PATIENT:")
        print(f"   Email: patient1@mentalhealth.app")
        print(f"   Password: Patient@123456")
        print(f"   Role: User")
        
        print(f"\n💼 COUNSELOR:")
        print(f"   Email: counselor@mentalhealth.app")
        print(f"   Password: Counselor@123456")
        print(f"   Role: Counselor")
        
        print(f"\n⚙️  ADMIN:")
        print(f"   Email: admin@mentalhealth.app")
        print(f"   Password: Admin@123456")
        print(f"   Role: Admin")
        
        print("\n" + "="*60)
        
    except Exception as e:
        print(f"❌ Error: {e}")
        raise
    finally:
        client.close()
        print("\n✅ Connection closed")

if __name__ == "__main__":
    print("🚀 Starting test data setup...")
    asyncio.run(setup_test_data())
