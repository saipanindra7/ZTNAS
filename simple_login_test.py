#!/usr/bin/env python3
"""
Simpler test - just try to login
"""

import urllib.request
import urllib.error
import json

API_URL = "http://localhost:8000/api/v1"
TEST_USERNAME = "testdiag"
TEST_PASSWORD = "TestDiag@123"

print("Testing login endpoint...")

login_data = {
    "username": TEST_USERNAME,
    "password": TEST_PASSWORD
}

try:
    req = urllib.request.Request(
        f"{API_URL}/auth/login",
        data=json.dumps(login_data).encode('utf-8'),
        headers={'Content-Type': 'application/json'},
        method='POST'
    )
    response = urllib.request.urlopen(req, timeout=5)
    print(f"SUCCESS! Status: {response.status}")
    body = response.read().decode('utf-8')
    result = json.loads(body)
    print(f"Token: {result.get('access_token', 'MISSING')[:50]}...")
    
except urllib.error.HTTPError as e:
    print(f"HTTP Error {e.code}")
    try:
        body = e.read().decode('utf-8')
        error = json.loads(body)
        print(f"Error detail: {error.get('detail', body)}")
    except:
        print(f"Response: {body}")
except Exception as e:
    print(f"ERROR: {e}")
