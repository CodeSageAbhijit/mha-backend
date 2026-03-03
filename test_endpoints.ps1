# Backend API Testing Script - PowerShell
# Tests all Mental Health Application endpoints
# No pytest required - uses native PowerShell cmdlets

$BASE_URL = "http://localhost:8080"
$API_PREFIX = "/api"
$HEADERS = @{"Content-Type" = "application/json"}

# Test counters
$totalTests = 0
$passedTests = 0
$failedTests = 0
$authToken = ""

Write-Host "================================================"
Write-Host "BACKEND API TESTING - POWERSHELL"
Write-Host "================================================"
Write-Host "URL: $BASE_URL"
Write-Host "================================================`n"

# Check if server is running
Write-Host "[CHECK] Testing server connection..." -ForegroundColor Cyan
try {
    $health = Invoke-WebRequest -Uri "$BASE_URL/health" -Method GET -ErrorAction Stop
    Write-Host "OK - Server is running`n" -ForegroundColor Green
}
catch {
    Write-Host "ERROR - Server not running at $BASE_URL" -ForegroundColor Red
    Write-Host "Start backend: python run.py`n" -ForegroundColor Yellow
    exit
}

# Function to test endpoint
function Test-API {
    param([string]$Method, [string]$Endpoint, [hashtable]$Body, [string]$Desc, [string]$Token)
    
    global:$totalTests++
    $url = "$BASE_URL$API_PREFIX$Endpoint"
    Write-Host "[TEST $global:totalTests] $Desc" -ForegroundColor Cyan
    Write-Host "  $Method $url" -ForegroundColor Gray
    
    try {
        $params = @{
            Uri = $url
            Method = $Method
            Headers = $HEADERS
            ErrorAction = "Stop"
        }
        
        if ($Token) {
            $params["Headers"]["Authorization"] = "Bearer $Token"
        }
        
        if ($Body) {
            $params["Body"] = ($Body | ConvertTo-Json -Compress)
        }
        
        $response = Invoke-WebRequest @params
        Write-Host "  ✓ PASS (Status: $($response.StatusCode))`n" -ForegroundColor Green
        $global:passedTests++
        return $response
    }
    catch {
        $status = $_.Exception.Response.StatusCode.Value__
        Write-Host "  ✗ FAIL (Status: $status)`n" -ForegroundColor Red
        $global:failedTests++
        return $null
    }
}

# SECTION 1: AUTH
Write-Host "`n============ SECTION 1: AUTHENTICATION ============`n" -ForegroundColor Yellow

Test-API POST "/register" @{email="test$(Get-Random)@test.com";password="Test@123";name="User";role="patient"} "Registration"

$resp = Test-API POST "/login" @{email="testuser@example.com";password="Test@123"} "Login"
if ($resp) {
    $authToken = ($resp.Content | ConvertFrom-Json).access_token
    Write-Host "  Token: $($authToken.Substring(0, 20))...`n" -ForegroundColor Gray
}

Test-API POST "/verify-otp" @{email="test@test.com";otp="123456"} "Verify OTP"
Test-API POST "/resend-otp" @{email="test@test.com"} "Resend OTP"
Test-API POST "/forgot-password" @{email="test@test.com"} "Password Reset"

# SECTION 2: USER
Write-Host "`n============ SECTION 2: USER PROFILE ============`n" -ForegroundColor Yellow

if ($authToken) {
    Test-API GET "/user/profile" $null "Get Profile" $authToken
    Test-API PUT "/user/profile" @{name="Updated";age=25} "Update Profile" $authToken
    Test-API POST "/user/profile/picture" @{image_url="http://example.com/img.jpg"} "Upload Picture" $authToken
}

# SECTION 3: THERAPISTS
Write-Host "`n============ SECTION 3: THERAPISTS ============`n" -ForegroundColor Yellow

$resp = Test-API GET "/therapists" $null "Get All Therapists"
$doctorId = ""
if ($resp) {
    $docs = $resp.Content | ConvertFrom-Json
    if ($docs.Count -gt 0) { $doctorId = $docs[0].id }
    Write-Host "  First therapist ID: $doctorId`n" -ForegroundColor Gray
}

Test-API GET "/therapists?specialty=Depression" $null "Search Therapists"

if ($doctorId) {
    Test-API GET "/therapists/$doctorId" $null "Get Therapist"
    Test-API GET "/therapists/$doctorId/availability" $null "Get Availability"
    Test-API GET "/therapists/$doctorId/reviews" $null "Get Reviews"
}

Test-API POST "/therapist/register" @{email="doc$(Get-Random)@test.com";password="Test@123";name="Dr. Test";specialty="Depression";experience=5;license_number="LIC123"} "Therapist Register"

# SECTION 4: APPOINTMENTS
Write-Host "`n============ SECTION 4: APPOINTMENTS ============`n" -ForegroundColor Yellow

