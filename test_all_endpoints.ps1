# Mental Health Application - Backend API Testing Script
# PowerShell Script to Test All Endpoints Without pytest
# Date: January 7, 2026

# Configuration
$BASE_URL = "http://localhost:8080"
$API_PREFIX = "/api"
$HEADERS = @{
    "Content-Type" = "application/json"
    "Accept" = "application/json"
}

# Colors for output
$GREEN = "Green"
$RED = "Red"
$YELLOW = "Yellow"
$CYAN = "Cyan"

# Test counters
$totalTests = 0
$passedTests = 0
$failedTests = 0
$authToken = ""
$userId = ""
$doctorId = ""
$appointmentId = ""
$chatId = ""

# ==================== UTILITY FUNCTIONS ====================

function Test-Endpoint {
    param(
        [string]$Method,
        [string]$Endpoint,
        [hashtable]$Body,
        [string]$Description,
        [string]$ExpectedStatus = "200"
    )
    
    $totalTests++
    $url = "$BASE_URL$API_PREFIX$Endpoint"
    
    Write-Host "`n[TEST $totalTests] $Description" -ForegroundColor $CYAN
    Write-Host "Method: $Method | URL: $url" -ForegroundColor Gray
    
    try {
        $params = @{
            Uri = $url
            Method = $Method
            Headers = $HEADERS
            ContentType = "application/json"
            ErrorAction = "Stop"
        }
        
        if ($Body) {
            $params["Body"] = ($Body | ConvertTo-Json -Compress)
            Write-Host "Body: $($params['Body'])" -ForegroundColor Gray
        }
        
        $response = Invoke-WebRequest @params
        
        Write-Host "✓ PASSED - Status: $($response.StatusCode)" -ForegroundColor $GREEN
        $passedTests++
        
        return $response
    }
    catch {
        $statusCode = $_.Exception.Response.StatusCode.Value__
        Write-Host "✗ FAILED - Status: $statusCode | Error: $($_.Exception.Message)" -ForegroundColor $RED
        $failedTests++
        return $null
    }
}

function Test-Endpoint-Auth {
    param(
        [string]$Method,
        [string]$Endpoint,
        [hashtable]$Body,
        [string]$Description,
        [string]$Token
    )
    
    $totalTests++
    $url = "$BASE_URL$API_PREFIX$Endpoint"
    
    Write-Host "`n[TEST $totalTests] $Description" -ForegroundColor $CYAN
    Write-Host "Method: $Method | URL: $url" -ForegroundColor Gray
    
    try {
        $authHeaders = $HEADERS.Clone()
        if ($Token) {
            $authHeaders["Authorization"] = "Bearer $Token"
        }
        
        $params = @{
            Uri = $url
            Method = $Method
            Headers = $authHeaders
            ContentType = "application/json"
            ErrorAction = "Stop"
        }
        
        if ($Body) {
            $params["Body"] = ($Body | ConvertTo-Json -Compress)
            Write-Host "Body: $($params['Body'])" -ForegroundColor Gray
        }
        
        $response = Invoke-WebRequest @params
        
        Write-Host "✓ PASSED - Status: $($response.StatusCode)" -ForegroundColor $GREEN
        $passedTests++
        
        return $response
    }
    catch {
        $statusCode = $_.Exception.Response.StatusCode.Value__
        Write-Host "✗ FAILED - Status: $statusCode | Error: $($_.Exception.Message)" -ForegroundColor $RED
        $failedTests++
        return $null
    }
}

# ==================== HEALTH CHECK ====================

Write-Host "`n" + "="*60 -ForegroundColor $YELLOW
Write-Host "STARTING BACKEND API TESTS" -ForegroundColor $YELLOW
Write-Host "Base URL: $BASE_URL" -ForegroundColor $YELLOW
Write-Host "="*60 -ForegroundColor $YELLOW

