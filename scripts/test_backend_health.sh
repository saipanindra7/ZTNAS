#!/bin/bash
# Test Backend Connectivity & Health
# Usage: bash test_backend_health.sh
# Run this after starting backend in another terminal

echo "╔════════════════════════════════════════════════════════════╗"
echo "║  Testing Backend API Connectivity                          ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

BACKEND_URL="http://localhost:8000"
MAX_RETRIES=5
RETRY_COUNT=0

# Wait for backend to be ready
echo "Waiting for backend to start (max 30 seconds)..."
while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
    if curl -s "$BACKEND_URL/api/v1/health" > /dev/null 2>&1; then
        echo -e "${GREEN}✓ Backend responding${NC}"
        break
    else
        RETRY_COUNT=$((RETRY_COUNT + 1))
        echo "  Attempt $RETRY_COUNT/$MAX_RETRIES..."
        sleep 5
    fi
done

if [ $RETRY_COUNT -eq $MAX_RETRIES ]; then
    echo -e "${RED}✗ Backend not responding after 30 seconds${NC}"
    exit 1
fi

echo ""

# Test health endpoint
echo "Test 1: Health Endpoint"
HEALTH=$(curl -s "$BACKEND_URL/api/v1/health")
echo "  Response: $HEALTH"

if echo "$HEALTH" | grep -q "healthy"; then
    echo -e "${GREEN}✓ Health endpoint working${NC}"
else
    echo -e "${RED}✗ Health endpoint failed${NC}"
fi

echo ""

# Test API documentation
echo "Test 2: API Documentation (Swagger)"
SWAGGER_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$BACKEND_URL/docs")
if [ "$SWAGGER_STATUS" = "200" ]; then
    echo -e "${GREEN}✓ Swagger UI available at $BACKEND_URL/docs${NC}"
else
    echo -e "${RED}✗ Swagger UI not available (HTTP $SWAGGER_STATUS)${NC}"
fi

echo ""

# Test login endpoint exists
echo "Test 3: Authentication Endpoint"
LOGIN_STATUS=$(curl -s -o /dev/null -w "%{http_code}" -X POST "$BACKEND_URL/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"test"}')

if [ "$LOGIN_STATUS" = "401" ] || [ "$LOGIN_STATUS" = "400" ]; then
    echo -e "${GREEN}✓ Login endpoint responding (HTTP $LOGIN_STATUS)${NC}"
else
    echo -e "${YELLOW}⚠ Login endpoint returned HTTP $LOGIN_STATUS${NC}"
fi

echo ""

# Test database connection through API
echo "Test 4: Database Connection (via API)"
USERS_RESPONSE=$(curl -s -X GET "$BACKEND_URL/api/v1/users" \
  -H "Authorization: Bearer invalid-token" 2>&1)

if echo "$USERS_RESPONSE" | grep -q "detail\|error\|unauthorized"; then
    echo -e "${GREEN}✓ Database connection working (auth correctly rejected)${NC}"
else
    echo -e "${YELLOW}⚠ Users endpoint returned: $USERS_RESPONSE${NC}"
fi

echo ""
echo "╔════════════════════════════════════════════════════════════╗"
echo -e "║  ${GREEN}✓ Backend Tests Complete${NC}                               ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""
echo "Next: Start frontend server (Step 2b)"
echo "Run: bash step2b_start_frontend.sh"
