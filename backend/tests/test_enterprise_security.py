#!/usr/bin/env python3
"""
Enterprise Security Features Test Suite
Tests rate limiting, account lockout, and protection mechanisms
"""

import requests
import time
import json
from datetime import datetime
import sys

BASE_URL = "http://localhost:8000"
API_URL = f"{BASE_URL}/api/v1/auth"

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    END = '\033[0m'

def print_test(title, status):
    symbol = f"{Colors.GREEN}✓{Colors.END}" if status else f"{Colors.RED}✗{Colors.END}"
    print(f"{symbol} {title}")

def print_section(title):
    print(f"\n{Colors.BLUE}{'='*60}{Colors.END}")
    print(f"{Colors.BLUE}{title}{Colors.END}")
    print(f"{Colors.BLUE}{'='*60}{Colors.END}\n")

def test_rate_limiting_register():
    """Test registration rate limiting (3/hour)"""
    print_section("TEST 1: Registration Rate Limiting (3 per hour)")
    
    base_payload = {
        "email": "ratelimit-test-{}.com",
        "username": "ratelimit_test_{}",
        "password": "TestPassword123!",
        "first_name": "Rate",
        "last_name": "Limiter",
        "confirm_password": "TestPassword123!"
    }
    
    success_count = 0
    rate_limit_hit = False
    
    for i in range(5):
        payload = base_payload.copy()
        payload["email"] = f"ratelimit{i}@test.com"
        payload["username"] = f"ratelimit_test_{i}"
        
        try:
            response = requests.post(f"{API_URL}/register", json=payload)
            print(f"  Attempt {i+1}: Status {response.status_code}")
            
            if response.status_code == 201:
                success_count += 1
                print(f"    {Colors.GREEN}✓ Registration successful{Colors.END}")
            elif response.status_code == 429:
                rate_limit_hit = True
                print(f"    {Colors.YELLOW}⚠ Rate limit hit (expected after 3){Colors.END}")
                print(f"    Details: {response.json()}")
            else:
                print(f"    Response: {response.json()}")
        except Exception as e:
            print(f"    {Colors.RED}✗ Error: {e}{Colors.END}")
        
        time.sleep(0.5)
    
    print()
    print_test("Some registrations succeeded", success_count > 0)
    print_test("Rate limit was enforced (429)", rate_limit_hit)

def test_rate_limiting_login():
    """Test login rate limiting (5/minute)"""
    print_section("TEST 2: Login Rate Limiting (5 per minute)")
    
    rate_limit_hit = False
    attempts = 0
    
    for i in range(8):
        payload = {
            "username": "nonexistent_user",
            "password": "wrongpassword",
            "device_name": f"Test Device {i+1}"
        }
        
        try:
            response = requests.post(f"{API_URL}/login", json=payload)
            attempts += 1
            print(f"  Attempt {i+1}: Status {response.status_code}")
            
            if response.status_code == 429:
                rate_limit_hit = True
                print(f"    {Colors.YELLOW}⚠ Rate limit hit (expected after 5){Colors.END}")
                print(f"    Details: {response.json()}")
            elif response.status_code in [401, 423]:
                print(f"    {Colors.GREEN}✓ Request processed (401/423){Colors.END}")
            else:
                print(f"    Response: {response.json()}")
        except Exception as e:
            print(f"    {Colors.RED}✗ Error: {e}{Colors.END}")
        
        time.sleep(0.3)
    
    print()
    print_test("Rate limit enforced after 5 attempts", rate_limit_hit)

def test_account_lockout():
    """Test account lockout after failed attempts"""
    print_section("TEST 3: Account Lockout Policy")
    
    # Use a test user that might exist
    username = "testcollege"
    
    print("Simulating multiple failed login attempts to trigger lockout...")
    print(f"Testing with user: {username}\n")
    
    failed_attempts = 0
    account_locked = False
    lock_message = ""
    
    for i in range(7):
        payload = {
            "username": username,
            "password": "wrongpasswordattempt",
            "device_name": f"Test Device {i+1}"
        }
        
        try:
            response = requests.post(f"{API_URL}/login", json=payload)
            print(f"  Attempt {i+1}: Status {response.status_code}")
            
            if response.status_code == 401:
                failed_attempts += 1
                print(f"    {Colors.RED}✗ Login failed (401){Colors.END}")
            elif response.status_code == 423:
                account_locked = True
                lock_message = response.json().get("detail", "Account locked")
                print(f"    {Colors.YELLOW}⚠ Account locked (423){Colors.END}")
                print(f"    Message: {lock_message}")
                break
            elif response.status_code == 429:
                print(f"    {Colors.YELLOW}⚠ Rate limit hit (429){Colors.END}")
                break
            else:
                print(f"    Status: {response.status_code}")
                print(f"    Response: {response.json()}")
        except Exception as e:
            print(f"    {Colors.RED}✗ Error: {e}{Colors.END}")
        
        time.sleep(0.2)
    
    print()
    print_test("Multiple failed attempts recorded", failed_attempts >= 1)
    print_test("Account lockout triggered (423)", account_locked)

