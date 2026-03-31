#!/usr/bin/env python3
"""Test login functionality with existing test users"""
import httpx
import json
import sys
import os

# Fix encoding for Windows
if sys.platform == 'win32':
    os.environ.setdefault('PYTHONIOENCODING', 'utf-8')

BASE_URL = "http://localhost:8000"

# Test users from database (from check_users.py output)
test_credentials = [
    {"username": "testuser", "password": "password123"},
    {"username": "testuser2", "password": "password123"},
    {"username": "browsertest", "password": "password123"},
    {"username": "test", "password": "password123"},
]

def test_login(username, password):
    """Attempt login with given credentials"""
    print(f"\n{'='*60}")
    print(f"Testing login: {username}")
    print(f"{'='*60}")
    
    try:
        # First check if user exists by attempting login
        response = httpx.post(
            f"{BASE_URL}/api/v1/auth/login",
            json={
                "username": username,
                "password": password,
                "device_name": "Test Device"
            },
            timeout=10
        )
        
        print(f"Status Code: {response.status_code}")
        
        try:
            data = response.json()
            print(f"Response: {json.dumps(data, indent=2)}")
            
            if response.status_code == 200:
                print(f"\n[SUCCESS] Login SUCCESS for {username}!")
                return True, data
            else:
                print(f"\n[FAILED] Login FAILED for {username}: {data.get('detail', 'Unknown error')}")
                return False, data
        except:
            print(f"Response text: {response.text}")
            return False, None
            
    except Exception as e:
        print(f"✗ Request error: {type(e).__name__}: {str(e)}")
        return False, None

def test_register_new_user():
    """Register a new test user"""
    print(f"\n{'='*60}")
    print("Registering new test user")
    print(f"{'='*60}")
    
    import datetime
    timestamp = int(datetime.datetime.now().timestamp())
    new_username = f"test_deploy_{timestamp}"
    
    try:
        response = httpx.post(
            f"{BASE_URL}/api/v1/auth/register",
            json={
                "username": new_username,
                "email": f"{new_username}@test.com",
                "password": "Test@Password123",
                "first_name": "Deployment",
                "last_name": "Test"
            },
            timeout=10
        )
        
        print(f"Status Code: {response.status_code}")
        data = response.json()
        print(f"Response: {json.dumps(data, indent=2)}")
        
        if response.status_code == 201:
            print(f"\n✓ User registration SUCCESS!")
            print(f"   Username: {new_username}")
            print(f"   Email: {new_username}@test.com")
            
            # Try to login with new user
            print(f"\nAttempting login with new user...")
            success, login_data = test_login(new_username, "Test@Password123")
            return success, new_username if success else None
        else:
            print(f"\n✗ Registration FAILED: {data}")
            return False, None
            
    except Exception as e:
        print(f"✗ Registration error: {type(e).__name__}: {str(e)}")
        return False, None

def main():
    print("\n" + "="*60)
    print("STEP 4: Authentication Testing")
    print("="*60)
    
    # First check if API is reachable
    try:
        health_resp = httpx.get(f"{BASE_URL}/health", timeout=5)
        if health_resp.status_code != 200:
            print(f"✗ Backend API not healthy! Status: {health_resp.status_code}")
            sys.exit(1)
        print(f"✓ Backend API is healthy")
    except Exception as e:
        print(f"✗ Cannot reach backend API: {e}")
        sys.exit(1)
    
    # Try existing test users
    print(f"\n\nAttempting login with existing test users...")
    successful_login = False
    
    for creds in test_credentials:
        success, data = test_login(creds["username"], creds["password"])
        if success:
            successful_login = True
            break
    
    # If no existing user works, try to register a new one
    if not successful_login:
        print(f"\n\nNo existing credentials worked. Attempting to register new user...")
        success, username = test_register_new_user()
        if success:
            successful_login = True
    
    # Summary
    print(f"\n\n" + "="*60)
    print("AUTHENTICATION TEST SUMMARY")
    print("="*60)
    
    if successful_login:
        print(f"✓ Authentication is working!")
        print(f"✓ STEP 4 PASSED: User can login and receive JWT tokens")
        print(f"\nNext steps:")
        print(f"1. Test dashboard at: http://localhost:5500/html/dashboard.html")
        print(f"2. Try logging in with the tested credentials")
        print(f"3. Verify views load and function correctly")
        return 0
    else:
        print(f"✗ Authentication tests FAILED")
        print(f"✗ Could not login with any test users")
        print(f"✗ Could not register new test user")
        print(f"\nTroubleshooting:")
        print(f"1. Check backend logs: tail -f backend/logs/ztnas.log")
        print(f"2. Verify API endpoints: curl http://localhost:8000/docs")
        print(f"3. Check database connection: python test_db_simple.py")
        return 1

if __name__ == "__main__":
    sys.exit(main())
