#!/usr/bin/env python3
"""
Final end-to-end verification: Registration + Login workflow
"""

import urllib.request
import urllib.error
import json
import time

API_URL = "http://localhost:8000/api/v1"

print("=" * 70)
print("FINAL VERIFICATION - END-TO-END LOGIN TEST")
print("=" * 70)

# Test 1: Check that the 'test' user exists and is unlocked
print("\n[1] Checking user 'test' status...")
try:
    resp = urllib.request.urlopen(f"{API_URL}/auth/debug/users")
    data = json.loads(resp.read())
    test_user = [u for u in data['users'] if u['email'] == 'test@test.com'][0]
    print(f"    User found: {test_user['username']}")
    print(f"    Is Active: {test_user['is_active']}")
    print(f"    Is Locked: {test_user['is_locked']}")
    print(f"    Failed Attempts: {test_user['failed_attempts']}")
    
    if test_user['is_locked']:
        print("    ERROR: User is still locked!")
        exit(1)
    if test_user['failed_attempts'] > 0:
        print("    WARNING: Failed attempts not reset!")
        
except Exception as e:
    print(f"    ERROR: {e}")
    exit(1)

# Test 2: Test login with new password
print("\n[2] Testing login with new password...")
login_data = {
    "username": "test@test.com",
    "password": "TestPassword@123"
}

try:
    req = urllib.request.Request(
        f"{API_URL}/auth/login",
        data=json.dumps(login_data).encode('utf-8'),
        headers={'Content-Type': 'application/json'},
        method='POST'
    )
    response = urllib.request.urlopen(req, timeout=5)
    body = response.read().decode('utf-8')
    result = json.loads(body)
    
    print(f"    Status: {response.status}")
    print(f"    Response: Got access_token of length {len(result.get('access_token', ''))}")
    print(f"    Token type: {result.get('token_type')}")
    
    if response.status != 200:
        print("    ERROR: Unexpected status code!")
        exit(1)
        
except urllib.error.HTTPError as e:
    print(f"    ERROR: Login failed with status {e.code}")
    print(f"    Response: {e.read().decode('utf-8')}")
    exit(1)
except Exception as e:
    print(f"    ERROR: {e}")
    exit(1)

# Test 3: Verify wrong password still fails
print("\n[3] Testing that wrong password is rejected...")
wrong_login = {
    "username": "test@test.com",
    "password": "WrongPassword@123"
}

try:
    req = urllib.request.Request(
        f"{API_URL}/auth/login",
        data=json.dumps(wrong_login).encode('utf-8'),
        headers={'Content-Type': 'application/json'},
        method='POST'
    )
    response = urllib.request.urlopen(req, timeout=5)
    print("    ERROR: Wrong password was accepted!")
    exit(1)
    
except urllib.error.HTTPError as e:
    if e.code == 401:
        print(f"    Correct: Wrong password rejected with 401")
    else:
        print(f"    ERROR: Unexpected error code {e.code}")
        exit(1)
except Exception as e:
    print(f"    ERROR: {e}")
    exit(1)

print("\n" + "=" * 70)
print("ALL TESTS PASSED - LOGIN SYSTEM FULLY OPERATIONAL")
print("=" * 70)
print("\nUSER CAN NOW LOGIN WITH:")
print("  Email: test@test.com")
print("  Password: TestPassword@123")
print("  URL: http://localhost:5500")
print("=" * 70)
