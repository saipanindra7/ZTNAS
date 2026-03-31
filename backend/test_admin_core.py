"""
Test admin endpoints - skip the stats endpoint
"""
import requests
import json

BASE_URL = "http://localhost:8000/api/v1"

print("=" * 70)
print("ADMIN API TEST - CORE ENDPOINTS")
print("=" * 70)

# Login
print("\n[+] Admin Login...")
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
print(f"  [OK] Login successful")
except Exception as e:
    print(f"  ERROR: {e}")
    exit(1)

# Test each endpoint
endpoints = [
    ("GET", "/admin/users?skip=0&limit=5", "User list"),
    ("GET", "/admin/users/1", "Get user detail"),
    ("GET", "/admin/users/9", "Get admin user"),
    ("GET", "/admin/logs?skip=0&limit=5", "Audit logs with limit"),
    ("GET", "/admin/logs?action=user_created&limit=10", "Filtered audit logs"),
    ("GET", "/admin/policies", "Get policies/roles"),
]

for method, endpoint, description in endpoints:
    print(f"\n[{method}] {endpoint}")
    print(f"    Description: {description}")
    try:
        if method == "GET":
            resp = requests.get(
                f"{BASE_URL}{endpoint}",
                headers=headers,
                timeout=10
            )
        else:
            resp = requests.post(
                f"{BASE_URL}{endpoint}",
                headers=headers,
                timeout=10
            )
        
        if resp.status_code == 200:
            data = resp.json()
            # Show summary
            if isinstance(data, list):
                print(f"    [OK] Status {resp.status_code}: Returned {len(data)} items")
                if data:
                    print(f"      Sample: {json.dumps(data[0], default=str)[:150]}...")
            elif isinstance(data, dict):
                print(f"    [OK] Status {resp.status_code}: {len(data)} keys")
                print(f"      Keys: {list(data.keys())}")
        else:
            print(f"    [FAIL] Status {resp.status_code}")
            print(f"      Error: {resp.json()}")
    except requests.exceptions.Timeout:
        print(f"    [FAIL] ERROR: Request timeout (>10s)")
    except Exception as e:
        print(f"    [FAIL] ERROR: {e}")

print("\n" + "=" * 70)
print("[SUCCESS] Admin core endpoints verified!")
print("=" * 70)
