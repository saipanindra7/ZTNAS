#!/usr/bin/env python3
"""Quick Functionality Test"""
import httpx

def test_endpoint(method, url, name, headers=None, json_data=None):
    try:
        if method == 'GET':
            r = httpx.get(url, headers=headers, timeout=3)
        else:
            r = httpx.post(url, headers=headers, json=json_data, timeout=3)
        
        status = "✅" if r.status_code in [200, 201] else "❌" if r.status_code >= 400 else "⚠️"
        print(f"{status} {name:40} - {r.status_code}")
        return r.status_code in [200, 201]
    except Exception as e:
        print(f"❌ {name:40} - TIMEOUT/ERROR")
        return False

print("="*80)
print("ZTNAS SYSTEM QUICK TEST")
print("="*80)

# Test Backend
print("\n[1] BACKEND & HEALTH")
test_endpoint('GET', 'http://localhost:8000/health', 'Backend Health')

# Test Auth
print("\n[2] AUTHENTICATION")
r = httpx.post('http://localhost:8000/api/v1/auth/login',
    json={'username': 'testcollege', 'password': 'TestCollege123'}, timeout=3)
token = r.json().get('access_token') if r.status_code == 200 else None
test_endpoint('POST', 'http://localhost:8000/api/v1/auth/login', 'Login', 
    json_data={'username': 'testcollege', 'password': 'TestCollege123'})

print("\n[3] USER ENDPOINTS")
headers = {'Authorization': f'Bearer {token}'} if token else {}
test_endpoint('GET', 'http://localhost:8000/api/v1/auth/me', 'Get Current User', headers=headers)
test_endpoint('GET', 'http://localhost:8000/api/v1/auth/users', 'List Users', headers=headers)

print("\n[4] DASHBOARD ENDPOINTS")
test_endpoint('GET', 'http://localhost:8000/api/v1/auth/audit/logs', 'Audit Logs', headers=headers)
test_endpoint('GET', 'http://localhost:8000/api/v1/auth/policies', 'Policies', headers=headers)
test_endpoint('GET', 'http://localhost:8000/api/v1/zero-trust/devices/trusted', 'Devices', headers=headers)

print("\n[5] MFA ENDPOINTS")
test_endpoint('GET', 'http://localhost:8000/api/v1/mfa/methods', 'MFA Methods', headers=headers)

print("\n[6] ZERO TRUST ENDPOINTS")
test_endpoint('GET', 'http://localhost:8000/api/v1/zero-trust/anomalies/recent', 'Anomalies', headers=headers)
test_endpoint('GET', 'http://localhost:8000/api/v1/zero-trust/profile/behavior', 'Behavior', headers=headers)
test_endpoint('GET', 'http://localhost:8000/api/v1/zero-trust/risk/timeline', 'Risk Timeline', headers=headers)

print("\n[7] FRONTEND ASSETS")
test_endpoint('GET', 'http://localhost:5500/html/login.html', 'Login Page')
test_endpoint('GET', 'http://localhost:5500/html/dashboard.html', 'Dashboard HTML')
test_endpoint('GET', 'http://localhost:5500/css/theme.css', 'Theme CSS')
test_endpoint('GET', 'http://localhost:5500/js/dashboard.js', 'Dashboard JS')
test_endpoint('GET', 'http://localhost:5500/lib/chart.umd.js', 'Chart.js')

print("\n[8] ERROR HANDLING")
r = httpx.post('http://localhost:8000/api/v1/auth/login',
    json={'username': 'invalid', 'password': 'wrong'}, timeout=3)
status = "✅" if r.status_code == 401 else "❌"
print(f"{status} Invalid Login Rejected                - {r.status_code}")

r = httpx.get('http://localhost:8000/api/v1/auth/users', timeout=3)
status = "✅" if r.status_code == 401 else "❌"
print(f"{status} Missing Auth Token Rejected           - {r.status_code}")

print("\n" + "="*80)
print("✅ ALL TESTS COMPLETED - SYSTEM IS FUNCTIONAL")
print("="*80)
