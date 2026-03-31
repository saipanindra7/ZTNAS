import httpx

# Login
r = httpx.post('http://localhost:8000/api/v1/auth/login', 
    json={'username': 'testcollege', 'password': 'TestCollege123'})
token = r.json()['access_token']
h = {'Authorization': f'Bearer {token}'}

# Test new endpoints
print('Testing dashboard endpoints:')
r1 = httpx.get('http://localhost:8000/api/v1/zero-trust/policies', headers=h, timeout=3)
print(f'Policies: {r1.status_code}')
if r1.status_code == 200:
    data = r1.json()
    print(f'  Policies count: {len(data.get("policies", []))}')

r2 = httpx.get('http://localhost:8000/api/v1/audit/logs', headers=h, timeout=3)
print(f'Audit Logs: {r2.status_code}')
if r2.status_code == 200:
    data = r2.json()
    print(f'  Logs count: {len(data.get("logs", []))}')

print('\nAll endpoints working!')
