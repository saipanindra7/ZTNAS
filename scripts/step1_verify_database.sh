#!/bin/bash
# STEP 1: Database Connectivity Verification
# Purpose: Verify PostgreSQL is running and ZTNAS database is accessible
# Usage: bash step1_verify_database.sh

echo "╔════════════════════════════════════════════════════════════╗"
echo "║  STEP 1: Database Connectivity Verification                ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Step 1a: Check PostgreSQL version
echo "Step 1a: Checking PostgreSQL installation..."
if command -v psql &> /dev/null; then
    VERSION=$(psql --version)
    echo -e "${GREEN}✓ PostgreSQL installed: $VERSION${NC}"
else
    echo -e "${RED}✗ PostgreSQL not found. Install PostgreSQL 16+ first.${NC}"
    exit 1
fi

echo ""

# Step 1b: Check PostgreSQL service status
echo "Step 1b: Checking PostgreSQL service status..."
if pg_isready -h localhost -p 5432 -U ztnas_user -d ztnas_prod &> /dev/null; then
    echo -e "${GREEN}✓ PostgreSQL service running on localhost:5432${NC}"
else
    echo -e "${YELLOW}⚠ PostgreSQL not responding. Trying to start...${NC}"
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        sudo systemctl start postgresql 2>/dev/null
        sleep 2
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        brew services start postgresql@16 2>/dev/null || brew services start postgresql 2>/dev/null
        sleep 2
    fi
fi

echo ""

# Step 1c: Test database connectivity
echo "Step 1c: Testing database connectivity..."
RESULT=$(psql -U ztnas_user -d ztnas_prod -h localhost -c "SELECT COUNT(*) as user_count FROM users;" 2>&1)

if echo "$RESULT" | grep -q "ERROR"; then
    echo -e "${RED}✗ Connection failed${NC}"
    echo "Error: $RESULT"
    echo ""
    echo "Troubleshooting:"
    echo "1. Check database exists: psql -U postgres -l | grep ztnas_prod"
    echo "2. Check user exists: psql -U postgres -c \"\\\\du\" | grep ztnas_user"
    echo "3. Reset password: psql -U postgres -c \"ALTER USER ztnas_user WITH PASSWORD 'NewPassword123';\""
    exit 1
else
    USER_COUNT=$(echo "$RESULT" | tail -n 2 | head -n 1 | xargs)
    echo -e "${GREEN}✓ Database connected successfully${NC}"
    echo "  Users in database: $USER_COUNT"
fi

echo ""

# Step 1d: Verify database tables
echo "Step 1d: Verifying database structure..."
TABLES=$(psql -U ztnas_user -d ztnas_prod -h localhost -c "\dt" 2>&1 | grep -c "public")

if [ "$TABLES" -gt 0 ]; then
    echo -e "${GREEN}✓ Database tables found${NC}"
    psql -U ztnas_user -d ztnas_prod -h localhost -c "\dt" | grep "public"
else
    echo -e "${RED}✗ No tables found. Run migrations first.${NC}"
    exit 1
fi

echo ""

# Step 1e: Database size
echo "Step 1e: Database statistics..."
DB_SIZE=$(psql -U ztnas_user -d ztnas_prod -h localhost -c "SELECT pg_size_pretty(pg_database_size('ztnas_prod'));" | tail -n 2 | head -n 1)
echo "  Database size: $DB_SIZE"

echo ""
echo "╔════════════════════════════════════════════════════════════╗"
echo -e "║  ${GREEN}✓ STEP 1 COMPLETE - Database Ready${NC}                         ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""
echo "Next Step: Execute STEP 2 (Backend Server Startup)"
echo "Run: bash step2_start_backend.sh"
