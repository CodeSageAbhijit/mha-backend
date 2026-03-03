@echo off
REM Backend API Test using curl

setlocal enabledelayedexpansion

set BASE=http://localhost:8080
set pass=0
set fail=0
set token=

echo.
echo ================================================
echo MENTAL HEALTH - BACKEND API TEST
echo Target: %BASE%
echo ================================================
echo.

REM Test function
:test_api
set name=%1
set endpoint=%2
set method=%3

echo [%name%]
curl -s -X %method% "%BASE%%endpoint%" -H "Content-Type: application/json" >nul 2>&1
if %errorlevel% equ 0 (
    echo OK - PASS
    set /a pass+=1
) else (
    echo FAIL
    set /a fail+=1
)
exit /b

REM ===== AUTHENTICATION =====
echo.
echo ===== AUTHENTICATION =====
call :test_api "Health Check" "/health" "GET"
call :test_api "Login" "/api/login" "POST"
call :test_api "Register" "/api/register" "POST"

REM ===== USER PROFILE =====
echo.
echo ===== USER PROFILE =====
call :test_api "Get Profile" "/api/user/profile" "GET"
call :test_api "Update Profile" "/api/user/profile" "POST"

REM ===== THERAPISTS =====
echo.
echo ===== THERAPISTS =====
call :test_api "Get Therapists" "/api/doctors" "GET"
call :test_api "Search Therapists" "/api/doctors/search" "GET"

REM ===== APPOINTMENTS =====
echo.
echo ===== APPOINTMENTS =====
call :test_api "Get Appointments" "/api/appointments" "GET"
call :test_api "Book Appointment" "/api/appointments" "POST"

REM ===== CHAT =====
echo.
echo ===== CHAT =====
call :test_api "Get Chats" "/api/chats" "GET"

REM ===== WALLET =====
echo.
echo ===== WALLET =====
call :test_api "Get Wallet" "/api/wallet/balance" "GET"

REM ===== RESULTS =====
echo.
echo ================================================
echo TEST RESULTS
echo ================================================
echo Passed: %pass%
echo Failed: %fail%

set /a total=pass+fail
if %total% gtr 0 (
    set /a percent=!pass!*100/%total%
    echo Pass Rate: !percent!%%
)

if %fail% equ 0 (
    echo.
    echo ALL TESTS PASSED!
) else (
    echo.
    echo SOME TESTS FAILED
)

echo ================================================
echo.

pause
