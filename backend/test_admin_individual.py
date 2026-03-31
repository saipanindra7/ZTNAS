"""
Test admin endpoints one by one with error handling and timeouts
"""
import requests
import json

BASE_URL = "http://localhost:8000/api/v1"

print("=" * 70)
print("ADMIN API TEST - INDIVIDUAL ENDPOINTS")
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
    print(f"  ✓ Login successful")
except Exception as e:
    print(f"  ERROR: {e}")
    exit(1)

# Test each endpoint
endpoints = [
    ("GET", "/admin/users?skip=0&limit=5", None),
    ("GET", "/admin/users/1", None),
    ("GET", "/admin/logs?skip=0&limit=5", None),
    ("GET", "/admin/logs/stats?days=7", None),
    ("GET", "/admin/policies", None),
]

for method, endpoint, data in endpoints:
    print(f"\n[ENDPOINT] {method} {endpoint}")
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
                json=data,
                timeout=10
            )
        
        print(f"  Status: {resp.status_code}")
        
        if resp.status_code == 200:
            data = resp.json()
            # Show summary
            if isinstance(data, list):
                print(f"  Items: {len(data)}")
            elif isinstance(data, dict):
                print(f"  Keys: {list(data.keys())[:5]}")
                # Show first few items if it's a list response
                for key in data.keys():
                    if isinstance(data[key], (list, dict)):
                        print(f"    {key}: {type(data[key]).__name__}")
            print(f"  ✓ OK")
        else:
            print(f"  Error: {resp.json()}")
    except requests.exceptions.Timeout:
        print(f"  ERROR: Request timeout")
    except Exception as e:
        print(f"  ERROR: {e}")

print("\n" + "=" * 70)
print("[DONE] Admin API endpoint test completed")
print("=" * 70)
