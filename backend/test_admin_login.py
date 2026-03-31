"""
Quick admin login test
"""
import requests

BASE_URL = "http://localhost:8000/api/v1"

print("Testing admin login...")
response = requests.post(
    f"{BASE_URL}/auth/login",
    json={"username": "admin1", "password": "password123"},
    timeout=5
)

print(f"Status: {response.status_code}")
if response.status_code == 200:
    print("Login successful!")
    token = response.json().get("access_token")
    print(f"Token: {token[:50]}...")
else:
    print(f"Error: {response.json()}")