# Check if server is running
Write-Host "`n[HEALTH CHECK] Connecting to Backend..." -ForegroundColor $CYAN
try {
    $health = Invoke-WebRequest -Uri "$BASE_URL/health" -Method GET -ErrorAction Stop
    Write-Host "✓ Backend is running!" -ForegroundColor $GREEN
} catch {
    Write-Host "✗ Backend is not responding at $BASE_URL" -ForegroundColor $RED
    Write-Host "Please start the backend server first: python run.py" -ForegroundColor $YELLOW
    exit
}

# ==================== SECTION 1: AUTHENTICATION ====================

Write-Host "`n" + "="*60 -ForegroundColor $YELLOW
Write-Host "SECTION 1: AUTHENTICATION ENDPOINTS" -ForegroundColor $YELLOW
Write-Host "="*60 -ForegroundColor $YELLOW

# Test 1: User Registration
$response = Test-Endpoint -Method POST -Endpoint "/register" `
    -Body @{
        email = "testuser_$(Get-Random)@example.com"
        phone = "9876543210"
        password = "Test@1234"
        name = "Test User"
        role = "patient"
    } `
    -Description "User Registration"

if ($response) {
    $userId = ($response.Content | ConvertFrom-Json).user_id
    Write-Host "User ID: $userId" -ForegroundColor Gray
}

# Test 2: User Login
$response = Test-Endpoint -Method POST -Endpoint "/login" `
    -Body @{
        email = "testuser@example.com"
        password = "Test@1234"
    } `
    -Description "User Login"

if ($response) {
    $authToken = ($response.Content | ConvertFrom-Json).access_token
    Write-Host "Auth Token: $($authToken.Substring(0, 20))..." -ForegroundColor Gray
}

# Test 3: Verify Email OTP
Test-Endpoint -Method POST -Endpoint "/verify-otp" `
    -Body @{
        email = "testuser@example.com"
        otp = "123456"
    } `
    -Description "Email OTP Verification"

# Test 4: Resend OTP
Test-Endpoint -Method POST -Endpoint "/resend-otp" `
    -Body @{
        email = "testuser@example.com"
    } `
    -Description "Resend OTP"

# Test 5: Password Reset Request
Test-Endpoint -Method POST -Endpoint "/forgot-password" `
    -Body @{
        email = "testuser@example.com"
    } `
    -Description "Password Reset Request"

