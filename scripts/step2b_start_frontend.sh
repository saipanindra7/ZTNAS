#!/bin/bash
# STEP 2b: Frontend Server Startup
# Purpose: Start HTTP server for dashboard and UI
# Usage: bash step2b_start_frontend.sh

echo "╔════════════════════════════════════════════════════════════╗"
echo "║  STEP 2b: Frontend Server Startup                          ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Step 1: Check directory
echo "Step 1: Verifying frontend directory..."
if [ ! -d "static" ]; then
    echo "✗ static directory not found. Navigate to frontend:"
    echo "  cd d:\\projects\\ztnas\\frontend"
    exit 1
else
    echo -e "${GREEN}✓ Frontend directory correct${NC}"
    echo "  Files: $(ls -1 static | wc -l) files in static/"
fi

echo ""

# Step 2: Check dependencies
echo "Step 2: Python HTTP Server (built-in)..."
if command -v python &> /dev/null; then
    echo -e "${GREEN}✓ Python available${NC}"
else
    echo "✗ Python not found"
    exit 1
fi

echo ""

# Step 3: Start frontend
echo "Step 3: Starting production HTTP server on port 5500..."
echo "  Dashboard: http://localhost:5500"
echo "  Login: http://localhost:5500"
echo ""
echo -e "${YELLOW}Starting server... Press Ctrl+C to stop${NC}"
echo ""

# Use production-ready simple server
python ../frontend/serve_simple.py

# If we get here, server stopped
echo ""
echo "Frontend server stopped."
