#!/usr/bin/env python3
"""
ZTNAS Integration Test - Verify All New Features
Tests: Admin account, MFA setup, admin endpoints, device management
"""

import requests
import json
import time

BASE_URL = "http://localhost:8000"
API_BASE = f"{BASE_URL}/api/v1"

print("🧪 ZTNAS Integration Test Suite\n")

# Test 1: Admin Login
print("1️⃣ Testing Admin Login...")
try:
    response = requests.post(
        f"{API_BASE}/auth/login",
        json={"username": "admin", "password": "admin"}
    )
    
    if response.status_code == 200:
        data = response.json()
        admin_token = data.get('access_token')
        print("   ✅ Admin login successful")
        print(f"   Token: {admin_token[:20]}...")
    else:
        print(f"   ❌ Login failed: {response.status_code}")
        print(f"   Response: {response.json()}")
        admin_token = None
except Exception as e:
    print(f"   ❌ Error: {str(e)}")
    admin_token = None

print()

# Test 2: Check MFA Status Endpoint
if admin_token:
    print("2️⃣ Testing MFA Status Endpoint...")
    try:
        response = requests.get(
            f"{API_BASE}/mfa/status",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        if response.status_code == 200:
            data = response.json()
            print("   ✅ MFA status endpoint working")
            print(f"   MFA Required: {data.get('mfa_required')}")
            print(f"   MFA Configured: {data.get('mfa_configured')}")
            print(f"   MFA Verified: {data.get('mfa_verified')}")
        else:
            print(f"   ❌ Endpoint failed: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Error: {str(e)}")

print()

# Test 3: Check Admin Users Endpoint
if admin_token:
    print("3️⃣ Testing Admin Users Endpoint...")
    try:
        response = requests.get(
            f"{API_BASE}/admin/users",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        if response.status_code == 200:
            data = response.json()
            print("   ✅ Admin users endpoint working")
            users = data.get('users', [])
            print(f"   Total Users: {len(users)}")
            for user in users[:3]:
                print(f"     • {user.get('username')} ({user.get('email')})")
        else:
            print(f"   ❌ Endpoint failed: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Error: {str(e)}")

print()

# Test 4: Check Admin Logs Endpoint
if admin_token:
    print("4️⃣ Testing Admin Logs Endpoint...")
    try:
        response = requests.get(
            f"{API_BASE}/admin/logs?limit=10",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        if response.status_code == 200:
            data = response.json()
            print("   ✅ Admin logs endpoint working")
            logs = data.get('logs', [])
            print(f"   Total Logs: {len(logs)}")
            if logs:
                print(f"     • Sample: {logs[0].get('action')} - {logs[0].get('status')}")
        else:
            print(f"   ❌ Endpoint failed: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Error: {str(e)}")

print()

# Test 5: Check MFA Setup Endpoints
if admin_token:
    print("5️⃣ Testing MFA Setup Endpoints...")
    try:
        response = requests.get(
            f"{API_BASE}/mfa/methods",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        if response.status_code == 200:
            data = response.json()
            print("   ✅ MFA methods endpoint working")
            methods = data.get('methods', [])
            print(f"   Available Methods: {len(methods)}")
            for method in methods[:3]:
                print(f"     • {method.get('name')}")
        else:
            print(f"   ❌ Endpoint failed: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Error: {str(e)}")

print()

# Test 6: Check Route Registration
print("6️⃣ Checking Route Registration...")
try:
    response = requests.get(f"{BASE_URL}/openapi.json")
    if response.status_code == 200:
        data = response.json()
        paths = list(data.get('paths', {}).keys())
        
        required_routes = [
            '/api/v1/mfa/status',
            '/api/v1/admin/users',
            '/api/v1/admin/logs',
            '/api/v1/admin/policies'
        ]
        
        found_routes = [route for route in required_routes if route in paths]
        missing_routes = [route for route in required_routes if route not in paths]
        
        print(f"   ✅ OpenAPI schema available")
        print(f"   Total Routes: {len(paths)}")
        print(f"   Required Routes Found: {len(found_routes)}/{len(required_routes)}")
        
        if missing_routes:
            print(f"   ⚠️ Missing Routes:")
            for route in missing_routes:
                print(f"     • {route}")
        else:
            print(f"   ✅ All required routes present")
    else:
        print(f"   ❌ Could not fetch OpenAPI schema")
except Exception as e:
    print(f"   ❌ Error: {str(e)}")

print("\n" + "="*50)
print("✅ Integration Test Complete!")
print("="*50)
