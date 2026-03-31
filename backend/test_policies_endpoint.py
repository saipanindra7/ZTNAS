"""
Test admin policies endpoint with timeout
"""
import requests

BASE_URL = "http://localhost:8000/api/v1"

# Login
login_resp = requests.post(
    f"{BASE_URL}/auth/login",
    json={"username": "admin1", "password": "password123"},
    timeout=5
)
token = login_resp.json()["access_token"]
headers = {"Authorization": f"Bearer {token}"}

# Test policies endpoint with longer timeout
print("Testing /admin/policies endpoint...")
print("Sending request...")
try:
    resp = requests.get(
        f"{BASE_URL}/admin/policies",
        headers=headers,
        timeout=15  # 15 second timeout
    )
    print(f"Status: {resp.status_code}")
    print(f"Response: {str(resp.json())[:200]}...")
except requests.exceptions.Timeout:
    print("ERROR: Request timed out after 15 seconds")
except Exception as e:
    print(f"ERROR: {e}")
