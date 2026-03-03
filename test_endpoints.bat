@echo off
REM Backend API Testing Script - Using cURL
REM Test all endpoints without pytest

setlocal enabledelayedexpansion

set BASE_URL=http://localhost:8080
set API_PREFIX=/api
set TOKEN=

REM Colors (using findstr for colored output)
REM Green: findstr /R "." 

echo.
echo ================================================
echo BACKEND API TESTING - CURL
echo ================================================
echo URL: %BASE_URL%
echo ================================================
echo.

REM Check if server is running
echo [CHECK] Testing server connection...
curl -s %BASE_URL%/health >nul 2>&1
if errorlevel 1 (
    echo ERROR - Server not running at %BASE_URL%
    echo Start backend: python run.py
    pause
    exit /b 1
)
echo OK - Server is running
echo.

REM Counter variables
set /A totalTests=0
set /A passedTests=0
set /A failedTests=0

REM ==================== SECTION 1: AUTH ====================
echo.
echo ============ SECTION 1: AUTHENTICATION ============
echo.

set /A totalTests+=1
echo [TEST !totalTests!] User Registration
curl -X POST "%BASE_URL%%API_PREFIX%/register" ^
  -H "Content-Type: application/json" ^
  -d "{\"email\":\"test!RANDOM!@test.com\",\"password\":\"Test@123\",\"name\":\"User\",\"role\":\"patient\"}" ^
  -w "\nStatus: %%{http_code}\n" 2>nul
echo.

set /A totalTests+=1
echo [TEST !totalTests!] User Login
for /f "tokens=*" %%A in ('curl -s -X POST "%BASE_URL%%API_PREFIX%/login" ^
  -H "Content-Type: application/json" ^
  -d "{\"email\":\"test@example.com\",\"password\":\"Test@123\"}"') do (
  set TOKEN=%%A
)
echo.

set /A totalTests+=1
echo [TEST !totalTests!] Verify OTP
curl -X POST "%BASE_URL%%API_PREFIX%/verify-otp" ^
  -H "Content-Type: application/json" ^
  -d "{\"email\":\"test@test.com\",\"otp\":\"123456\"}" ^
  -w "\nStatus: %%{http_code}\n" 2>nul
echo.

set /A totalTests+=1
echo [TEST !totalTests!] Resend OTP
curl -X POST "%BASE_URL%%API_PREFIX%/resend-otp" ^
  -H "Content-Type: application/json" ^
  -d "{\"email\":\"test@test.com\"}" ^
  -w "\nStatus: %%{http_code}\n" 2>nul
echo.

set /A totalTests+=1
echo [TEST !totalTests!] Password Reset Request
curl -X POST "%BASE_URL%%API_PREFIX%/forgot-password" ^
  -H "Content-Type: application/json" ^
  -d "{\"email\":\"test@test.com\"}" ^
  -w "\nStatus: %%{http_code}\n" 2>nul
echo.

REM ==================== SECTION 2: USER ====================
echo.
echo ============ SECTION 2: USER PROFILE ============
echo.

if defined TOKEN (
  set /A totalTests+=1
  echo [TEST !totalTests!] Get User Profile
  curl -X GET "%BASE_URL%%API_PREFIX%/user/profile" ^
    -H "Authorization: Bearer !TOKEN!" ^
    -w "\nStatus: %%{http_code}\n" 2>nul
  echo.

  set /A totalTests+=1
  echo [TEST !totalTests!] Update User Profile
  curl -X PUT "%BASE_URL%%API_PREFIX%/user/profile" ^
    -H "Authorization: Bearer !TOKEN!" ^
    -H "Content-Type: application/json" ^
    -d "{\"name\":\"Updated Name\",\"age\":25}" ^
    -w "\nStatus: %%{http_code}\n" 2>nul
  echo.
)

REM ==================== SECTION 3: THERAPISTS ====================
echo.
echo ============ SECTION 3: THERAPISTS ============
echo.

set /A totalTests+=1
echo [TEST !totalTests!] Get All Therapists
curl -X GET "%BASE_URL%%API_PREFIX%/therapists" ^
  -w "\nStatus: %%{http_code}\n" 2>nul
echo.

set /A totalTests+=1
echo [TEST !totalTests!] Search Therapists
curl -X GET "%BASE_URL%%API_PREFIX%/therapists?specialty=Depression" ^
  -w "\nStatus: %%{http_code}\n" 2>nul
echo.

set /A totalTests+=1
echo [TEST !totalTests!] Therapist Registration
curl -X POST "%BASE_URL%%API_PREFIX%/therapist/register" ^
  -H "Content-Type: application/json" ^
  -d "{\"email\":\"doc!RANDOM!@test.com\",\"password\":\"Test@123\",\"name\":\"Dr. Test\",\"specialty\":\"Depression\",\"experience\":5,\"license_number\":\"LIC123\"}" ^
  -w "\nStatus: %%{http_code}\n" 2>nul
echo.

