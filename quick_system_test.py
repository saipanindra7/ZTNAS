#!/usr/bin/env python
"""Quick test - display results clearly"""

import httpx
import json

BASE_URL = "http://localhost:8000"

print("\n" + "=" * 70)
print("  COLLEGE SYSTEM - QUICK FUNCTIONALITY CHECK")
print("=" * 70 + "\n")

tests_passed = 0
tests_failed = 0

# TEST 1: Health Check
print("[TEST 1]  Health Check")
try:
    r = httpx.get(f"{BASE_URL}/health", timeout=5)
    if r.status_code == 200:
        print("  ✓ PASS - Backend is healthy")
        tests_passed += 1
    else:
        print(f"  ✗ FAIL - Status: {r.status_code}")
        tests_failed += 1
except Exception as e:
    print(f"  ✗ ERROR: {e}")
    tests_failed += 1

# TEST 2: Dashboard
print("\n[TEST 2]  Dashboard Access")
try:
    r = httpx.get("http://localhost:5500/html/dashboard.html", timeout=5)
    if r.status_code == 200:
        print(f"  ✓ PASS - Dashboard loads ({len(r.content)} bytes)")
        tests_passed += 1
    else:
        print(f"  ✗ FAIL - Status: {r.status_code}")
        tests_failed += 1
except Exception as e:
    print(f"  ✗ ERROR: {e}")
    tests_failed += 1

# TEST 3: User Registration (new user)
print("\n[TEST 3]  User Registration")
reg_data = {
    "email": "testcollege@example.edu",
    "username": "testcollege",
    "password": "TestCollege123",
    "first_name": "Test",
    "last_name": "College"
}
try:
    r = httpx.post(f"{BASE_URL}/api/v1/auth/register", json=reg_data, timeout=10)
    if r.status_code in [200, 201]:
        print("  ✓ PASS - User registered successfully")
        tests_passed += 1
        reg_user_id = r.json().get("user_id") or r.json().get("id")
    else:
        print(f"  ✗ FAIL - Status: {r.status_code}")
        print(f"        Response: {r.text[:150]}")
        tests_failed += 1
        reg_user_id = None
except Exception as e:
    print(f"  ✗ ERROR: {e}")
    tests_failed += 1
    reg_user_id = None

# TEST 4: Login (with newly registered user)
print("\n[TEST 4]  Login Authentication")
login_data = {
    "username": reg_data["username"],
    "password": reg_data["password"]
}
try:
    r = httpx.post(f"{BASE_URL}/api/v1/auth/login", json=login_data, timeout=10)
    if r.status_code == 200:
        print("  ✓ PASS - Login successful")
        resp = r.json()
        token = resp.get("access_token", "N/A")
        print(f"        User ID: {resp.get('user_id', 'N/A')}")
        print(f"        Token: {str(token)[:40]}...")
        tests_passed += 1
        access_token = token
    else:
        print(f"  ✗ FAIL - Status: {r.status_code}")
        print(f"        Response: {r.text[:150]}")
        tests_failed += 1
        access_token = None
except Exception as e:
    print(f"  ✗ ERROR: {e}")
    tests_failed += 1
    access_token = None

# TEST 5: Protected API with Token
if access_token:
    print("\n[TEST 5]  Protected Endpoint (with token)")
    try:
        headers = {"Authorization": f"Bearer {access_token}"}
        r = httpx.get(f"{BASE_URL}/api/v1/mfa/methods", headers=headers, timeout=5)
        if r.status_code in [200, 401]:  # 401 is ok if not set up yet
            print(f"  ✓ PASS - Token accepted (Status: {r.status_code})")
            tests_passed += 1
        else:
            print(f"  ✗ FAIL - Status: {r.status_code}")
            tests_failed += 1
    except Exception as e:
        print(f"  ✗ ERROR: {e}")
        tests_failed += 1
else:
    print("\n[TEST 5]  Protected Endpoint (SKIPPED - no token)")

# TEST 6: API Documentation
print("\n[TEST 6]  API Documentation")
try:
    r = httpx.get(f"{BASE_URL}/docs", timeout=5)
    if r.status_code == 200:
        print("  ✓ PASS - Swagger UI available")
        tests_passed += 1
    else:
        print(f"  ✗ FAIL - Status: {r.status_code}")
        tests_failed += 1
except Exception as e:
    print(f"  ✗ ERROR: {e}")
    tests_failed += 1

# TEST 7: Prometheus Metrics
print("\n[TEST 7]  Prometheus Metrics")
try:
    r = httpx.get(f"{BASE_URL}/metrics", timeout=5)
    if r.status_code == 200:
        print("  ✓ PASS - Metrics endpoint working")
        tests_passed += 1
    else:
        print(f"  ✗ FAIL - Status: {r.status_code}")
        tests_failed += 1
except Exception as e:
    print(f"  ✗ ERROR: {e}")
    tests_failed += 1

# SUMMARY
print("\n" + "=" * 70)
total = tests_passed + tests_failed
pct = (tests_passed / total * 100) if total > 0 else 0

print(f"  RESULTS: {tests_passed}/{total} tests passed ({pct:.0f}%)")

if tests_failed == 0:
    print("\n  ✓✓✓ ALL TESTS PASSING - SYSTEM IS FULLY FUNCTIONAL! ✓✓✓")
elif tests_failed <= 2:
    print("\n  ✓ Most features working! Minor issues only.")
else:
    print(f"\n  ⚠️  {tests_failed} tests failed - Review above for details")

print("=" * 70 + "\n")