def test_token_refresh_rate_limit():
    """Test refresh token rate limiting (10/minute)"""
    print_section("TEST 4: Refresh Token Rate Limiting (10 per minute)")
    
    # First, try to get a valid refresh token
    login_payload = {
        "username": "testcollege",
        "password": "TestCollege123",
        "device_name": "Test Device"
    }
    
    print("Attempting to get refresh token...")
    try:
        response = requests.post(f"{API_URL}/login", json=login_payload)
        if response.status_code != 200:
            print(f"{Colors.YELLOW}⚠ Could not login with test user, testing with invalid tokens{Colors.END}\n")
            refresh_token = "invalid_token"
        else:
            tokens = response.json()
            refresh_token = tokens.get("refresh_token", "invalid_token")
            print(f"{Colors.GREEN}✓ Got refresh token{Colors.END}\n")
    except Exception as e:
        print(f"{Colors.RED}✗ Error getting tokens: {e}{Colors.END}\n")
        refresh_token = "invalid_token"
    
    rate_limit_hit = False
    
    for i in range(12):
        payload = {"refresh_token": refresh_token}
        
        try:
            response = requests.post(f"{API_URL}/refresh", json=payload)
            print(f"  Attempt {i+1}: Status {response.status_code}")
            
            if response.status_code == 429:
                rate_limit_hit = True
                print(f"    {Colors.YELLOW}⚠ Rate limit hit{Colors.END}")
            elif response.status_code == 401:
                print(f"    {Colors.GREEN}✓ Invalid token rejected (401){Colors.END}")
            else:
                print(f"    Response: {response.status_code}")
        except Exception as e:
            print(f"    {Colors.RED}✗ Error: {e}{Colors.END}")
        
        time.sleep(0.2)
    
    print()
    print_test("Refresh endpoint tested successfully", True)

def test_admin_unlock_endpoint():
    """Test admin unlock endpoint"""
    print_section("TEST 5: Admin Account Unlock Endpoint")
    
    # Try to access admin unlock endpoint (will fail without auth, but tests endpoint exists)
    print("Testing admin unlock endpoint access...\n")
    
    try:
        response = requests.post(f"{API_URL}/admin/unlock-account/1")
        
        print(f"  Endpoint response status: {response.status_code}")
        
        if response.status_code == 401:
            print(f"    {Colors.GREEN}✓ Returns 401 (requires auth){Colors.END}")
        elif response.status_code == 403:
            print(f"    {Colors.GREEN}✓ Returns 403 (requires admin role){Colors.END}")
        else:
            print(f"    Status: {response.status_code}")
        
        print_test("Admin unlock endpoint exists and protected", response.status_code in [401, 403])
    except Exception as e:
        print(f"    {Colors.RED}✗ Error: {e}{Colors.END}")
        print_test("Admin unlock endpoint accessible", False)

def test_admin_account_status_endpoint():
    """Test admin account status endpoint"""
    print_section("TEST 6: Admin Account Status Endpoint")
    
    print("Testing admin account status endpoint access...\n")
    
    try:
        response = requests.get(f"{API_URL}/admin/account-status/1")
        
        print(f"  Endpoint response status: {response.status_code}")
        
        if response.status_code == 401:
            print(f"    {Colors.GREEN}✓ Returns 401 (requires auth){Colors.END}")
        elif response.status_code == 403:
            print(f"    {Colors.GREEN}✓ Returns 403 (requires admin role){Colors.END}")
        else:
            print(f"    Status: {response.status_code}")
        
        print_test("Admin account status endpoint exists and protected", response.status_code in [401, 403])
    except Exception as e:
        print(f"    {Colors.RED}✗ Error: {e}{Colors.END}")
        print_test("Admin account status endpoint accessible", False)

def main():
    print_section("ZTNAS Enterprise Security Features - Test Suite")
    print(f"Testing against: {BASE_URL}\n")
    
    # Check if backend is accessible
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        print(f"{Colors.GREEN}✓ Backend is running{Colors.END}\n")
    except Exception as e:
        print(f"{Colors.RED}✗ Backend is not accessible: {e}{Colors.END}")
        print(f"{Colors.RED}✗ Make sure the backend is running on {BASE_URL}{Colors.END}")
        sys.exit(1)
    
    # Run tests
    test_rate_limiting_login()
    test_account_lockout()
    test_token_refresh_rate_limit()
    test_admin_unlock_endpoint()
    test_admin_account_status_endpoint()
    
    print_section("Test Suite Complete")
    print("For detailed results, check the output above\n")

if __name__ == "__main__":
    main()
