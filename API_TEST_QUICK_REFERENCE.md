# Backend API Testing - Quick Guide

**Test All Backend Endpoints Without pytest**

---

## Quick Start

### Option 1: Using PowerShell (Recommended)
```powershell
cd d:\Vs code\mha\mental_health_backend
.\test_endpoints.bat
```

### Option 2: Using curl Manually
```bash
# Test health
curl http://localhost:8080/health

# Test login
curl -X POST http://localhost:8080/api/login ^
  -H "Content-Type: application/json" ^
  -d "{\"email\":\"test@example.com\",\"password\":\"Test@123\"}"
```

### Option 3: Using PowerShell Directly
```powershell
# Single endpoint test
Invoke-WebRequest -Uri http://localhost:8080/health -Method GET

# With data
$body = @{email="test@example.com";password="Test@123"} | ConvertTo-Json
Invoke-WebRequest -Uri http://localhost:8080/api/login -Method POST -Body $body -ContentType "application/json"
```

---

## Test Endpoints by Section

### 1. AUTHENTICATION (5 tests)

**Register User**
```bash
curl -X POST http://localhost:8080/api/register ^
  -H "Content-Type: application/json" ^
  -d "{\"email\":\"user@test.com\",\"password\":\"Test@123\",\"name\":\"User\",\"role\":\"patient\"}"
```

**Login**
```bash
curl -X POST http://localhost:8080/api/login ^
  -H "Content-Type: application/json" ^
  -d "{\"email\":\"test@example.com\",\"password\":\"Test@123\"}"
```

**Verify OTP**
```bash
curl -X POST http://localhost:8080/api/verify-otp ^
  -H "Content-Type: application/json" ^
  -d "{\"email\":\"test@test.com\",\"otp\":\"123456\"}"
```

**Resend OTP**
```bash
curl -X POST http://localhost:8080/api/resend-otp ^
  -H "Content-Type: application/json" ^
  -d "{\"email\":\"test@test.com\"}"
```

**Forgot Password**
```bash
curl -X POST http://localhost:8080/api/forgot-password ^
  -H "Content-Type: application/json" ^
  -d "{\"email\":\"test@test.com\"}"
```

---

### 2. USER PROFILE (3 tests)

**Get Profile** (requires auth)
```bash
curl -X GET http://localhost:8080/api/user/profile ^
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Update Profile** (requires auth)
```bash
curl -X PUT http://localhost:8080/api/user/profile ^
  -H "Authorization: Bearer YOUR_TOKEN" ^
  -H "Content-Type: application/json" ^
  -d "{\"name\":\"Updated Name\",\"age\":25}"
```

**Upload Picture** (requires auth)
```bash
curl -X POST http://localhost:8080/api/user/profile/picture ^
  -H "Authorization: Bearer YOUR_TOKEN" ^
  -H "Content-Type: application/json" ^
  -d "{\"image_url\":\"https://example.com/image.jpg\"}"
```

---

### 3. THERAPISTS (4 tests)

**Get All Therapists**
```bash
curl http://localhost:8080/api/therapists
```

**Search Therapists**
```bash
curl "http://localhost:8080/api/therapists?specialty=Depression"
```

**Get Therapist Details**
```bash
curl http://localhost:8080/api/therapists/THERAPIST_ID
```

**Register Therapist**
```bash
curl -X POST http://localhost:8080/api/therapist/register ^
  -H "Content-Type: application/json" ^
  -d "{\"email\":\"doc@test.com\",\"password\":\"Test@123\",\"name\":\"Dr. Test\",\"specialty\":\"Depression\",\"experience\":5,\"license_number\":\"LIC123\"}"
```

---

### 4. APPOINTMENTS (4 tests)

**Book Appointment** (requires auth)
```bash
curl -X POST http://localhost:8080/api/appointments ^
  -H "Authorization: Bearer YOUR_TOKEN" ^
  -H "Content-Type: application/json" ^
  -d "{\"therapist_id\":\"1\",\"date\":\"2026-01-15\",\"time\":\"10:00 AM\",\"session_type\":\"video\",\"reason\":\"Anxiety\"}"
```

**Get My Appointments** (requires auth)
```bash
curl http://localhost:8080/api/appointments ^
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Get Appointment Details** (requires auth)
```bash
curl http://localhost:8080/api/appointments/APPOINTMENT_ID ^
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Reschedule Appointment** (requires auth)
```bash
curl -X PUT http://localhost:8080/api/appointments/APPOINTMENT_ID/reschedule ^
  -H "Authorization: Bearer YOUR_TOKEN" ^
  -H "Content-Type: application/json" ^
  -d "{\"new_date\":\"2026-01-20\",\"new_time\":\"02:00 PM\"}"
```

---

### 5. CHAT & MESSAGING (4 tests)

**Get Chats** (requires auth)
```bash
curl http://localhost:8080/api/chats ^
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Create Chat** (requires auth)
```bash
curl -X POST http://localhost:8080/api/chats ^
  -H "Authorization: Bearer YOUR_TOKEN" ^
  -H "Content-Type: application/json" ^
  -d "{\"recipient_id\":\"THERAPIST_ID\",\"message_type\":\"text\"}"
```

**Send Message** (requires auth)
```bash
curl -X POST http://localhost:8080/api/chats/CHAT_ID/messages ^
  -H "Authorization: Bearer YOUR_TOKEN" ^
  -H "Content-Type: application/json" ^
  -d "{\"message\":\"Hello!\",\"message_type\":\"text\"}"
```

