#!/usr/bin/env python3
"""
Test the login endpoint exactly as the frontend would
"""

import json

print("=" * 70)
print("TESTING LOGIN API ENDPOINT - SIMULATING FRONTEND")
print("=" * 70)

# Create test user credentials (same as diagnostic test)
test_credentials = {
    "username": "testdiag",
    "password": "TestDiag@123"
}

print("\nCredentials that would be sent:")
print(json.dumps(test_credentials, indent=2))

print("\nExpected Request:")
print("POST /api/v1/auth/login HTTP/1.1")
print("Host: localhost:8000")
print("Content-Type: application/json")
print(f"Content-Length: {len(json.dumps(test_credentials))}")
print(f"\n{json.dumps(test_credentials)}")

print("\n" + "=" * 70)
print("WHAT TO TEST NEXT:")
print("=" * 70)
print("""
1. Make sure backend is running on port 8000
   - Check: netstat -ano | Select-String 8000
   
2. Test the login endpoint directly in PowerShell:
   
   $credentials = @{
       username = "testdiag"
       password = "TestDiag@123"
   } | ConvertTo-Json
   
   $uri = "http://localhost:8000/api/v1/auth/login"
   
   Invoke-WebRequest -Uri $uri `
       -Method POST `
       -Headers @{"Content-Type"="application/json"} `
       -Body $credentials
   
3. Or use curl equivalent:
   curl -X POST http://localhost:8000/api/v1/auth/login \\
     -H "Content-Type: application/json" \\
     -d '{"username":"testdiag","password":"TestDiag@123"}'

4. If login works for testdiag, then the issue is that:
   - User didn't actually register correctly
   - User is registering but password not being stored
   - User changing password between registration and login
   
5. Go to browser and test:
   - http://localhost:8000/api/v1/auth/debug/users
   - Look for your username in the list
   - If found, try: http://localhost:8000/api/v1/auth/debug/test-login/YOUR_USERNAME/YOUR_PASSWORD
""")
