# Backend API Test Script
# Tests core endpoints without pytest

$BASE = "http://localhost:8080"
$pass = 0
$fail = 0
$token = $null

Write-Host "`n================================================" -ForegroundColor Cyan
Write-Host "MENTAL HEALTH - BACKEND API TEST" -ForegroundColor Cyan
Write-Host "Target: $BASE" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan

# Function to test endpoint
function Test-API {
    param([string]$Name, [string]$Endpoint, [string]$Method = "GET", [hashtable]$Body)
    
    Write-Host "`n[$Name]" -ForegroundColor Yellow
    
    try {
        $params = @{
            Uri = "$BASE$Endpoint"
            Method = $Method
            ErrorAction = "Stop"
            TimeoutSec = 10
        }
        
        if ($global:token) {
            $params["Headers"] = @{"Authorization" = "Bearer $global:token"}
        }
        
        if ($Body) {
            $params["Body"] = ($Body | ConvertTo-Json)
            $params["ContentType"] = "application/json"
        }
        
        $response = Invoke-WebRequest @params
        Write-Host "✓ PASS - Status: $($response.StatusCode)" -ForegroundColor Green
        $script:pass++
        
        if ($response.Content) {
            try {
                $data = $response.Content | ConvertFrom-Json
                return $data
            } catch {
                return $response.Content
            }
        }
        return $response
    }
    catch {
        Write-Host "✗ FAIL - Error: $($_.Exception.Message)" -ForegroundColor Red
        $script:fail++
        return $null
    }
}

# ===== 1. AUTHENTICATION =====
Write-Host "`n===== AUTHENTICATION =====" -ForegroundColor Magenta

# Register
$regResult = Test-API "Register User" "/api/register" "POST" @{
    email = "test$(Get-Random)@test.com"
    password = "Test123456!"
    first_name = "Test"
    last_name = "User"
    role = "patient"
}

# Login
$loginResult = Test-API "Login" "/api/login" "POST" @{
    email = "test@test.com"
    password = "Test@123456"
}

if ($loginResult) {
    try {
        $loginData = $loginResult | ConvertFrom-Json
        if ($loginData.access_token) {
            $global:token = $loginData.access_token
            Write-Host "✓ Token obtained: $($global:token.Substring(0, 20))..." -ForegroundColor Green
        }
    } catch {
        Write-Host "Login parsing error" -ForegroundColor Yellow
    }
}

# ===== 2. USER PROFILE =====
Write-Host "`n===== USER PROFILE =====" -ForegroundColor Magenta

Test-API "Get Profile" "/api/user/profile" "GET" | Out-Null
Test-API "Update Profile" "/api/user/profile" "POST" @{
    first_name = "Updated"
    last_name = "Name"
} | Out-Null

# ===== 3. THERAPISTS =====
Write-Host "`n===== THERAPISTS =====" -ForegroundColor Magenta

Test-API "Get All Therapists" "/api/doctors" "GET" | Out-Null
Test-API "Get Therapist List" "/api/doctors?page=1&limit=10" "GET" | Out-Null
Test-API "Search Therapists" "/api/doctors/search?specialization=psychology" "GET" | Out-Null

# ===== 4. APPOINTMENTS =====
Write-Host "`n===== APPOINTMENTS =====" -ForegroundColor Magenta

Test-API "Get Appointments" "/api/appointments" "GET" | Out-Null
Test-API "Book Appointment" "/api/appointments" "POST" @{
    doctor_id = "1"
    appointment_date = "2025-01-20"
    appointment_time = "10:00"
    notes = "Test appointment"
} | Out-Null

# ===== 5. CHAT =====
Write-Host "`n===== CHAT =====" -ForegroundColor Magenta

Test-API "Get Chats" "/api/chats" "GET" | Out-Null
Test-API "Create Chat" "/api/chats" "POST" @{
    doctor_id = "1"
    message = "Hello"
} | Out-Null

# ===== 6. WALLET =====
Write-Host "`n===== WALLET =====" -ForegroundColor Magenta

Test-API "Get Wallet" "/api/wallet/balance" "GET" | Out-Null
Test-API "Wallet History" "/api/wallet/transactions?page=1&limit=10" "GET" | Out-Null

# ===== 7. REVIEWS =====
Write-Host "`n===== REVIEWS =====" -ForegroundColor Magenta

Test-API "Get Reviews" "/api/reviews?page=1&limit=10" "GET" | Out-Null
Test-API "Create Review" "/api/reviews" "POST" @{
    doctor_id = "1"
    rating = 5
    comment = "Great service"
} | Out-Null

# ===== 8. ADMIN =====
Write-Host "`n===== ADMIN =====" -ForegroundColor Magenta

Test-API "Admin Dashboard" "/api/admin/dashboard" "GET" | Out-Null
Test-API "Admin Users" "/api/admin/users?page=1&limit=10" "GET" | Out-Null

# ===== RESULTS =====
Write-Host "`n================================================" -ForegroundColor Cyan
Write-Host "TEST RESULTS" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan
Write-Host "Passed: $pass" -ForegroundColor Green
Write-Host "Failed: $fail" -ForegroundColor $(if ($fail -eq 0) { "Green" } else { "Red" })

$total = $pass + $fail
if ($total -gt 0) {
    $percent = [math]::Round(($pass / $total) * 100, 1)
    Write-Host "Pass Rate: $percent%" -ForegroundColor $(if ($percent -ge 80) { "Green" } else { "Yellow" })
}

if ($fail -eq 0) {
    Write-Host "`n✓ ALL TESTS PASSED!" -ForegroundColor Green
} else {
    Write-Host "`n✗ SOME TESTS FAILED" -ForegroundColor Red
}

Write-Host "`n================================================" -ForegroundColor Cyan