**Get Messages** (requires auth)
```bash
curl http://localhost:8080/api/chats/CHAT_ID/messages ^
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

### 6. PAYMENTS (4 tests)

**Get Wallet** (requires auth)
```bash
curl http://localhost:8080/api/wallet ^
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Add Funds to Wallet** (requires auth)
```bash
curl -X POST http://localhost:8080/api/wallet/add ^
  -H "Authorization: Bearer YOUR_TOKEN" ^
  -H "Content-Type: application/json" ^
  -d "{\"amount\":1000,\"payment_method\":\"upi\"}"
```

**Create Payment** (requires auth)
```bash
curl -X POST http://localhost:8080/api/payments/create ^
  -H "Authorization: Bearer YOUR_TOKEN" ^
  -H "Content-Type: application/json" ^
  -d "{\"amount\":500,\"currency\":\"INR\",\"payment_method\":\"card\"}"
```

**Payment History** (requires auth)
```bash
curl http://localhost:8080/api/payments/history ^
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

### 7. REVIEWS (2 tests)

**Submit Review** (requires auth)
```bash
curl -X POST http://localhost:8080/api/reviews ^
  -H "Authorization: Bearer YOUR_TOKEN" ^
  -H "Content-Type: application/json" ^
  -d "{\"therapist_id\":\"THERAPIST_ID\",\"rating\":5,\"comment\":\"Great!\"}"
```

**Get Reviews**
```bash
curl http://localhost:8080/api/reviews/therapist/THERAPIST_ID
```

---

### 8. ADMIN (3 tests)

**Get All Users** (requires auth, admin)
```bash
curl http://localhost:8080/api/admin/users ^
  -H "Authorization: Bearer ADMIN_TOKEN"
```

**Dashboard Stats** (requires auth, admin)
```bash
curl http://localhost:8080/api/admin/dashboard/stats ^
  -H "Authorization: Bearer ADMIN_TOKEN"
```

**Get Transactions** (requires auth, admin)
```bash
curl http://localhost:8080/api/admin/transactions ^
  -H "Authorization: Bearer ADMIN_TOKEN"
```

---

### 9. AI & RECOMMENDATIONS (2 tests)

**Get Recommendations** (requires auth)
```bash
curl http://localhost:8080/api/recommendations ^
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Submit Mood Check-in** (requires auth)
```bash
curl -X POST http://localhost:8080/api/mood-checkin ^
  -H "Authorization: Bearer YOUR_TOKEN" ^
  -H "Content-Type: application/json" ^
  -d "{\"mood\":\"happy\",\"intensity\":8}"
```

---

### 10. CRISIS SUPPORT (1 test)

**Report Crisis** (requires auth)
```bash
curl -X POST http://localhost:8080/api/crisis-report ^
  -H "Authorization: Bearer YOUR_TOKEN" ^
  -H "Content-Type: application/json" ^
  -d "{\"description\":\"Need help\",\"urgency\":\"high\"}"
```

---

## Getting Auth Token

1. **Register or Login First**
```bash
curl -X POST http://localhost:8080/api/login ^
  -H "Content-Type: application/json" ^
  -d "{\"email\":\"test@example.com\",\"password\":\"Test@123\"}" > response.json
```

2. **Extract Token** (PowerShell)
```powershell
$response = Get-Content response.json | ConvertFrom-Json
$token = $response.access_token
Write-Host $token
```

3. **Use Token in Requests**
```bash
curl http://localhost:8080/api/user/profile ^
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

---

## Response Codes

| Code | Meaning |
|------|---------|
| 200 | Success |
| 201 | Created |
| 400 | Bad Request |
| 401 | Unauthorized (missing auth) |
| 403 | Forbidden (no permission) |
| 404 | Not Found |
| 500 | Server Error |

---

## Check Server Status

**Health Check**
```bash
curl http://localhost:8080/health
```

Expected response:
```json
{"status":"running","version":"1.0"}
```

---

## Files Included

1. **test_endpoints.bat** - Batch script for Windows (easy to run)
2. **test_endpoints.ps1** - PowerShell script (more features)
3. **test_all_endpoints.ps1** - Comprehensive PowerShell script (42 tests)
4. **TEST_GUIDE.md** - Detailed testing guide

---

## Running Full Test Suite

```bash
# Batch (Windows)
cd d:\Vs code\mha\mental_health_backend
test_endpoints.bat

# PowerShell
powershell -ExecutionPolicy Bypass -File .\test_all_endpoints.ps1

# Or run test_endpoints.ps1 for simpler output
powershell -ExecutionPolicy Bypass -File .\test_endpoints.ps1
```

---

## Expected Results

If backend is working correctly, you should see:

```
[CHECK] Testing server connection...
OK - Server is running

[TEST 1] User Registration
  POST http://localhost:8080/api/register
  Status: 201

[TEST 2] User Login
  POST http://localhost:8080/api/login
  Status: 200

...

================================================
TEST SUMMARY
================================================

Total Tests: 30
Passed: 30
Failed: 0
Pass Rate: 100%

SUCCESS - All tests passed!
```

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Connection refused | Start backend: `python run.py` |
| 400 Bad Request | Check JSON format in -d flag |
| 401 Unauthorized | Get and include auth token |
| 404 Not Found | Check endpoint URL spelling |
| Database error | Verify PostgreSQL is running |
| CORS error | Check CORS configuration in backend |

---

## Next Steps After Testing

1. ✅ All endpoints return correct status codes
2. ✅ Response data is valid
3. ✅ Error handling works
4. ✅ Authentication required endpoints return 401 without token
5. Ready for: Load testing, security testing, production deployment

---

**Scripts Location:** `d:\Vs code\mha\mental_health_backend\`  
**Last Updated:** January 7, 2026
