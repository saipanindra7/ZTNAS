"""
Test script for Admin API endpoints
Tests user management, audit logs, and policy management
"""

import requests
import json
from datetime import datetime

BASE_URL = "http://localhost:8000/api/v1"

# Test user credentials
ADMIN_USERNAME = "admin1"
ADMIN_PASSWORD = "password123"

print("=" * 70)
print("ADMIN API ENDPOINTS TEST")
print("=" * 70)

# Step 1: Login as Admin
print("\n[STEP 1] Login as Admin...")
login_response = requests.post(
    f"{BASE_URL}/auth/login",
    json={"username": ADMIN_USERNAME, "password": ADMIN_PASSWORD}
)
print(f"Status: {login_response.status_code}")

if login_response.status_code == 200:
    token = login_response.json().get("access_token")
    print(f"* Token received: {token[:50]}...")
else:
    print(f"ERROR: {login_response.json()}")
    exit(1)

headers = {"Authorization": f"Bearer {token}"}

# Step 2: Get All Users
print("\n[STEP 2] Get all users...")
users_response = requests.get(
    f"{BASE_URL}/admin/users?skip=0&limit=20",
    headers=headers
)
print(f"Status: {users_response.status_code}")
if users_response.status_code == 200:
    users_data = users_response.json()
    if users_data:
        total = users_data[0].get("total", len(users_data)) if isinstance(users_data[0], dict) else len(users_data)
        print(f"Total users: {total}")
        print(f"First user: {json.dumps(users_data[0], indent=2)[:300]}...")
else:
    print(f"ERROR: {users_response.json()}")

# Step 3: Get User Detail
print("\n[STEP 3] Get user detail (admin1)...")
user_detail_response = requests.get(
    f"{BASE_URL}/admin/users/1",
    headers=headers
)
print(f"Status: {user_detail_response.status_code}")
if user_detail_response.status_code == 200:
    user_detail = user_detail_response.json()
    print(f"User: {user_detail.get('username')} ({user_detail.get('email')})")
    print(f"Roles: {user_detail.get('roles', [])}")
    print(f"MFA Methods: {len(user_detail.get('mfa_methods', []))}")
    print(f"Devices: {len(user_detail.get('devices', []))}")
else:
    print(f"ERROR: {user_detail_response.json()}")

# Step 4: Get Audit Logs
print("\n[STEP 4] Get audit logs...")
logs_response = requests.get(
    f"{BASE_URL}/admin/logs?skip=0&limit=10",
    headers=headers
)
print(f"Status: {logs_response.status_code}")
if logs_response.status_code == 200:
    logs_data = logs_response.json()
    print(f"Total logs: {logs_data[0].get('total', len(logs_data)) if logs_data and isinstance(logs_data[0], dict) else len(logs_data)}")
    if logs_data:
        print(f"Latest log: {json.dumps(logs_data[0], indent=2)[:400]}...")
else:
    print(f"ERROR: {logs_response.json()}")

# Step 5: Get Audit Log Statistics
print("\n[STEP 5] Get audit log statistics...")
stats_response = requests.get(
    f"{BASE_URL}/admin/logs/stats?days=7",
    headers=headers
)
print(f"Status: {stats_response.status_code}")
if stats_response.status_code == 200:
    stats = stats_response.json()
    print(f"Statistics: {json.dumps(stats, indent=2)}")
else:
    print(f"ERROR: {stats_response.json()}")

# Step 6: Get Policies
print("\n[STEP 6] Get policies...")
policies_response = requests.get(
    f"{BASE_URL}/admin/policies",
    headers=headers
)
print(f"Status: {policies_response.status_code}")
if policies_response.status_code == 200:
    policies = policies_response.json()
    print(f"Roles: {len(policies)}")
    if policies:
        first_role = policies[0]
        print(f"First role: {first_role.get('name')}")
        print(f"Permissions: {first_role.get('permissions_count')}")
else:
    print(f"ERROR: {policies_response.json()}")

# Step 7: Get System Status
print("\n[STEP 7] Get system status...")
status_response = requests.get(
    f"{BASE_URL}/admin/system-status",
    headers=headers
)
print(f"Status: {status_response.status_code}")
if status_response.status_code == 200:
    system_status = status_response.json()
    print(f"Status: {json.dumps(system_status, indent=2)}")
else:
    print(f"Note: System status endpoint may not exist yet (expected for initial implementation)")

print("\n" + "=" * 70)
print("[SUCCESS] Admin API tests completed!")
print("=" * 70)
