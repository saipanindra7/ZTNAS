"""Quick test of student API endpoints"""
import requests
import json

BASE_URL = "http://localhost:8000/api/v1"

print("=" * 60)
print("ZTNAS Student API Test")
print("=" * 60)

# Test 1: Login
print("\n[TEST] Login as student1...")
login_data = {"username": "student1", "password": "password123"}
resp = requests.post(f"{BASE_URL}/auth/login", json=login_data, timeout=5)
print(f"Status: {resp.status_code}")
print(f"Response: {resp.text[:200]}")

if resp.status_code == 200:
    token_data = resp.json()
    access_token = token_data.get("access_token")
    print(f"* Token received: {access_token[:30]}...")
    
    # Test 2: Get attendance
    print("\n[TEST 2] Get attendance records...")
    headers = {"Authorization": f"Bearer {access_token}"}
    resp2 = requests.get(f"{BASE_URL}/student/attendance", headers=headers, timeout=5)
    print(f"Status: {resp2.status_code}")
    data = resp2.json()
    print(f"Records count: {len(data) if isinstance(data, list) else 'ERROR'}")
    if isinstance(data, list) and len(data) > 0:
        print(f"Sample: {json.dumps(data[0], indent=2)}")
    
    # Test 3: Get attendance summary
    print("\n[TEST 3] Get attendance summary...")
    resp3 = requests.get(f"{BASE_URL}/student/attendance/summary", headers=headers, timeout=5)
    print(f"Status: {resp3.status_code}")
    print(f"Summary: {json.dumps(resp3.json(), indent=2)}")
    
    # Test 4: Get marks
    print("\n[TEST 4] Get marks...")
    resp4 = requests.get(f"{BASE_URL}/student/marks", headers=headers, timeout=5)
    print(f"Status: {resp4.status_code}")
    data = resp4.json()
    print(f"Records count: {len(data) if isinstance(data, list) else 'ERROR'}")
    if isinstance(data, list) and len(data) > 0:
        print(f"Sample: {json.dumps(data[0], indent=2)}")
    
    # Test 5: Get fees
    print("\n[TEST 5] Get fees summary...")
    resp5 = requests.get(f"{BASE_URL}/student/fees/summary", headers=headers, timeout=5)
    print(f"Status: {resp5.status_code}")
    print(f"Summary: {json.dumps(resp5.json(), indent=2)}")
    
    # Test 6: Dashboard summary
    print("\n[TEST 6] Get dashboard summary...")
    resp6 = requests.get(f"{BASE_URL}/student/dashboard-summary", headers=headers, timeout=5)
    print(f"Status: {resp6.status_code}")
    print(f"Summary: {json.dumps(resp6.json(), indent=2)}")
    
else:
    print(f"* Login failed. Available endpoints:")
    print("Check the API documentation.")

print("\n" + "=" * 60)
print("Test complete!")
print("=" * 60)
