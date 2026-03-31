#!/usr/bin/env python3
"""
Test login against the running backend server
"""

import requests
import json
import sys
import time

print("=" * 70)
print("TESTING LOGIN AGAINST RUNNING BACKEND")
print("=" * 70)

API_URL = "http://localhost:8000/api/v1"
TEST_USERNAME = "testdiag"
TEST_PASSWORD = "TestDiag@123"

# Step 1: Check if backend is responding
print("\n[1] Checking if backend is running...")
try:
    response = requests.get(f"{API_URL}/health", timeout=5)
    print(f"Backend health check: {response.status_code}")
except Exception as e:
    print(f"ERROR: Cannot connect to backend: {e}")
    print("Make sure backend is running on port 8000")
    sys.exit(1)

# Step 2: First register a fresh test user
print(f"\n[2] Registering test user '{TEST_USERNAME}'...")
register_data = {
    "email": f"test_{int(time.time())}@example.com",
    "username": TEST_USERNAME,
    "password": TEST_PASSWORD
}

try:
    response = requests.post(
        f"{API_URL}/auth/register",
        json=register_data,
        timeout=5
    )
    print(f"Registration response: {response.status_code}")
    if response.status_code in [201, 200]:
        print(f"Registration successful: {json.dumps(response.json(), indent=2)}")
    else:
        print(f"Registration failed: {response.text}")
except Exception as e:
    print(f"ERROR during registration: {e}")

# Step 3: Try to login
print(f"\n[3] Attempting login with same credentials...")
login_data = {
    "username": TEST_USERNAME,
    "password": TEST_PASSWORD
}

try:
    response = requests.post(
        f"{API_URL}/auth/login",
        json=login_data,
        timeout=5
    )
    print(f"Login response: {response.status_code}")
    
    if response.status_code == 200:
        print("LOGIN SUCCESSFUL!")
        print(json.dumps(response.json(), indent=2))
    else:
        print(f"Login failed with status {response.status_code}")
        print(f"Response: {response.text}")
        
except Exception as e:
    print(f"ERROR during login: {e}")

# Step 4: Check debug endpoints
print(f"\n[4] Checking debug endpoints...")
print(f"\nUsers in database:")
try:
    response = requests.get(f"{API_URL}/auth/debug/users", timeout=5)
    if response.status_code == 200:
        data = response.json()
        print(f"Total users: {data.get('total_users', 0)}")
        if data.get('users'):
            for user in data['users']:
                print(f"  - {user['username']} (active: {user['is_active']}, locked: {user['is_locked']})")
except Exception as e:
    print(f"ERROR: {e}")

# Step 5: Manual password verification
print(f"\n[5] Manual password verification test...")
try:
    response = requests.get(
        f"{API_URL}/auth/debug/test-login/{TEST_USERNAME}/{TEST_PASSWORD}",
        timeout=5
    )
    if response.status_code == 200:
        print(json.dumps(response.json(), indent=2))
except Exception as e:
    print(f"ERROR: {e}")

print("\n" + "=" * 70)
