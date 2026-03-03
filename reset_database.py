#!/usr/bin/env python3
"""
Reset SQLite database - drops all tables and recreates them with new schema
This will rename doctor_availability table to psychiatrist_availability
"""

import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from app.database.database import drop_tables, create_tables, engine

def reset_database():
    """Drop and recreate all database tables"""
    db_path = Path("mental_health.db")
    
    print("🔄 Resetting SQLite database...")
    print(f"📂 Database location: {db_path.absolute()}")
    
    try:
        # Drop all existing tables
        print("\n🗑️  Dropping all existing tables...")
        drop_tables()
        print("✅ Tables dropped successfully")
        
        # Recreate tables with new schema
        print("\n🔨 Creating tables with updated schema...")
        create_tables()
        print("✅ Tables created successfully with new psychiatrist_availability table")
        
        print("\n" + "="*60)
        print("✅ DATABASE RESET COMPLETE!")
        print("="*60)
        print("\nChanges applied:")
        print("  • doctor_availability → psychiatrist_availability")
        print("  • DoctorAvailability → PsychiatristAvailability")
        print("  • All tables recreated with new schema")
        print("\n✨ Your database is now ready with psychiatrist terminology!")
        
    except Exception as e:
        print(f"\n❌ Error resetting database: {e}")
        sys.exit(1)

if __name__ == "__main__":
    reset_database()
