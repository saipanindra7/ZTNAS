#!/usr/bin/env python3
"""Quick test registration and login"""
import httpx
import datetime

BASE_URL = "http://localhost:8000"

# Create unique test user
timestamp = int(datetime.datetime.now().timestamp())
username = f"deploy_test_{timestamp}"
password = "DeployTest@123"
email = f"{username}@test.com"

print("Testing Step 4: Authentication\n")

# Register
print(f"1. Registering new user: {username}")
reg_resp = httpx.post(
    f"{BASE_URL}/api/v1/auth/register",
    json={
        "username": username,
        "email": email,
        "password": password,
        "first_name": "Deploy",
        "last_name": "Test"
    }
)
print(f"   Status: {reg_resp.status_code}")
if reg_resp.status_code == 201:
    print(f"   [SUCCESS] User registered!")
    user_data = reg_resp.json()
    print(f"   User ID: {user_data.get('id')}")
else:
    print(f"   [ERROR] {reg_resp.json()}")

# Login
print(f"\n2. Attempting login with {username}")
login_resp = httpx.post(
    f"{BASE_URL}/api/v1/auth/login",
    json={
        "username": username,
        "password": password,
        "device_name": "Deployment Test"
    }
)
print(f"   Status: {login_resp.status_code}")
if login_resp.status_code == 200:
    print(f"   [SUCCESS] Login successful!")
    token_data = login_resp.json()
    print(f"   Access Token: {token_data['access_token'][:50]}...")
    print(f"   Token Type: {token_data.get('token_type')}")
    print(f"   Expires In: {token_data.get('expires_in')} seconds")
    print(f"\n[PASSED] STEP 4: Authentication is working!")
else:
    print(f"   [ERROR] {login_resp.json()}")
    print(f"\n[FAILED] STEP 4: Authentication test failed")
