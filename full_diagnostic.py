#!/usr/bin/env python3
"""
Comprehensive diagnostic to understand the login issue
"""

import urllib.request
import urllib.error
import json
import time

API_URL = "http://localhost:8000/api/v1"

print("=" * 70)
print("COMPREHENSIVE LOGIN DIAGNOSTIC")
print("=" * 70)

# Step 1: See what users exist in the running database
print("\n[STEP 1] Checking users in live database...")
try:
    response = urllib.request.urlopen(f"{API_URL}/auth/debug/users", timeout=5)
    body = response.read().decode('utf-8')
    data = json.loads(body)
    print(f"Total users in database: {data.get('total_users', 0)}")
    if data.get('users'):
        print("\nUser list:")
        for user in data['users']:
            print(f"  - {user['username']:<20} | email={user['email']:<30} | active={user['is_active']} | locked={user['is_locked']}")
    else:
        print("No users in database!")
except Exception as e:
    print(f"ERROR: {e}")

# Step 2: Register a new test user
print("\n[STEP 2] Registering new test user...")
unique_id = int(time.time() * 1000) % 10000
test_email = f"testreg{unique_id}@example.com"
test_username = f"testreg{unique_id}"
test_password = "TestReg@12345"

register_data = {
    "email": test_email,
    "username": test_username,
    "password": test_password
}

print(f"Registration data:")
print(f"  User: {test_username}")
print(f"  Email: {test_email}")
print(f"  Password: {test_password}")

try:
    req = urllib.request.Request(
        f"{API_URL}/auth/register",
        data=json.dumps(register_data).encode('utf-8'),
        headers={'Content-Type': 'application/json'},
        method='POST'
    )
    response = urllib.request.urlopen(req, timeout=5)
    body = response.read().decode('utf-8')
    result = json.loads(body)
    print(f"Registration response (201/200): {result}")
except urllib.error.HTTPError as e:
    body = e.read().decode('utf-8')
    print(f"Registration failed ({e.code}): {body}")
except Exception as e:
    print(f"ERROR: {e}")

# Step 3: Try to login with that user
print(f"\n[STEP 3] Attempting login with '{test_username}'...")

login_data = {
    "username": test_username,
    "password": test_password
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
    print(f"LOGIN SUCCESSFUL!")
    print(f"Token type: {result.get('token_type')}")
    print(f"Access token length: {len(result.get('access_token', ''))}")
except urllib.error.HTTPError as e:
    print(f"LOGIN FAILED ({e.code})")
    try:
        body = e.read().decode('utf-8')
        error_detail = json.loads(body).get('detail')
        print(f"Error: {error_detail}")
    except:
        pass
except Exception as e:
    print(f"ERROR: {e}")

# Step 4: Check if user was registered
print(f"\n[STEP 4] Checking if user exists in database after login attempt...")
try:
    response = urllib.request.urlopen(f"{API_URL}/auth/debug/users", timeout=5)
    body = response.read().decode('utf-8')
    data = json.loads(body)
    
    found = False
    for user in data.get('users', []):
        if user['username'] == test_username:
            print(f"User found! Details:")
            print(f"  Username: {user['username']}")
            print(f"  Email: {user['email']}")
            print(f"  Active: {user['is_active']}")
            print(f"  Locked: {user['is_locked']}")
            print(f"  Failed attempts: {user['failed_attempts']}")
            print(f"  Password hash preview: {user['password_hash_preview']}")
            found = True
            break
    
    if not found:
        print(f"User '{test_username}' NOT found in database!")
        print("This means registration was not successful")
        
except Exception as e:
    print(f"ERROR: {e}")

print("\n" + "=" * 70)
print("ANALYSIS:")
print("=" * 70)
print("""
If the user is NOT in the database after attempting to login, then:
1. Frontend registration form is not successfully registering users
2. Check frontend console (F12) for any errors during registration
3. Check network tab to see if registration request succeeded

If the user IS in the database but login failed:
1. Password verification is broken (unlikely, tested earlier)
2. User account is locked
3. User is marked inactive

If login succeeded:
1. The authentication system is working correctly
2. The issue is with the user's specific credentials or account status
""")
