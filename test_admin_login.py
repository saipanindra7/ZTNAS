#!/usr/bin/env python3
"""Test admin login and role retrieval"""

import requests
import json

BASE_URL = 'http://localhost:8000/api/v1'

# Step 1: Login
print('🔐 Step 1: Logging in as admin...')
login_response = requests.post(f'{BASE_URL}/auth/login', json={
    'username': 'admin',
    'password': 'admin'
})

if login_response.status_code != 200:
    print(f'❌ Login failed: {login_response.status_code}')
    print(f'   Response: {login_response.text}')
    exit(1)

login_data = login_response.json()
access_token = login_data.get('access_token')
print(f'✅ Login successful!')
print(f'   Access token: {access_token[:50]}...')

# Step 2: Get user details with role
print('\n🔍 Step 2: Fetching user details...')
headers = {'Authorization': f'Bearer {access_token}'}
user_response = requests.get(f'{BASE_URL}/auth/me', headers=headers)

if user_response.status_code != 200:
    print(f'❌ Failed to fetch user: {user_response.status_code}')
    print(f'   Response: {user_response.text}')
    exit(1)

user_data = user_response.json()
print(f'✅ User details retrieved!')
print(f'   Username: {user_data.get("username")}')
print(f'   Email: {user_data.get("email")}')

# Check if roles are included
if 'roles' in user_data:
    print(f'   Roles: {json.dumps(user_data["roles"], indent=6)}')
    
    # Extract role names
    role_names = [role.get('name') for role in user_data.get('roles', [])]
    print(f'\n✅ Role names: {role_names}')
    
    if 'admin' in role_names:
        print('✅ ADMIN ROLE FOUND - Frontend will now show admin dashboard!')
    else:
        print('⚠️  Admin role not found in roles list')
else:
    print('❌ Roles field not included in response')
    print(f'   Available fields: {user_data.keys()}')

print('\n📝 Full user response:')
print(json.dumps(user_data, indent=2, default=str))