REM ==================== SECTION 4: APPOINTMENTS ====================
echo.
echo ============ SECTION 4: APPOINTMENTS ============
echo.

if defined TOKEN (
  set /A totalTests+=1
  echo [TEST !totalTests!] Get My Appointments
  curl -X GET "%BASE_URL%%API_PREFIX%/appointments" ^
    -H "Authorization: Bearer !TOKEN!" ^
    -w "\nStatus: %%{http_code}\n" 2>nul
  echo.

  set /A totalTests+=1
  echo [TEST !totalTests!] Book Appointment
  curl -X POST "%BASE_URL%%API_PREFIX%/appointments" ^
    -H "Authorization: Bearer !TOKEN!" ^
    -H "Content-Type: application/json" ^
    -d "{\"therapist_id\":\"1\",\"date\":\"2026-01-15\",\"time\":\"10:00 AM\",\"session_type\":\"video\",\"reason\":\"Anxiety\"}" ^
    -w "\nStatus: %%{http_code}\n" 2>nul
  echo.
)

REM ==================== SECTION 5: CHAT ====================
echo.
echo ============ SECTION 5: CHAT and MESSAGING ============
echo.

if defined TOKEN (
  set /A totalTests+=1
  echo [TEST !totalTests!] Get Chats
  curl -X GET "%BASE_URL%%API_PREFIX%/chats" ^
    -H "Authorization: Bearer !TOKEN!" ^
    -w "\nStatus: %%{http_code}\n" 2>nul
  echo.

  set /A totalTests+=1
  echo [TEST !totalTests!] Create Chat
  curl -X POST "%BASE_URL%%API_PREFIX%/chats" ^
    -H "Authorization: Bearer !TOKEN!" ^
    -H "Content-Type: application/json" ^
    -d "{\"recipient_id\":\"1\",\"message_type\":\"text\"}" ^
    -w "\nStatus: %%{http_code}\n" 2>nul
  echo.
)

REM ==================== SECTION 6: PAYMENTS ====================
echo.
echo ============ SECTION 6: PAYMENTS ============
echo.

if defined TOKEN (
  set /A totalTests+=1
  echo [TEST !totalTests!] Get Wallet
  curl -X GET "%BASE_URL%%API_PREFIX%/wallet" ^
    -H "Authorization: Bearer !TOKEN!" ^
    -w "\nStatus: %%{http_code}\n" 2>nul
  echo.

  set /A totalTests+=1
  echo [TEST !totalTests!] Payment History
  curl -X GET "%BASE_URL%%API_PREFIX%/payments/history" ^
    -H "Authorization: Bearer !TOKEN!" ^
    -w "\nStatus: %%{http_code}\n" 2>nul
  echo.

  set /A totalTests+=1
  echo [TEST !totalTests!] Create Payment
  curl -X POST "%BASE_URL%%API_PREFIX%/payments/create" ^
    -H "Authorization: Bearer !TOKEN!" ^
    -H "Content-Type: application/json" ^
    -d "{\"amount\":500,\"currency\":\"INR\",\"payment_method\":\"card\"}" ^
    -w "\nStatus: %%{http_code}\n" 2>nul
  echo.
)

REM ==================== SECTION 7: REVIEWS ====================
echo.
echo ============ SECTION 7: REVIEWS ============
echo.

if defined TOKEN (
  set /A totalTests+=1
  echo [TEST !totalTests!] Submit Review
  curl -X POST "%BASE_URL%%API_PREFIX%/reviews" ^
    -H "Authorization: Bearer !TOKEN!" ^
    -H "Content-Type: application/json" ^
    -d "{\"therapist_id\":\"1\",\"rating\":5,\"comment\":\"Great therapist!\"}" ^
    -w "\nStatus: %%{http_code}\n" 2>nul
  echo.
)

REM ==================== SECTION 8: ADMIN ====================
echo.
echo ============ SECTION 8: ADMIN ============
echo.

if defined TOKEN (
  set /A totalTests+=1
  echo [TEST !totalTests!] Get All Users
  curl -X GET "%BASE_URL%%API_PREFIX%/admin/users" ^
    -H "Authorization: Bearer !TOKEN!" ^
    -w "\nStatus: %%{http_code}\n" 2>nul
  echo.

  set /A totalTests+=1
  echo [TEST !totalTests!] Dashboard Stats
  curl -X GET "%BASE_URL%%API_PREFIX%/admin/dashboard/stats" ^
    -H "Authorization: Bearer !TOKEN!" ^
    -w "\nStatus: %%{http_code}\n" 2>nul
  echo.
)

REM ==================== SUMMARY ====================
echo.
echo ================================================
echo TEST SUMMARY
echo ================================================
echo.
echo Total Tests: !totalTests!
echo.

if !totalTests! gtr 0 (
  for /f %%A in ('powershell -Command "Write-Host ([math]::Round(100,1))"') do set percent=%%A
  echo Tests executed successfully
)

echo.
echo ================================================
echo.

pause
