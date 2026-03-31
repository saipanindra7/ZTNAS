"""Test Faculty API Endpoints"""
import requests
import json
from datetime import datetime, timedelta

BASE_URL = "http://localhost:8000/api/v1"

print("=" * 70)
print("FACULTY API ENDPOINTS TEST")
print("=" * 70)

# Step 1: Login as faculty
print("\n[STEP 1] Login as Faculty...")
login_data = {"username": "faculty1", "password": "password123"}
resp = requests.post(f"{BASE_URL}/auth/login", json=login_data, timeout=5)
print(f"Status: {resp.status_code}")

if resp.status_code != 200:
    print("Login failed!")
    print(resp.text)
    exit(1)

token_data = resp.json()
access_token = token_data.get("access_token")
print(f"* Token received: {access_token[:30]}...")

headers = {"Authorization": f"Bearer {access_token}"}

# Step 2: Get Faculty's Classes
print("\n[STEP 2] Get my classes...")
resp = requests.get(f"{BASE_URL}/faculty/my-classes", headers=headers, timeout=5)
print(f"Status: {resp.status_code}")
classes = resp.json()
print(f"Classes: {json.dumps(classes, indent=2)}")

if not classes:
    print("ERROR: No classes found for faculty!")
    exit(1)

class_id = classes[0]["id"]
print(f"* Selected class ID: {class_id}")

# Step 3: Get Students in Class
print(f"\n[STEP 3] Get students in class {class_id}...")
resp = requests.get(f"{BASE_URL}/faculty/classes/{class_id}/students", headers=headers, timeout=5)
print(f"Status: {resp.status_code}")
students = resp.json()
print(f"Students found: {len(students)}")
if students:
    print(f"Sample student: {json.dumps(students[0], indent=2)}")

# Step 4: Mark Attendance
print(f"\n[STEP 4] Mark attendance for class {class_id}...")
today = datetime.utcnow().strftime("%Y-%m-%d")
attendance_data = {
    "class_id": class_id,
    "attendance_date": today,
    "records": [
        {"student_id": 1, "status": "PRESENT", "remarks": "On time"},
        {"student_id": 2, "status": "ABSENT", "remarks": "Sick leave"},
        {"student_id": 3, "status": "PRESENT", "remarks": None},
    ]
}
resp = requests.post(f"{BASE_URL}/faculty/attendance/mark", json=attendance_data, headers=headers, timeout=5)
print(f"Status: {resp.status_code}")
print(f"Response: {json.dumps(resp.json(), indent=2)}")

# Step 5: Get Attendance History
print(f"\n[STEP 5] Get attendance history for class {class_id}...")
resp = requests.get(f"{BASE_URL}/faculty/attendance/{class_id}?days=30", headers=headers, timeout=5)
print(f"Status: {resp.status_code}")
att_data = resp.json()
print(f"Total records: {att_data.get('records_count')}")
if att_data.get('attendance_by_date'):
    sample_date = list(att_data['attendance_by_date'].keys())[0] if att_data['attendance_by_date'] else None
    if sample_date:
        print(f"Sample date {sample_date}: {att_data['attendance_by_date'][sample_date]}")

# Step 6: Enter Marks
print(f"\n[STEP 6] Enter marks for class {class_id}...")
marks_data = {
    "class_id": class_id,
    "exam_type": "mid_term",
    "records": [
        {"student_id": 1, "marks_obtained": 95, "total_marks": 100},
        {"student_id": 2, "marks_obtained": 78, "total_marks": 100},
        {"student_id": 3, "marks_obtained": 88, "total_marks": 100},
    ]
}
resp = requests.post(f"{BASE_URL}/faculty/marks/enter", json=marks_data, headers=headers, timeout=5)
print(f"Status: {resp.status_code}")
print(f"Response: {json.dumps(resp.json(), indent=2)}")

# Step 7: Get Marks History
print(f"\n[STEP 7] Get marks history for class {class_id}...")
resp = requests.get(f"{BASE_URL}/faculty/marks/{class_id}", headers=headers, timeout=5)
print(f"Status: {resp.status_code}")
marks_history = resp.json()
print(f"Total marks records: {marks_history.get('total_records')}")
if marks_history.get('marks_by_exam'):
    sample_exam = list(marks_history['marks_by_exam'].keys())[0]
    print(f"Sample exam '{sample_exam}': {marks_history['marks_by_exam'][sample_exam]}")

# Step 8: Get Dashboard
print(f"\n[STEP 8] Get faculty dashboard...")
resp = requests.get(f"{BASE_URL}/faculty/dashboard", headers=headers, timeout=5)
print(f"Status: {resp.status_code}")
print(f"Dashboard: {json.dumps(resp.json(), indent=2)}")

print("\n" + "=" * 70)
print("[SUCCESS] All faculty API tests completed!")
print("=" * 70)
