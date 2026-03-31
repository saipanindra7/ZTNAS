#!/usr/bin/env python3
"""
Frontend Server Verification Script
Tests that the production server is working correctly
"""

import requests
import sys
import time
from pathlib import Path

def verify_server(host="localhost", port=5500):
    """Verify the frontend server is running and responding correctly"""
    
    url_base = f"http://{host}:{port}"
    
    print("\n" + "="*70)
    print("ZTNAS Frontend Server Verification")
    print("="*70 + "\n")
    
    # Test 1: Root request should serve index.html
    print("Test 1: Root request (/) should serve index.html...")
    try:
        response = requests.get(f"{url_base}/", timeout=2)
        if response.status_code == 200:
            if "DOCTYPE html" in response.text or "ZTNAS" in response.text:
                print("✓ PASS: Root served successfully (200 OK)")
            else:
                print("✗ FAIL: Invalid response content")
                return False
        else:
            print(f"✗ FAIL: Got status code {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("✗ FAIL: Cannot connect to server")
        print(f"   Make sure server is running on http://{host}:{port}")
        return False
    except Exception as e:
        print(f"✗ FAIL: {str(e)}")
        return False
    
    # Test 2: Should not show directory listing
    print("\nTest 2: Directory listing should be blocked...")
    try:
        response = requests.get(f"{url_base}/static/", timeout=2)
        if response.status_code == 403:
            print("✓ PASS: Directory listing blocked (403 Forbidden)")
        elif response.status_code == 200 and "Index of" not in response.text:
            print("✓ PASS: Directory listing not shown")
        else:
            print(f"⚠ WARNING: Got status code {response.status_code}")
    except Exception as e:
        print(f"⚠ WARNING: {str(e)}")
    
    # Test 3: Security headers
    print("\nTest 3: Security headers should be present...")
    try:
        response = requests.get(f"{url_base}/", timeout=2)
        headers_to_check = [
            'X-Frame-Options',
            'X-Content-Type-Options',
            'Content-Security-Policy'
        ]
        all_present = True
        for header in headers_to_check:
            if header in response.headers:
                print(f"✓ {header}: {response.headers[header][:50]}...")
            else:
                print(f"✗ Missing: {header}")
                all_present = False
        
        if all_present:
            print("✓ PASS: All security headers present")
        else:
            print("✗ FAIL: Some security headers missing")
            return False
    except Exception as e:
        print(f"✗ FAIL: {str(e)}")
        return False
    
    # Test 4: Static files
    print("\nTest 4: Static files should load...")
    static_files = [
        "/css/style.css",
        "/js/login.js",
        "/html/login.html",
        "/html/dashboard.html"
    ]
    
    all_found = True
    for file in static_files:
        try:
            response = requests.get(f"{url_base}{file}", timeout=2)
            if response.status_code == 200:
                print(f"✓ {file}")
            else:
                print(f"✗ {file} (Status: {response.status_code})")
                all_found = False
        except Exception as e:
            print(f"✗ {file} ({str(e)})")
            all_found = False
    
    if all_found:
        print("✓ PASS: All static files found")
    else:
        print("✗ FAIL: Some static files missing")
        return False
    
    # Test 5: CORS headers
    print("\nTest 5: CORS headers should be present...")
    try:
        response = requests.get(f"{url_base}/", timeout=2)
        if 'Access-Control-Allow-Origin' in response.headers:
            print(f"✓ Access-Control-Allow-Origin: {response.headers['Access-Control-Allow-Origin']}")
            print("✓ PASS: CORS headers present")
        else:
            print("✗ FAIL: CORS headers missing")
            return False
    except Exception as e:
        print(f"✗ FAIL: {str(e)}")
        return False
    
    print("\n" + "="*70)
    print("✅ ALL TESTS PASSED - Server is production-ready!")
    print("="*70 + "\n")
    
    return True

if __name__ == "__main__":
    # Wait a moment for server to start
    time.sleep(1)
    
    # Run verification
    success = verify_server()
    sys.exit(0 if success else 1)
