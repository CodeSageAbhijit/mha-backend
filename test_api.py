#!/usr/bin/env python3
"""
Backend API Testing Script
Test all key endpoints without pytest
"""

import requests
import json
from typing import Dict, Any

BASE_URL = "http://localhost:8080"
PASS = 0
FAIL = 0
TOKEN = None

def test_endpoint(name: str, endpoint: str, method: str = "GET", data: Dict[str, Any] = None) -> bool:
    """Test an API endpoint"""
    global PASS, FAIL, TOKEN
    
    url = f"{BASE_URL}{endpoint}"
    headers = {
        "Content-Type": "application/json"
    }
    
    if TOKEN:
        headers["Authorization"] = f"Bearer {TOKEN}"
    
    try:
        if method == "GET":
            r = requests.get(url, headers=headers, timeout=5)
        elif method == "POST":
            r = requests.post(url, json=data, headers=headers, timeout=5)
        elif method == "PUT":
            r = requests.put(url, json=data, headers=headers, timeout=5)
        else:
            return False
        
        if r.status_code < 400:
            print(f"  ✓ {name} - Status: {r.status_code}")
            PASS += 1
            return True
        else:
            print(f"  ✗ {name} - Status: {r.status_code}")
            FAIL += 1
            return False
            
    except Exception as e:
        print(f"  ✗ {name} - Error: {str(e)}")
        FAIL += 1
        return False

def main():
    global TOKEN
    
    print("\n" + "="*50)
    print("MENTAL HEALTH - BACKEND API TEST")
    print(f"Target: {BASE_URL}")
    print("="*50)
    
    # ===== AUTHENTICATION =====
    print("\n[AUTHENTICATION]")
    test_endpoint("Register", "/api/register", "POST", {
        "email": f"test{int(__import__('time').time())}@test.com",
        "password": "Test123456!",
        "first_name": "Test",
        "last_name": "User"
    })
    
    result = test_endpoint("Login", "/api/login", "POST", {
        "username": "patient@example.com",
        "password": "patient123",
        "role": "patient"
    })
    
    # ===== USER PROFILE =====
    print("\n[USER PROFILE]")
    test_endpoint("Get Profile", "/api/user/profile", "GET")
    test_endpoint("Update Profile", "/api/user/profile", "POST", {
        "first_name": "Updated"
    })
    
    # ===== THERAPISTS =====
    print("\n[THERAPISTS]")
    test_endpoint("Get Therapists", "/api/psychiatrists", "GET")
    test_endpoint("Get Therapists Paginated", "/api/psychiatrists?page=1&limit=10", "GET")
    test_endpoint("Search Therapists", "/api/psychiatrists/search?specialization=psychology", "GET")
    
    # ===== APPOINTMENTS =====
    print("\n[APPOINTMENTS]")
    test_endpoint("Get Appointments", "/api/appointments", "GET")
    test_endpoint("Book Appointment", "/api/appointments", "POST", {
        "doctor_id": "1",
        "appointment_date": "2025-01-20",
        "appointment_time": "10:00",
        "notes": "Test"
    })
    
    # ===== CHAT =====
    print("\n[CHAT]")
    test_endpoint("Get Chats", "/api/chats", "GET")
    test_endpoint("Create Chat", "/api/chats", "POST", {
        "doctor_id": "1",
        "message": "Hello"
    })
    
    # ===== WALLET =====
    print("\n[WALLET]")
    test_endpoint("Get Wallet", "/api/wallet/balance", "GET")
    test_endpoint("Wallet History", "/api/wallet/transactions", "GET")
    
    # ===== REVIEWS =====
    print("\n[REVIEWS]")
    test_endpoint("Get Reviews", "/api/reviews", "GET")
    test_endpoint("Create Review", "/api/reviews", "POST", {
        "doctor_id": "1",
        "rating": 5,
        "comment": "Great!"
    })
    
    # ===== ADMIN =====
    print("\n[ADMIN]")
    test_endpoint("Admin Dashboard", "/api/admin/dashboard", "GET")
    test_endpoint("Admin Users", "/api/admin/users", "GET")
    
    # ===== RESULTS =====
    print("\n" + "="*50)
    print("TEST RESULTS")
    print("="*50)
    print(f"Passed: {PASS}")
    print(f"Failed: {FAIL}")
    
    total = PASS + FAIL
    if total > 0:
        percent = (PASS / total) * 100
        print(f"Pass Rate: {percent:.1f}%")
    
    if FAIL == 0:
        print("\n✓ ALL TESTS PASSED!")
    else:
        print(f"\n✗ {FAIL} TESTS FAILED")
    
    print("="*50 + "\n")

if __name__ == "__main__":
    main()
