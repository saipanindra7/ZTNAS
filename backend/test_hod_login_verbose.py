"""
Test HOD login with verbose output and timeout
"""
import requests
import json
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import time

BASE_URL = "http://localhost:8000/api/v1"

# Create a session with retries
session = requests.Session()
retry = Retry(connect=3, backoff_factor=0.5)
adapter = HTTPAdapter(max_retries=retry)
session.mount('http://', adapter)

print("=" * 70)
print("HOD LOGIN TEST - VERBOSE")
print("=" * 70)

username = "hod1"
password = "password123"

print(f"\n[*] Attempting login for: {username}")
print(f"[*] POST to: {BASE_URL}/auth/login")
print(f"[*] Payload: username={username}, password=***")

try:
    start_time = time.time()
    print(f"\n[*] Sending request... (timeout=10s)")
    
    response = requests.post(
        f"{BASE_URL}/auth/login",
        json={"username": username, "password": password},
        timeout=10
    )
    
    elapsed_time = time.time() - start_time
    
    print(f"[✓] Response received in {elapsed_time:.2f}s")
    print(f"[*] Status code: {response.status_code}")
    print(f"[*] Response headers: {dict(response.headers)}")
    print(f"[*] Response body: {response.text[:500]}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"\n[✓] Login successful!")
        print(f"[*] Access token: {data.get('access_token', '')[:50]}...")
    else:
        print(f"\n[✗] Login failed!")
        print(f"[*] Error: {response.json()}")
        
except requests.exceptions.Timeout:
    print(f"[✗] Request timed out after 10 seconds")
except requests.exceptions.ConnectionError as e:
    print(f"[✗] Connection error: {e}")
except Exception as e:
    print(f"[✗] Error: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 70)
