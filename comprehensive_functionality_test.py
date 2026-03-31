#!/usr/bin/env python3
"""
Comprehensive ZTNAS College Dashboard System Test
Tests all functionalities, permissions, and data flows
"""

import httpx
import json
from datetime import datetime

BASE_URL = "http://localhost:8000/api/v1"

class zt_Tester:
    def __init__(self):
        self.tests_passed = 0
        self.tests_failed = 0
        self.test_results = []

    def test(self, name, condition, details=""):
        """Record test result"""
        status = "✅ PASS" if condition else "❌ FAIL"
        self.test_results.append(f"{status} - {name}" + (f": {details}" if details else ""))
        
        if condition:
            self.tests_passed += 1
        else:
            self.tests_failed += 1
        
        return condition

    def print_results(self):
        """Print all test results"""
        print("\n" + "="*80)
        print("TEST RESULTS SUMMARY")
        print("="*80)
        for result in self.test_results:
            print(result)
        print(f"\nPassed: {self.tests_passed} | Failed: {self.tests_failed}")
        print("="*80)

def run_all_tests():
    tester = zt_Tester()
    
    print("="*80)
    print("ZTNAS COLLEGE DASHBOARD - COMPREHENSIVE FUNCTIONALITY TEST")
    print("="*80)
    
    # ========== TEST 1: BACKEND HEALTH ==========
    print("\n[TEST 1] Backend Health & Initialization")
    print("-"*80)
    try:
        r = httpx.get(f"{BASE_URL}/../health", timeout=5)
        tester.test("Backend Health Check", r.status_code == 200)
        if r.status_code == 200:
            data = r.json()
            tester.test("Backend Status", data.get("status") == "healthy")
            tester.test("Production Modules", len(data.get("production_modules", [])) >= 5, 
                       f"Modules: {len(data.get('production_modules', []))}")
    except Exception as e:
        tester.test("Backend Health Check", False, str(e)[:50])
    
    # ========== TEST 2: AUTHENTICATION ==========
    print("\n[TEST 2] Authentication System")
    print("-"*80)
    token = None
    user_id = None
    
    try:
        # Test Login
        login_resp = httpx.post(f"{BASE_URL}/auth/login",
            json={'username': 'testcollege', 'password': 'TestCollege123'},
            timeout=5)
        
        tester.test("Login Success", login_resp.status_code == 200)
        
        if login_resp.status_code == 200:
            data = login_resp.json()
            token = data.get('access_token')
            tester.test("Token Generation", token is not None and len(token) > 50)
            tester.test("Token Type", data.get('token_type') == 'bearer')
            tester.test("Token Expiry", data.get('expires_in', 0) > 0)
        
        # Test Get Current User
        if token:
            headers = {'Authorization': f'Bearer {token}'}
            user_resp = httpx.get(f"{BASE_URL}/auth/me", headers=headers, timeout=5)
            tester.test("Get Current User", user_resp.status_code == 200)
            
            if user_resp.status_code == 200:
                user = user_resp.json()
                user_id = user.get('id')
                tester.test("User Info Present", user.get('username') is not None)
                tester.test("User Email Present", user.get('email') is not None)
                tester.test("User Active", user.get('is_active') == True)
    
    except Exception as e:
        tester.test("Authentication System", False, str(e)[:50])
    
    # ========== TEST 3: USER MANAGEMENT ==========
    print("\n[TEST 3] User Management")
    print("-"*80)
    
    if token:
        try:
            headers = {'Authorization': f'Bearer {token}'}
            
            # List Users
            users_resp = httpx.get(f"{BASE_URL}/auth/users", headers=headers, timeout=5)
            tester.test("List Users", users_resp.status_code == 200)
            
            if users_resp.status_code == 200:
                data = users_resp.json()
                tester.test("Users Count", data.get('total_users', 0) > 0,
                           f"Total: {data.get('total_users')}")
                tester.test("Users Array", 'users' in data and isinstance(data['users'], list))
                
                if data.get('users'):
                    user = data['users'][0]
                    tester.test("User Fields Complete",
                               all(k in user for k in ['id', 'username', 'email', 'is_active']))
        
        except Exception as e:
            tester.test("User Management", False, str(e)[:50])
    
    # ========== TEST 4: DASHBOARD ENDPOINTS ==========
    print("\n[TEST 4] Dashboard Endpoints")
    print("-"*80)
    
    if token:
        try:
            headers = {'Authorization': f'Bearer {token}'}
            
            endpoints = {
                '/auth/audit/logs': 'Audit Logs',
                '/auth/policies': 'Access Policies',
                '/zero-trust/devices/trusted': 'Trusted Devices'
            }
            
            for endpoint, name in endpoints.items():
                r = httpx.get(f"{BASE_URL}{endpoint}", headers=headers, timeout=5)
                tester.test(f"Dashboard - {name}", r.status_code == 200, f"Status: {r.status_code}")
                
                if r.status_code == 200:
                    data = r.json()
                    if 'logs' in data:
                        tester.test(f"{name} - Data Format", isinstance(data['logs'], list))
                    elif 'policies' in data:
                        tester.test(f"{name} - Data Format", isinstance(data['policies'], list))
                        if data['policies']:
                            policy = data['policies'][0]
                            tester.test(f"{name} - Policy Fields",
                                       all(k in policy for k in ['id', 'name', 'roles']))
                    elif 'devices' in data:
                        tester.test(f"{name} - Data Format", isinstance(data['devices'], list))
        
        except Exception as e:
            tester.test("Dashboard Endpoints", False, str(e)[:50])
    
    # ========== TEST 5: MFA SYSTEM ==========
    print("\n[TEST 5] MFA System")
    print("-"*80)
    
    if token:
        try:
            headers = {'Authorization': f'Bearer {token}'}
            
            # List MFA Methods
            mfa_resp = httpx.get(f"{BASE_URL}/mfa/methods", headers=headers, timeout=5)
            tester.test("List MFA Methods", mfa_resp.status_code == 200)
            
            if mfa_resp.status_code == 200:
                data = mfa_resp.json()
                tester.test("MFA Methods Present", 'methods' in data)
                tester.test("MFA Methods Format", isinstance(data.get('methods', []), list))
        
        except Exception as e:
            tester.test("MFA System", False, str(e)[:50])
    
    # ========== TEST 6: ZERO TRUST ENDPOINTS ==========
    print("\n[TEST 6] Zero Trust Analysis")
    print("-"*80)
    
    if token:
        try:
            headers = {'Authorization': f'Bearer {token}'}
            
            zt_endpoints = {
                '/zero-trust/anomalies/recent': 'Anomalies Detection',
                '/zero-trust/profile/behavior': 'Behavior Profile',
                '/zero-trust/risk/timeline': 'Risk Timeline',
            }
            
            for endpoint, name in zt_endpoints.items():
                r = httpx.get(f"{BASE_URL}{endpoint}", headers=headers, timeout=5)
                tester.test(f"Zero Trust - {name}", r.status_code == 200, f"Status: {r.status_code}")
        
        except Exception as e:
            tester.test("Zero Trust Endpoints", False, str(e)[:50])
    
    # ========== TEST 7: ROLE-BASED ACCESS ==========
    print("\n[TEST 7] Role-Based Access Control")
    print("-"*80)
    
    test_accounts = [
        {'username': 'testcollege', 'password': 'TestCollege123', 'role': 'Faculty'},
        {'username': 'collegeadmin', 'password': 'CollegeTest123', 'role': 'Admin'},
    ]
    
    for account in test_accounts:
        try:
            # Login with account
            r = httpx.post(f"{BASE_URL}/auth/login",
                json={'username': account['username'], 'password': account['password']},
                timeout=5)
            
            tester.test(f"RBAC - {account['role']} Login", r.status_code == 200)
            
            if r.status_code == 200:
                token = r.json().get('access_token')
                headers = {'Authorization': f'Bearer {token}'}
                
                # Get user info to verify role
                user_resp = httpx.get(f"{BASE_URL}/auth/me", headers=headers, timeout=5)
                if user_resp.status_code == 200:
                    user = user_resp.json()
                    tester.test(f"RBAC - {account['role']} Has ID", user.get('id') is not None)
        
        except Exception as e:
            tester.test(f"RBAC - {account['role']}", False, str(e)[:50])
    
    # ========== TEST 8: FRONTEND ASSETS ==========
    print("\n[TEST 8] Frontend Assets")
    print("-"*80)
    
    try:
        frontend_assets = [
            ('http://localhost:5500/html/login.html', 'Login Page'),
            ('http://localhost:5500/html/dashboard.html', 'Dashboard'),
            ('http://localhost:5500/css/theme.css', 'Theme CSS'),
            ('http://localhost:5500/js/dashboard.js', 'Dashboard JS'),
            ('http://localhost:5500/lib/chart.umd.js', 'Chart.js Library'),
        ]
        
        for url, name in frontend_assets:
            r = httpx.get(url, timeout=5)
            tester.test(f"Frontend - {name}", r.status_code == 200, f"Status: {r.status_code}")
    
    except Exception as e:
        tester.test("Frontend Assets", False, str(e)[:50])
    
    # ========== TEST 9: DATABASE CONNECTIVITY ==========
    print("\n[TEST 9] Database Connectivity")
    print("-"*80)
    
    if token:
        try:
            headers = {'Authorization': f'Bearer {token}'}
            
            # Try multiple endpoints that require DB calls
            db_endpoints = [
                f"{BASE_URL}/auth/users",
                f"{BASE_URL}/auth/audit/logs",
                f"{BASE_URL}/auth/me"
            ]
            
            all_pass = True
            for endpoint in db_endpoints:
                r = httpx.get(endpoint, headers=headers, timeout=5)
                if r.status_code != 200:
                    all_pass = False
            
            tester.test("Database Connectivity", all_pass, "All DB queries successful")
        
        except Exception as e:
            tester.test("Database Connectivity", False, str(e)[:50])
    
    # ========== TEST 10: ERROR HANDLING ==========
    print("\n[TEST 10] Error Handling")
    print("-"*80)
    
    try:
        # Test invalid login
        r = httpx.post(f"{BASE_URL}/auth/login",
            json={'username': 'invalid_user', 'password': 'wrong_password'},
            timeout=5)
        tester.test("Error - Invalid Login Rejected", r.status_code == 401)
        
        # Test missing token
        r = httpx.get(f"{BASE_URL}/auth/users", timeout=5)
        tester.test("Error - Missing Auth Token Rejected", r.status_code == 401)
        
        # Test invalid token
        headers = {'Authorization': 'Bearer invalid_token_123'}
        r = httpx.get(f"{BASE_URL}/auth/users", headers=headers, timeout=5)
        tester.test("Error - Invalid Token Rejected", r.status_code == 401)
    
    except Exception as e:
        tester.test("Error Handling", False, str(e)[:50])
    
    print("\n")
    tester.print_results()
    
    return tester.tests_failed == 0

if __name__ == "__main__":
    success = run_all_tests()
    exit(0 if success else 1)
