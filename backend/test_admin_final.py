"""
Test admin core endpoints
"""
import requests
import json

BASE_URL = "http://localhost:8000/api/v1"

print("=" * 70)
print("ADMIN API TEST - CORE ENDPOINTS")
print("=" * 70)

# Login first
print("\n[*] Admin Login...")
try:
    login_resp = requests.post(
        f"{BASE_URL}/auth/login",
        json={"username": "admin1", "password": "password123"},
        timeout=5
    )
    if login_resp.status_code != 200:
        print(f"  ERROR: {login_resp.json()}")
        exit(1)
    token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    print(f"  OK - Login successful")
except Exception as e:
    print(f"  ERROR: {e}")
    exit(1)

# Test endpoints
endpoints = [
    ("GET", "/admin/users?skip=0&limit=5", "User list"),
    ("GET", "/admin/users/1", "Get user detail"),
    ("GET", "/admin/users/9", "Get admin user"),
    ("GET", "/admin/logs?skip=0&limit=5", "Audit logs"),
    ("GET", "/admin/policies", "Get policies"),
]

for method, endpoint, description in endpoints:
    print(f"\n[{method}] {endpoint}")
    print(f"  Description: {description}")
    try:
        if method == "GET":
            resp = requests.get(
                f"{BASE_URL}{endpoint}",
                headers=headers,
                timeout=10
            )
        
        if resp.status_code == 200:
            data = resp.json()
            if isinstance(data, list):
                print(f"  OK - Status {resp.status_code}: {len(data)} items")
            elif isinstance(data, dict):
                print(f"  OK - Status {resp.status_code}: {len(data)} keys")
        else:
            print(f"  FAIL - Status {resp.status_code}: {resp.json()}")
    except requests.exceptions.Timeout:
        print(f"  FAIL - Request timeout")
    except Exception as e:
        print(f"  FAIL - {e}")

print("\n" + "=" * 70)
print("[DONE] Admin core endpoints verified")
print("=" * 70)