if ($authToken) {
    $resp = Test-API POST "/appointments" @{therapist_id=$doctorId;date=(Get-Date).AddDays(3).ToString("yyyy-MM-dd");time="10:00 AM";session_type="video";reason="Anxiety"} "Book Appointment" $authToken
    $appointmentId = ""
    if ($resp) { $appointmentId = ($resp.Content | ConvertFrom-Json).appointment_id }
    Write-Host "  Appointment ID: $appointmentId`n" -ForegroundColor Gray
    
    Test-API GET "/appointments" $null "Get My Appointments" $authToken
    
    if ($appointmentId) {
        Test-API GET "/appointments/$appointmentId" $null "Get Appointment" $authToken
        Test-API PUT "/appointments/$appointmentId/reschedule" @{new_date=(Get-Date).AddDays(4).ToString("yyyy-MM-dd");new_time="02:00 PM"} "Reschedule" $authToken
        Test-API POST "/appointments/$appointmentId/cancel" @{reason="Cannot attend"} "Cancel" $authToken
    }
}

# SECTION 5: CHAT
Write-Host "`n============ SECTION 5: CHAT and MESSAGING ============`n" -ForegroundColor Yellow

if ($authToken) {
    Test-API GET "/chats" $null "Get Chats" $authToken
    
    $resp = Test-API POST "/chats" @{recipient_id=$doctorId;message_type="text"} "Create Chat" $authToken
    $chatId = ""
    if ($resp) { $chatId = ($resp.Content | ConvertFrom-Json).chat_id }
    Write-Host "  Chat ID: $chatId`n" -ForegroundColor Gray
    
    if ($chatId) {
        Test-API POST "/chats/$chatId/messages" @{message="Hello!";message_type="text"} "Send Message" $authToken
        Test-API GET "/chats/$chatId/messages" $null "Get Messages" $authToken
        Test-API POST "/chats/$chatId/mark-read" @{} "Mark Read" $authToken
    }
}

# SECTION 6: PAYMENTS
Write-Host "`n============ SECTION 6: PAYMENTS ============`n" -ForegroundColor Yellow

if ($authToken) {
    Test-API POST "/payments/create" @{amount=500;currency="INR";payment_method="card"} "Create Payment" $authToken
    Test-API POST "/payments/verify" @{payment_id="PAY_123";signature="sig"} "Verify Payment" $authToken
    Test-API GET "/payments/history" $null "Payment History" $authToken
    Test-API GET "/wallet" $null "Get Wallet" $authToken
    Test-API POST "/wallet/add" @{amount=1000;payment_method="upi"} "Add to Wallet" $authToken
}

# SECTION 7: REVIEWS
Write-Host "`n============ SECTION 7: REVIEWS ============`n" -ForegroundColor Yellow

if ($authToken) {
    Test-API POST "/reviews" @{therapist_id=$doctorId;rating=5;comment="Great!"} "Submit Review" $authToken
    if ($doctorId) {
        Test-API GET "/reviews/therapist/$doctorId" $null "Get Reviews" $authToken
    }
}

# SECTION 8: ADMIN
Write-Host "`n============ SECTION 8: ADMIN ============`n" -ForegroundColor Yellow

if ($authToken) {
    Test-API GET "/admin/users" $null "Get Users" $authToken
    Test-API GET "/admin/therapists" $null "Get Therapists" $authToken
    if ($doctorId) {
        Test-API POST "/admin/therapists/$doctorId/verify" @{status="approved"} "Approve Therapist" $authToken
    }
    Test-API GET "/admin/dashboard/stats" $null "Dashboard Stats" $authToken
    Test-API GET "/admin/transactions" $null "Transactions" $authToken
}

# SECTION 9: AI
Write-Host "`n============ SECTION 9: AI and RECOMMENDATIONS ============`n" -ForegroundColor Yellow

if ($authToken) {
    Test-API GET "/recommendations" $null "Get Recommendations" $authToken
    Test-API POST "/mood-checkin" @{mood="happy";intensity=8} "Mood Checkin" $authToken
    Test-API GET "/mood-history" $null "Mood History" $authToken
}

# SECTION 10: CRISIS
Write-Host "`n============ SECTION 10: CRISIS SUPPORT ============`n" -ForegroundColor Yellow

if ($authToken) {
    Test-API GET "/crisis-resources" $null "Crisis Resources" $authToken
    Test-API POST "/crisis-report" @{description="Help";urgency="high"} "Report Crisis" $authToken
}

# SUMMARY
Write-Host "`n================================================" -ForegroundColor Yellow
Write-Host "TEST SUMMARY" -ForegroundColor Yellow
Write-Host "================================================`n" -ForegroundColor Yellow

Write-Host "Total Tests: $global:totalTests"
Write-Host "Passed: $global:passedTests" -ForegroundColor Green
Write-Host "Failed: $global:failedTests" -ForegroundColor Red

if ($global:totalTests -gt 0) {
    $percent = [math]::Round(($global:passedTests / $global:totalTests) * 100, 1)
    Write-Host "Pass Rate: $percent%`n"
}

if ($global:failedTests -eq 0) {
    Write-Host "SUCCESS - All tests passed!`n" -ForegroundColor Green
} else {
    Write-Host "FAILED - Some tests failed. Check errors above.`n" -ForegroundColor Red
}

Write-Host "================================================" -ForegroundColor Yellow
