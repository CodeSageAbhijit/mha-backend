#!/usr/bin/env python3
"""Verify the SQLite migration was successful"""

import os
import sqlite3
from pathlib import Path

db_path = Path("mental_health.db")

print("\n" + "="*60)
print("🔍 MIGRATION VERIFICATION")
print("="*60 + "\n")

# Check if database exists
if db_path.exists():
    size_kb = db_path.stat().st_size / 1024
    print(f"✅ Database file exists: mental_health.db")
    print(f"📊 Database size: {size_kb:.1f} KB\n")
else:
    print("❌ Database file not found!")
    exit(1)

# Connect and verify tables/data
try:
    conn = sqlite3.connect("mental_health.db")
    cursor = conn.cursor()
    
    # Get list of tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [row[0] for row in cursor.fetchall()]
    print(f"📋 Tables created: {len(tables)}")
    for table in sorted(tables):
        cursor.execute(f"SELECT COUNT(*) FROM {table}")
        count = cursor.fetchone()[0]
        print(f"   - {table}: {count} records")
    
    # Key verification queries
    print("\n🔐 Key Data Summary:")
    cursor.execute("SELECT COUNT(*) FROM users")
    users = cursor.fetchone()[0]
    print(f"   - Total Users: {users}")
    
    cursor.execute("SELECT COUNT(*) FROM patients")
    patients = cursor.fetchone()[0]
    print(f"   - Patients: {patients}")
    
    cursor.execute("SELECT COUNT(*) FROM psychiatrists")
    psychiatrists = cursor.fetchone()[0]
    print(f"   - Psychiatrists: {psychiatrists}")
    
    cursor.execute("SELECT COUNT(*) FROM counselors")
    counselors = cursor.fetchone()[0]
    print(f"   - Counselors: {counselors}")
    
    cursor.execute("SELECT COUNT(*) FROM appointments")
    appointments = cursor.fetchone()[0]
    print(f"   - Appointments: {appointments}")
    
    conn.close()
    
    print("\n" + "="*60)
    print("✅ MIGRATION VERIFICATION COMPLETE")
    print("="*60 + "\n")
    
except Exception as e:
    print(f"❌ Error verifying database: {e}")
    exit(1)
