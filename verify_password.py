#!/usr/bin/env python3
"""
Verify the new password works
"""

import urllib.request
import urllib.error
import json

API_URL = "http://localhost:8000/api/v1"

print("=" * 70)
print("VERIFYING PASSWORD WORKS")
print("=" * 70)

login_data = {
    "username": "test@test.com",
    "password": "TestPassword@123"
}

print(f"\nTesting login with:")
print(f"  Email: {login_data['username']}")
print(f"  Password: {login_data['password']}")

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
    
    print(f"\nRESULT: LOGIN SUCCESSFUL!")
    print(f"Status: 200 OK")
    print(f"Access token length: {len(result.get('access_token', ''))}")
    print(f"Token type: {result.get('token_type')}")
    
except urllib.error.HTTPError as e:
    body = e.read().decode('utf-8')
    print(f"\nRESULT: LOGIN FAILED")
    print(f"Status: {e.code}")
    print(f"Error: {body}")
except Exception as e:
    print(f"\nERROR: {e}")

print("\n" + "=" * 70)
print("You can now use these credentials to login:")
print("  URL: http://localhost:5500")
print("  Email: test@test.com")
print("  Password: TestPassword@123")
print("=" * 70)
