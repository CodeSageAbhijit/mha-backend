#!/bin/bash
# Authentication & CORS Testing Script
# Usage: bash test_auth.sh http://localhost:8080

API_URL="${1:-http://localhost:8080}"
ORIGIN="http://localhost:3000"

echo "🔍 Testing Mental Health App Authentication"
echo "================================================"
echo "API URL: $API_URL"
echo "Origin: $ORIGIN"
echo "================================================"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test 1: CORS Preflight for Login
echo -e "\n${YELLOW}TEST 1: CORS Preflight for Login${NC}"
echo "Method: OPTIONS"
echo "Endpoint: /api/login"
response=$(curl -s -w "\n%{http_code}" -X OPTIONS "$API_URL/api/login" \
  -H "Origin: $ORIGIN" \
  -H "Access-Control-Request-Method: POST" \
  -H "Access-Control-Request-Headers: Content-Type,Authorization" \
  -v 2>&1)

status=$(echo "$response" | tail -1)
if [ "$status" = "200" ]; then
    echo -e "${GREEN}✅ CORS Preflight: PASSED (200)${NC}"
else
    echo -e "${RED}❌ CORS Preflight: FAILED ($status)${NC}"
fi

# Test 2: Login with Valid Credentials
echo -e "\n${YELLOW}TEST 2: Login with Valid Credentials${NC}"
response=$(curl -s -X POST "$API_URL/api/login" \
  -H "Content-Type: application/json" \
  -H "Origin: $ORIGIN" \
  -d '{
    "username": "w@gmail.com",
    "password": "123456",
    "role": "user"
  }')

status=$(echo "$response" | grep -o '"success":true' || echo "failed")
if [[ $status == *"success"* ]]; then
    echo -e "${GREEN}✅ Login Valid Credentials: PASSED${NC}"
    echo "Response: $response" | head -c 200
    echo "..."
else
    echo -e "${RED}❌ Login Valid Credentials: FAILED${NC}"
    echo "Response: $response"
fi

# Test 3: Login with Invalid Credentials
echo -e "\n${YELLOW}TEST 3: Login with Invalid Credentials${NC}"
response=$(curl -s -X POST "$API_URL/api/login" \
  -H "Content-Type: application/json" \
  -H "Origin: $ORIGIN" \
  -d '{
    "username": "wrong@gmail.com",
    "password": "wrongpass",
    "role": "user"
  }')

status=$(echo "$response" | grep -o '"success":false' || echo "passed")
if [[ $status == *"success"* ]]; then
    echo -e "${GREEN}✅ Login Invalid Credentials: PASSED (correctly rejected)${NC}"
else
    echo -e "${YELLOW}⚠️  Login Invalid Credentials: Check response${NC}"
    echo "Response: $response"
fi

# Test 4: CORS Preflight for Registration
echo -e "\n${YELLOW}TEST 4: CORS Preflight for Registration${NC}"
response=$(curl -s -w "\n%{http_code}" -X OPTIONS "$API_URL/api/register" \
  -H "Origin: $ORIGIN" \
  -H "Access-Control-Request-Method: POST" \
  -H "Access-Control-Request-Headers: Content-Type" \
  -v 2>&1)

status=$(echo "$response" | tail -1)
if [ "$status" = "200" ]; then
    echo -e "${GREEN}✅ Registration CORS Preflight: PASSED (200)${NC}"
else
    echo -e "${RED}❌ Registration CORS Preflight: FAILED ($status)${NC}"
fi

# Test 5: Health Check
echo -e "\n${YELLOW}TEST 5: Backend Health Check${NC}"
response=$(curl -s "$API_URL/health" 2>/dev/null || echo '{"status":"unreachable"}')
if [[ $response == *"ok"* ]] || [[ $response == *"operational"* ]]; then
    echo -e "${GREEN}✅ Backend Health: PASSED${NC}"
else
    echo -e "${YELLOW}⚠️  Backend Health: Check manually${NC}"
    echo "Response: $response"
fi

# Test 6: Check CORS Headers
echo -e "\n${YELLOW}TEST 6: CORS Headers in Response${NC}"
headers=$(curl -s -I -X OPTIONS "$API_URL/api/login" \
  -H "Origin: $ORIGIN" \
  -H "Access-Control-Request-Method: POST")

if echo "$headers" | grep -q "Access-Control-Allow-Origin"; then
    echo -e "${GREEN}✅ CORS Headers Present: PASSED${NC}"
    echo "$headers" | grep "Access-Control"
else
    echo -e "${RED}❌ CORS Headers: NOT FOUND${NC}"
fi

echo -e "\n================================================"
echo "✅ Authentication Testing Complete"
echo "================================================"

# Summary
echo -e "\n${YELLOW}Summary${NC}"
echo "If all tests passed, your authentication should work!"
echo ""
echo "Next steps:"
echo "1. Try login in web app"
echo "2. Check browser DevTools Network tab"
echo "3. Verify OPTIONS request returns 200"
echo "4. Check POST request succeeds"
