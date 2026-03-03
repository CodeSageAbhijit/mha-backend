# Quick Backend API Test Script
# Run this in PowerShell to test core API endpoints

$BASE = "http://localhost:8080"

Write-Host "`n" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan
Write-Host "MENTAL HEALTH APP - BACKEND API TEST" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan
Write-Host "Target: $BASE`n" -ForegroundColor Cyan

$pass = 0
$fail = 0

function Test-API {
    param([string]$Name, [string]$Endpoint, [string]$Method = "GET", [hashtable]$Body, [string]$Token)
    
    Write-Host "[$([int](Get-Date -UFormat %s) % 100)] $Name" -ForegroundColor Yellow
    
    try {
        $params = @{
            Uri = "$BASE$Endpoint"
            Method = $Method
            ErrorAction = "Stop"
        }
        
        if ($Token) {
            $params["Headers"] = @{"Authorization" = "Bearer $Token"}
        }
        
        if ($Body) {
            $params["Body"] = ($Body | ConvertTo-Json)
            $params["ContentType"] = "application/json"
        }
        
        $r = Invoke-WebRequest @params
        Write-Host "    ✓ PASS ($($r.StatusCode))" -ForegroundColor Green
        Write-Host ""
        $global:pass++
        return $r
    }
    catch {
        Write-Host "    ✗ FAIL" -ForegroundColor Red
        Write-Host ""
        $global:fail++
        return $null
    }
}

# ==================================================
#  TEST 1-5: AUTH & USER
# ==================================================

$r = Test-API "Register User" "/api/register" "POST" @{
    email = "test_$(Get-Random)@test.com"
    password = "Test@123"
    name = "Test User"
    role = "patient"
}

$r = Test-API "Login" "/api/login" "POST" @{
    email = "testuser@example.com"
    password = "Test@123"
}

$token = if ($r) { ($r.Content | ConvertFrom-Json).access_token } else { "" }

if ($token) {
    Write-Host "    Token: $($token.Substring(0,20))..."  -ForegroundColor Gray
    Write-Host ""
}

$r = Test-API "Get User Profile" "/api/user/profile" "GET" $null $token

$r = Test-API "Update Profile" "/api/user/profile" "PUT" @{
    name = "Updated Name"
    age = 25
} $token

# ==================================================
# TEST 6-10: THERAPISTS
# ==================================================

$r = Test-API "Get All Therapists" "/api/doctors" "GET"

$docId = if ($r) { ($r.Content | ConvertFrom-Json)[0].id } else { "" }

if ($docId) {
    Test-API "Get Therapist Details" "/api/doctors/$docId" "GET" | Out-Null
    Test-API "Get Therapist Availability" "/api/doctors/$docId/availability" "GET" | Out-Null
}

Test-API "Search Therapists" "/api/doctors?specialty=Depression" "GET" | Out-Null

# ==================================================
# TEST 11-15: APPOINTMENTS
# ==================================================

if ($token) {
    $r = Test-API "Get Appointments" "/api/appointments" "GET" $null $token
    
    $r = Test-API "Book Appointment" "/api/appointments" "POST" @{
        doctor_id = $docId
        date = (Get-Date).AddDays(3).ToString("yyyy-MM-dd")
        time = "10:00 AM"
        session_type = "video"
        reason = "Anxiety"
    } $token
    
    $appointmentId = if ($r) { ($r.Content | ConvertFrom-Json).appointment_id } else { "" }
}

# ==================================================
# TEST 16-20: CHAT & MESSAGING
# ==================================================

if ($token) {
    Test-API "Get Chats" "/api/chats" "GET" $null $token | Out-Null
    
    Test-API "Create Chat" "/api/chats" "POST" @{
        recipient_id = $docId
        message_type = "text"
    } $token | Out-Null
}

# ==================================================
# TEST 21-25: PAYMENTS & WALLET
# ==================================================

if ($token) {
    Test-API "Get Wallet" "/api/wallet" "GET" $null $token | Out-Null
    
    Test-API "Get Payment History" "/api/payments/history" "GET" $null $token | Out-Null
    
    Test-API "Create Payment" "/api/payments" "POST" @{
        amount = 500
        currency = "INR"
        method = "card"
    } $token | Out-Null
}

# ==================================================
# TEST 26-30: ADMIN & REVIEWS
# ==================================================

if ($token) {
    Test-API "Get Admin Dashboard" "/api/admin/dashboard" "GET" $null $token | Out-Null
}

if ($token) {
    Test-API "Submit Review" "/api/reviews" "POST" @{
        doctor_id = $docId
        rating = 5
        comment = "Great therapist!"
    } $token | Out-Null
}

if ($docId) {
    Test-API "Get Therapist Reviews" "/api/reviews/doctor/$docId" "GET" | Out-Null
}

# ==================================================
# SUMMARY
# ==================================================

Write-Host ""
Write-Host "================================================" -ForegroundColor Cyan
Write-Host "TEST SUMMARY" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "Passed: $pass" -ForegroundColor Green
Write-Host "Failed: $fail" -ForegroundColor $(if ($fail -eq 0) { "Green" } else { "Red" })

$total = $pass + $fail
if ($total -gt 0) {
    $percent = [math]::Round(($pass / $total) * 100, 1)
    Write-Host "Rate: $percent%`n"
}

if ($fail -eq 0) {
    Write-Host "✓ ALL TESTS PASSED!" -ForegroundColor Green
    Write-Host ""
} else {
    Write-Host "✗ SOME TESTS FAILED - Check errors above" -ForegroundColor Red
    Write-Host ""
}

Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""