# Test 6: Logout (requires auth)
if ($authToken) {
    Test-Endpoint-Auth -Method POST -Endpoint "/logout" `
        -Body @{} `
        -Description "User Logout" `
        -Token $authToken
}

# ==================== SECTION 2: USER PROFILE ====================

Write-Host "`n" + "="*60 -ForegroundColor $YELLOW
Write-Host "SECTION 2: USER PROFILE ENDPOINTS" -ForegroundColor $YELLOW
Write-Host "="*60 -ForegroundColor $YELLOW

if ($authToken) {
    # Test 7: Get User Profile
    Test-Endpoint-Auth -Method GET -Endpoint "/user/profile" `
        -Description "Get User Profile" `
        -Token $authToken
    
    # Test 8: Update User Profile
    Test-Endpoint-Auth -Method PUT -Endpoint "/user/profile" `
        -Body @{
            name = "Updated Name"
            phone = "9876543210"
            age = 25
            gender = "Male"
        } `
        -Description "Update User Profile" `
        -Token $authToken
    
    # Test 9: Upload Profile Picture
    Test-Endpoint-Auth -Method POST -Endpoint "/user/profile/picture" `
        -Body @{
            image_url = "https://example.com/image.jpg"
        } `
        -Description "Upload Profile Picture" `
        -Token $authToken
}

# ==================== SECTION 3: THERAPIST ENDPOINTS ====================

Write-Host "`n" + "="*60 -ForegroundColor $YELLOW
Write-Host "SECTION 3: THERAPIST ENDPOINTS" -ForegroundColor $YELLOW
Write-Host "="*60 -ForegroundColor $YELLOW

# Test 10: Get All Therapists
$response = Test-Endpoint -Method GET -Endpoint "/therapists" `
    -Description "Get All Therapists"

if ($response) {
    $therapists = $response.Content | ConvertFrom-Json
    if ($therapists.Count -gt 0) {
        $doctorId = $therapists[0].id
        Write-Host "Therapist ID: $doctorId" -ForegroundColor Gray
    }
}

# Test 11: Search Therapists
Test-Endpoint -Method GET -Endpoint "/therapists?specialty=Depression`&rating=4" `
    -Description "Search Therapists by Specialty"

# Test 12: Get Therapist Details
if ($doctorId) {
    Test-Endpoint -Method GET -Endpoint "/therapists/$doctorId" `
        -Description "Get Therapist Details"
    
    # Test 13: Get Therapist Availability
    Test-Endpoint -Method GET -Endpoint "/therapists/$doctorId/availability" `
        -Description "Get Therapist Availability"
}

# Test 14: Get Therapist Reviews
if ($doctorId) {
    Test-Endpoint -Method GET -Endpoint "/therapists/$doctorId/reviews" `
        -Description "Get Therapist Reviews"
}

# Test 15: Therapist Registration
Test-Endpoint -Method POST -Endpoint "/therapist/register" `
    -Body @{
        email = "therapist_$(Get-Random)@example.com"
        phone = "9876543211"
        password = "Test@1234"
        name = "Dr. Test"
        specialty = "Depression"
        experience = 5
        license_number = "LIC123456"
    } `
    -Description "Therapist Registration"

# ==================== SECTION 4: APPOINTMENTS ====================

Write-Host "`n" + "="*60 -ForegroundColor $YELLOW
Write-Host "SECTION 4: APPOINTMENT ENDPOINTS" -ForegroundColor $YELLOW
Write-Host "="*60 -ForegroundColor $YELLOW

if ($authToken) {
    # Test 16: Book Appointment
    $response = Test-Endpoint-Auth -Method POST -Endpoint "/appointments" `
        -Body @{
            therapist_id = $doctorId
            date = (Get-Date).AddDays(3).ToString("yyyy-MM-dd")
            time = "10:00 AM"
            session_type = "video"
            reason = "Anxiety consultation"
        } `
        -Description "Book Appointment" `
        -Token $authToken
    
    if ($response) {
        $appointmentId = ($response.Content | ConvertFrom-Json).appointment_id
        Write-Host "Appointment ID: $appointmentId" -ForegroundColor Gray
    }
    
    # Test 17: Get My Appointments
    Test-Endpoint-Auth -Method GET -Endpoint "/appointments" `
        -Description "Get My Appointments" `
        -Token $authToken
    
    # Test 18: Get Appointment Details
    if ($appointmentId) {
        Test-Endpoint-Auth -Method GET -Endpoint "/appointments/$appointmentId" `
            -Description "Get Appointment Details" `
            -Token $authToken
    }
    
    # Test 19: Reschedule Appointment
    if ($appointmentId) {
        Test-Endpoint-Auth -Method PUT -Endpoint "/appointments/$appointmentId/reschedule" `
            -Body @{
                new_date = (Get-Date).AddDays(4).ToString("yyyy-MM-dd")
                new_time = "02:00 PM"
            } `
            -Description "Reschedule Appointment" `
            -Token $authToken
    }
    
    # Test 20: Cancel Appointment
    if ($appointmentId) {
        Test-Endpoint-Auth -Method POST -Endpoint "/appointments/$appointmentId/cancel" `
            -Body @{
                reason = "Cannot attend"
            } `
            -Description "Cancel Appointment" `
            -Token $authToken
    }
}

# ==================== SECTION 5: CHAT & MESSAGING ====================

Write-Host "`n" + "="*60 -ForegroundColor $YELLOW
Write-Host "SECTION 5: CHAT and MESSAGING ENDPOINTS" -ForegroundColor $YELLOW
Write-Host "="*60 -ForegroundColor $YELLOW

if ($authToken) {
    # Test 21: Get Chat List
    $response = Test-Endpoint-Auth -Method GET -Endpoint "/chats" `
        -Description "Get Chat List" `
        -Token $authToken
    
    # Test 22: Create Chat Room
    $response = Test-Endpoint-Auth -Method POST -Endpoint "/chats" `
        -Body @{
            recipient_id = $doctorId
            message_type = "text"
        } `
        -Description "Create Chat Room" `
        -Token $authToken
    
    if ($response) {
        $chatId = ($response.Content | ConvertFrom-Json).chat_id
        Write-Host "Chat ID: $chatId" -ForegroundColor Gray
    }
    
    # Test 23: Send Message
    if ($chatId) {
        Test-Endpoint-Auth -Method POST -Endpoint "/chats/$chatId/messages" `
            -Body @{
                message = "Hello, how are you?"
                message_type = "text"
            } `
            -Description "Send Chat Message" `
            -Token $authToken
    }
    
    # Test 24: Get Chat Messages
    if ($chatId) {
        Test-Endpoint-Auth -Method GET -Endpoint "/chats/$chatId/messages" `
            -Description "Get Chat Messages" `
            -Token $authToken
    }
    
    # Test 25: Mark as Read
    if ($chatId) {
        Test-Endpoint-Auth -Method POST -Endpoint "/chats/$chatId/mark-read" `
            -Body @{} `
            -Description "Mark Chat as Read" `
            -Token $authToken
    }
}

# ==================== SECTION 6: PAYMENTS ====================

Write-Host "`n" + "="*60 -ForegroundColor $YELLOW
Write-Host "SECTION 6: PAYMENT ENDPOINTS" -ForegroundColor $YELLOW
Write-Host "="*60 -ForegroundColor $YELLOW

if ($authToken) {
    # Test 26: Create Payment
    $response = Test-Endpoint-Auth -Method POST -Endpoint "/payments/create" `
        -Body @{
            appointment_id = $appointmentId
            amount = 500
            currency = "INR"
            payment_method = "credit_card"
        } `
        -Description "Create Payment" `
        -Token $authToken
    
    # Test 27: Verify Payment
    Test-Endpoint-Auth -Method POST -Endpoint "/payments/verify" `
        -Body @{
            payment_id = "PAY_123456"
            signature = "signature_hash"
        } `
        -Description "Verify Payment" `
        -Token $authToken
    
    # Test 28: Get Payment History
    Test-Endpoint-Auth -Method GET -Endpoint "/payments/history" `
        -Description "Get Payment History" `
        -Token $authToken
    
    # Test 29: Get Wallet
    Test-Endpoint-Auth -Method GET -Endpoint "/wallet" `
        -Description "Get Wallet Balance" `
        -Token $authToken
    
    # Test 30: Add to Wallet
    Test-Endpoint-Auth -Method POST -Endpoint "/wallet/add" `
        -Body @{
            amount = 1000
            payment_method = "upi"
        } `
        -Description "Add Funds to Wallet" `
        -Token $authToken
}

# ==================== SECTION 7: REVIEWS ====================

Write-Host "`n" + "="*60 -ForegroundColor $YELLOW
Write-Host "SECTION 7: REVIEW and RATING ENDPOINTS" -ForegroundColor $YELLOW
Write-Host "="*60 -ForegroundColor $YELLOW

if ($authToken) {
    # Test 31: Submit Review
    Test-Endpoint-Auth -Method POST -Endpoint "/reviews" `
        -Body @{
            therapist_id = $doctorId
            rating = 5
            comment = "Great therapist, very helpful!"
            anonymous = $false
        } `
        -Description "Submit Review" `
        -Token $authToken
    
    # Test 32: Get Reviews
    if ($doctorId) {
        Test-Endpoint-Auth -Method GET -Endpoint "/reviews/therapist/$doctorId" `
            -Description "Get Therapist Reviews" `
            -Token $authToken
    }
}

# ==================== SECTION 8: ADMIN ENDPOINTS ====================

Write-Host "`n" + "="*60 -ForegroundColor $YELLOW
Write-Host "SECTION 8: ADMIN ENDPOINTS" -ForegroundColor $YELLOW
Write-Host "="*60 -ForegroundColor $YELLOW

# Note: These require admin token
if ($authToken) {
    # Test 33: Get Users (Admin)
    Test-Endpoint-Auth -Method GET -Endpoint "/admin/users" `
        -Description "Get All Users (Admin)" `
        -Token $authToken
    
    # Test 34: Get Therapists (Admin)
    Test-Endpoint-Auth -Method GET -Endpoint "/admin/therapists" `
        -Description "Get All Therapists (Admin)" `
        -Token $authToken
    
    # Test 35: Verify Therapist
    Test-Endpoint-Auth -Method POST -Endpoint "/admin/therapists/$doctorId/verify" `
        -Body @{
            status = "approved"
        } `
        -Description "Approve Therapist (Admin)" `
        -Token $authToken
    
    # Test 36: Get Dashboard Stats
    Test-Endpoint-Auth -Method GET -Endpoint "/admin/dashboard/stats" `
        -Description "Get Dashboard Stats (Admin)" `
        -Token $authToken
    
    # Test 37: Get Transactions
    Test-Endpoint-Auth -Method GET -Endpoint "/admin/transactions" `
        -Description "Get Transactions (Admin)" `
        -Token $authToken
}

# ==================== SECTION 9: AI and RECOMMENDATIONS ====================

Write-Host "`n" + "="*60 -ForegroundColor $YELLOW
Write-Host "SECTION 9: AI and RECOMMENDATION ENDPOINTS" -ForegroundColor $YELLOW
Write-Host "="*60 -ForegroundColor $YELLOW

if ($authToken) {
    # Test 38: Get AI Recommendations
    Test-Endpoint-Auth -Method GET -Endpoint "/recommendations" `
        -Description "Get AI Recommendations" `
        -Token $authToken
    
    # Test 39: Mood Check-in
    Test-Endpoint-Auth -Method POST -Endpoint "/mood-checkin" `
        -Body @{
            mood = "happy"
            intensity = 8
            notes = "Had a great day"
        } `
        -Description "Submit Mood Check-in" `
        -Token $authToken
    
    # Test 40: Get Mood History
    Test-Endpoint-Auth -Method GET -Endpoint "/mood-history" `
        -Description "Get Mood History" `
        -Token $authToken
}

# ==================== SECTION 10: CRISIS SUPPORT ====================

Write-Host "`n" + "="*60 -ForegroundColor $YELLOW
Write-Host "SECTION 10: CRISIS SUPPORT ENDPOINTS" -ForegroundColor $YELLOW
Write-Host "="*60 -ForegroundColor $YELLOW

if ($authToken) {
    # Test 41: Get Crisis Resources
    Test-Endpoint-Auth -Method GET -Endpoint "/crisis-resources" `
        -Description "Get Crisis Resources" `
        -Token $authToken
    
    # Test 42: Report Crisis
    Test-Endpoint-Auth -Method POST -Endpoint "/crisis-report" `
        -Body @{
            description = "Feeling suicidal"
            urgency = "high"
            location = "Home"
        } `
        -Description "Report Crisis" `
        -Token $authToken
}

# ==================== TEST SUMMARY ====================

Write-Host "`n" + "="*60 -ForegroundColor $YELLOW
Write-Host "TEST SUMMARY" -ForegroundColor $YELLOW
Write-Host "="*60 -ForegroundColor $YELLOW

Write-Host "`nTotal Tests: $totalTests" -ForegroundColor $CYAN
Write-Host "Passed: $passedTests" -ForegroundColor $GREEN
Write-Host "Failed: $failedTests" -ForegroundColor $RED

$passPercentage = if ($totalTests -gt 0) { [math]::Round(($passedTests / $totalTests) * 100, 2) } else { 0 }
Write-Host "Pass Rate: $passPercentage%" -ForegroundColor $(if ($passPercentage -eq 100) { $GREEN } else { $YELLOW })

if ($failedTests -eq 0) {
    Write-Host "✓ ALL TESTS PASSED! Backend is ready for production." -ForegroundColor $GREEN
} else {
    Write-Host "✗ Some tests failed. Please review the errors above." -ForegroundColor $RED
}

Write-Host "="*60 -ForegroundColor $YELLOW
