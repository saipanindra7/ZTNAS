#!/bin/bash
# STEP 2: Backend Server Startup
# Purpose: Start FastAPI backend and verify all endpoints are responding
# Usage: bash step2_start_backend.sh

echo "╔════════════════════════════════════════════════════════════╗"
echo "║  STEP 2: Backend Server Startup                            ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Step 2a: Check if running in correct directory
echo "Step 2a: Verifying directory structure..."
if [ ! -f "main.py" ]; then
    echo "✗ main.py not found. Navigate to backend directory:"
    echo "  cd d:\\projects\\ztnas\\backend"
    exit 1
else
    echo -e "${GREEN}✓ Backend directory correct${NC}"
fi

echo ""

# Step 2b: Check Python version
echo "Step 2b: Checking Python version..."
PYTHON_VERSION=$(python --version 2>&1)
echo "  $PYTHON_VERSION"

if ! echo "$PYTHON_VERSION" | grep -q "3.1[1-9]"; then
    echo -e "${YELLOW}⚠ Python 3.11+ recommended. Continuing anyway...${NC}"
fi

echo ""

# Step 2c: Check dependencies
echo "Step 2c: Checking FastAPI dependency..."
if python -c "import fastapi; print(fastapi.__version__)" &> /dev/null; then
    FASTAPI_VERSION=$(python -c "import fastapi; print(fastapi.__version__)")
    echo -e "${GREEN}✓ FastAPI $FASTAPI_VERSION installed${NC}"
else
    echo -e "${YELLOW}⚠ FastAPI not installed. Installing...${NC}"
    pip install fastapi uvicorn sqlalchemy psycopg2-binary pydantic
fi

echo ""

# Step 2d: Start backend
echo "Step 2d: Starting FastAPI backend on port 8000..."
echo "  Command: python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload"
echo ""
echo -e "${YELLOW}Starting server... Press Ctrl+C to stop${NC}"
echo ""

python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload

# If we get here, server stopped
echo ""
echo "Backend server stopped."
