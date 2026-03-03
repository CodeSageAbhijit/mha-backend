# Quick Backend API Test
# Run this in PowerShell to test all endpoints

$BASE = "http://localhost:8080"

Write-Host "Testing Backend API Endpoints`n" -ForegroundColor Cyan

# Test 1: Health
Write-Host "[1] Health Check" -ForegroundColor Yellow
try {
    $r = Invoke-WebRequest "$BASE/health" -ErrorAction Stop
    Write-Host "✓ PASS`n" -ForegroundColor Green
} catch { Write-Host "✗ FAIL`n" -ForegroundColor Red }

# Test 2: Register
Write-Host "[2] Register User" -ForegroundColor Yellow
try {
    $r = Invoke-WebRequest "$BASE/api/register" -Method POST `
        -Body (@{email="test_$((Get-Random))@test.com";password="Test@123";name="User";role="patient"} | ConvertTo-Json) `
        -Headers @{"Content-Type"="application/json"} -ErrorAction Stop
    Write-Host "✓ PASS`n" -ForegroundColor Green
} catch { Write-Host "✗ FAIL`n" -ForegroundColor Red }

# Test 3: Login
Write-Host "[3] Login" -ForegroundColor Yellow
try {
    $r = Invoke-WebRequest "$BASE/api/login" -Method POST `
        -Body (@{email="testuser@example.com";password="Test@123"} | ConvertTo-Json) `
        -Headers @{"Content-Type"="application/json"} -ErrorAction Stop
    $token = ($r.Content | ConvertFrom-Json).access_token
    Write-Host "✓ PASS (Token: $($token.Substring(0,20))...)`n" -ForegroundColor Green
} catch { Write-Host "✗ FAIL`n" -ForegroundColor Red; $token = "" }

# Test 4: Get Therapists
Write-Host "[4] Get Therapists" -ForegroundColor Yellow
try {
    $r = Invoke-WebRequest "$BASE/api/therapists" -ErrorAction Stop
    $docs = $r.Content | ConvertFrom-Json
    Write-Host "✓ PASS (Found $($docs.Count) therapists)`n" -ForegroundColor Green
    if ($docs.Count -gt 0) { $docId = $docs[0].id }
} catch { Write-Host "✗ FAIL`n" -ForegroundColor Red }

# Test 5: Get Therapist Details
if ($docId) {
    Write-Host "[5] Get Therapist Details" -ForegroundColor Yellow
    try {
        $r = Invoke-WebRequest "$BASE/api/therapists/$docId" -ErrorAction Stop
        Write-Host "✓ PASS`n" -ForegroundColor Green
    } catch { Write-Host "✗ FAIL`n" -ForegroundColor Red }
}

# Test 6: Get User Profile (requires auth)
if ($token) {
    Write-Host "[6] Get User Profile" -ForegroundColor Yellow
    try {
        $r = Invoke-WebRequest "$BASE/api/user/profile" `
            -Headers @{"Authorization"="Bearer $token"} `
            -ErrorAction Stop
        Write-Host "✓ PASS`n" -ForegroundColor Green
    } catch { Write-Host "✗ FAIL`n" -ForegroundColor Red }
}

# Test 7: Get Appointments (requires auth)
if ($token) {
    Write-Host "[7] Get My Appointments" -ForegroundColor Yellow
    try {
        $r = Invoke-WebRequest "$BASE/api/appointments" `
            -Headers @{"Authorization"="Bearer $token"} `
            -ErrorAction Stop
        Write-Host "✓ PASS`n" -ForegroundColor Green
    } catch { Write-Host "✗ FAIL`n" -ForegroundColor Red }
}

# Test 8: Get Chats (requires auth)
if ($token) {
    Write-Host "[8] Get Chats" -ForegroundColor Yellow
    try {
        $r = Invoke-WebRequest "$BASE/api/chats" `
            -Headers @{"Authorization"="Bearer $token"} `
            -ErrorAction Stop
        Write-Host "✓ PASS`n" -ForegroundColor Green
    } catch { Write-Host "✗ FAIL`n" -ForegroundColor Red }
}

# Test 9: Get Wallet (requires auth)
if ($token) {
    Write-Host "[9] Get Wallet" -ForegroundColor Yellow
    try {
        $r = Invoke-WebRequest "$BASE/api/wallet" `
            -Headers @{"Authorization"="Bearer $token"} `
            -ErrorAction Stop
        Write-Host "✓ PASS`n" -ForegroundColor Green
    } catch { Write-Host "✗ FAIL`n" -ForegroundColor Red }
}

# Test 10: Get Payment History (requires auth)
if ($token) {
    Write-Host "[10] Get Payment History" -ForegroundColor Yellow
    try {
        $r = Invoke-WebRequest "$BASE/api/payments/history" `
            -Headers @{"Authorization"="Bearer $token"} `
            -ErrorAction Stop
        Write-Host "✓ PASS`n" -ForegroundColor Green
    } catch { Write-Host "✗ FAIL`n" -ForegroundColor Red }
}

Write-Host "================================================" -ForegroundColor Cyan
Write-Host "BASIC TEST COMPLETE" -ForegroundColor Cyan
Write-Host "================================================`n" -ForegroundColor Cyan

Write-Host "To run comprehensive tests, see:" -ForegroundColor Yellow
Write-Host "- test_endpoints.bat (Windows batch)" -ForegroundColor Gray
Write-Host "- test_all_endpoints.ps1 (Full PowerShell)" -ForegroundColor Gray
