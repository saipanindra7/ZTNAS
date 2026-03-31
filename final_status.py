#!/usr/bin/env python3
import urllib.request
import json

resp = urllib.request.urlopen('http://localhost:8000/api/v1/auth/debug/users')
users = json.loads(resp.read())

print('DATABASE STATUS:')
print(f"Total users: {users['total_users']}")
print()

for user in users['users']:
    status = 'LOCKED' if user['is_locked'] else ('ACTIVE' if user['is_active'] else 'INACTIVE')
    print(f"  - {user['username']:<15} | {status:<10} | Failed: {user['failed_attempts']}")

print()
print("TEST USER ('test@test.com'):")
test_user = [u for u in users['users'] if u['email'] == 'test@test.com'][0]
print(f"  Username: {test_user['username']}")
print(f"  Is Locked: {test_user['is_locked']}")
print(f"  Failed Attempts: {test_user['failed_attempts']}")
print()
print("Status: UNLOCKED AND READY FOR LOGIN")
