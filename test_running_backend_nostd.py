#!/usr/bin/env python3
"""
Test login against the running backend server - using stdlib only
"""

import urllib.request
import urllib.error
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
    response = urllib.request.urlopen(f"{API_URL}/health", timeout=5)
    print(f"Backend health check: {response.status}")
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
    req = urllib.request.Request(
        f"{API_URL}/auth/register",
        data=json.dumps(register_data).encode('utf-8'),
        headers={'Content-Type': 'application/json'},
        method='POST'
    )
    response = urllib.request.urlopen(req, timeout=5)
    print(f"Registration response: {response.status}")
    body = response.read().decode('utf-8')
    print(f"Registration result: {json.loads(body)}")
except urllib.error.HTTPError as e:
    print(f"Registration HTTP error {e.code}: {e.read().decode('utf-8')}")
except Exception as e:
    print(f"ERROR during registration: {e}")

# Step 3: Try to login
print(f"\n[3] Attempting login with same credentials...")
login_data = {
    "username": TEST_USERNAME,
    "password": TEST_PASSWORD
}

try:
    req = urllib.request.Request(
        f"{API_URL}/auth/login",
        data=json.dumps(login_data).encode('utf-8'),
        headers={'Content-Type': 'application/json'},
        method='POST'
    )
    response = urllib.request.urlopen(req, timeout=5)
    print(f"Login response: {response.status}")
    body = response.read().decode('utf-8')
    login_result = json.loads(body)
    print("LOGIN SUCCESSFUL!")
    print(f"Access token: {login_result.get('access_token', 'MISSING')[:50]}...")
    
except urllib.error.HTTPError as e:
    print(f"Login HTTP error {e.code}")
    body = e.read().decode('utf-8')
    print(f"Error response: {body}")
except Exception as e:
    print(f"ERROR during login: {e}")

# Step 4: Check debug endpoints
print(f"\n[4] Checking users in database...")
try:
    response = urllib.request.urlopen(f"{API_URL}/auth/debug/users", timeout=5)
    body = response.read().decode('utf-8')
    data = json.loads(body)
    print(f"Total users: {data.get('total_users', 0)}")
    if data.get('users'):
        print("Users found:")
        for user in data['users'][:5]:  # Show first 5 users
            print(f"  - {user['username']} (ID:{user['id']}, active:{user['is_active']}, locked:{user['is_locked']})")
except Exception as e:
    print(f"ERROR: {e}")

# Step 5: Manual password verification
print(f"\n[5] Manual password verification...")
try:
    response = urllib.request.urlopen(
        f"{API_URL}/auth/debug/test-login/{TEST_USERNAME}/{TEST_PASSWORD}",
        timeout=5
    )
    body = response.read().decode('utf-8')
    result = json.loads(body)
    print(f"Test login result: {json.dumps(result, indent=2)}")
except Exception as e:
    print(f"ERROR: {e}")

print("\n" + "=" * 70)
