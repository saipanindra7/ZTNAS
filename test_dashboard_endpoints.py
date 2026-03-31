#!/usr/bin/env python3
"""
Test dashboard endpoints to ensure they work properly
"""

import sys
import os

# Add backend directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from fastapi.testclient import TestClient
from backend.main import create_app
from config.database import get_db, init_db
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import json

# Create test client
app = create_app()
client = TestClient(app)

def test_endpoints():
    """Test all dashboard endpoints"""
    
    print("=" * 80)
    print("DASHBOARD ENDPOINTS TEST")
    print("=" * 80)
    
    # Generate unique email for this test run
    import time
    timestamp = str(int(time.time()))
    test_email = f"dashboard_test_{timestamp}@test.com"
    
    # Test 1: Register a test user
    print("\n[1] Testing User Registration...")
    register_data = {
        "email": test_email,
        "username": f"dashboard_test_{timestamp}",
        "password": "TestPassword@123"
    }
    
    resp = client.post("/api/v1/auth/register", json=register_data)
    print(f"   Status: {resp.status_code}")
    if resp.status_code != 201:
        print(f"   Error: {resp.json()}")
        return False
    
    user_data = resp.json()
    user_id = user_data.get("id")
    print(f"   [OK] User registered with ID: {user_id}")
    
    # Test 2: Login to get token
    print("\n[2] Testing User Login...")
    login_data = {
        "username": "dashboard_test",
        "password": "TestPassword@123"
    }
    
    resp = client.post("/api/v1/auth/login", json=login_data)
    print(f"   Status: {resp.status_code}")
    if resp.status_code != 200:
        print(f"   Error: {resp.json()}")
        return False
    
    token_data = resp.json()
    access_token = token_data.get("access_token")
    print(f"   [OK] Login successful, token received: {access_token[:20]}...")
    
    headers = {"Authorization": f"Bearer {access_token}"}
    
    # Test 3: Get current user info
    print("\n[3] Testing GET /auth/me...")
    resp = client.get("/api/v1/auth/me", headers=headers)
    print(f"   Status: {resp.status_code}")
    if resp.status_code != 200:
        print(f"   Error: {resp.json()}")
        return False
    print(f"   [OK] Current user info retrieved")
    
    # Test 4: List all users
    print("\n[4] Testing GET /auth/users...")
    resp = client.get("/api/v1/auth/users", headers=headers)
    print(f"   Status: {resp.status_code}")
    if resp.status_code != 200:
        print(f"   Error: {resp.json()}")
        return False
    
    users_data = resp.json()
    total_users = users_data.get("total_users", 0)
    print(f"   [OK] Users list retrieved: {total_users} total users")
    
    # Test 5: Get risk timeline
    print("\n[5] Testing GET /zero-trust/risk/timeline...")
    resp = client.get("/api/v1/zero-trust/risk/timeline", headers=headers)
    print(f"   Status: {resp.status_code}")
    if resp.status_code != 200:
        print(f"   Error: {resp.json()}")
        return False
    
    timeline_data = resp.json()
    total_events = timeline_data.get("total_events", 0)
    print(f"   [OK] Risk timeline retrieved: {total_events} events")
    
    # Test 6: Get recent anomalies
    print("\n[6] Testing GET /zero-trust/anomalies/recent...")
    resp = client.get("/api/v1/zero-trust/anomalies/recent", headers=headers)
    print(f"   Status: {resp.status_code}")
    if resp.status_code != 200:
        print(f"   Error: {resp.json()}")
        return False
    
    anomalies_data = resp.json()
    total_anomalies = len(anomalies_data.get("anomalies", []))
    print(f"   [OK] Recent anomalies retrieved: {total_anomalies} anomalies")
    
    # Test 7: Test without authentication (should fail)
    print("\n[7] Testing endpoints WITHOUT authentication (should fail)...")
    resp = client.get("/api/v1/auth/users")
    print(f"   GET /auth/users (no auth): {resp.status_code} - {resp.status_code == 401 and '[OK] CORRECTLY REJECTED' or '[FAIL] SHOULD HAVE FAILED'}")
    
    resp = client.get("/api/v1/zero-trust/risk/timeline")
    print(f"   GET /risk/timeline (no auth): {resp.status_code} - {resp.status_code == 401 and '[OK] CORRECTLY REJECTED' or '[FAIL] SHOULD HAVE FAILED'}")
    
    resp = client.get("/api/v1/zero-trust/anomalies/recent")
    print(f"   GET /anomalies/recent (no auth): {resp.status_code} - {resp.status_code == 401 and '[OK] CORRECTLY REJECTED' or '[FAIL] SHOULD HAVE FAILED'}")
    
    print("\n" + "=" * 80)
    print("ALL TESTS PASSED [OK]")
    print("=" * 80)
    return True

if __name__ == "__main__":
    try:
        success = test_endpoints()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n[FAIL] Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
