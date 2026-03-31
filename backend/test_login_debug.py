"""
Quick login test to debug credentials
"""
import requests
import json

BASE_URL = "http://localhost:8000/api/v1"

# Test different user credentials
test_users = [
    ("faculty1", "password123"),
    ("student1", "password123"),
    ("hod1", "password123"),
]

print("Testing user credentials...")
print("=" * 60)

for username, password in test_users:
    response = requests.post(
        f"{BASE_URL}/auth/login",
        json={"username": username, "password": password}
    )
    status = "✓ OK" if response.status_code == 200 else f"✗ FAIL ({response.status_code})"
    print(f"{username}: {status}")
    if response.status_code != 200:
        print(f"  Error: {response.json()}")
    else:
        print(f"  Token: {response.json().get('access_token', '')[:40]}...")
