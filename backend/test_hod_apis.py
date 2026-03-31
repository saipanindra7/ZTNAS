"""
Test script for HOD API endpoints
Tests all HOD dashboard and management endpoints
"""

import requests
import json
from datetime import datetime

BASE_URL = "http://localhost:8000/api/v1"

# Test user credentials
HOD_USERNAME = "hod1"
HOD_PASSWORD = "password123"

print("=" * 70)
print("HOD API ENDPOINTS TEST")
print("=" * 70)

# Step 1: Login as HOD
print("\n[STEP 1] Login as HOD...")
login_response = requests.post(
    f"{BASE_URL}/auth/login",
    json={"username": HOD_USERNAME, "password": HOD_PASSWORD}
)
print(f"Status: {login_response.status_code}")

if login_response.status_code == 200:
    token = login_response.json().get("access_token")
    print(f"* Token received: {token[:50]}...")
else:
    print(f"ERROR: {login_response.json()}")
    exit(1)

headers = {"Authorization": f"Bearer {token}"}

# Step 2: Get HOD Dashboard Summary
print("\n[STEP 2] Get HOD dashboard summary...")
dashboard_response = requests.get(
    f"{BASE_URL}/hod/dashboard-summary",
    headers=headers
)
print(f"Status: {dashboard_response.status_code}")
if dashboard_response.status_code == 200:
    dashboard = dashboard_response.json()
    print(f"Dashboard: {json.dumps(dashboard, indent=2)}")
else:
    print(f"ERROR: {dashboard_response.json()}")

# Step 3: Get Faculty List
print("\n[STEP 3] Get faculty list...")
faculty_response = requests.get(
    f"{BASE_URL}/hod/faculty",
    headers=headers
)
print(f"Status: {faculty_response.status_code}")
if faculty_response.status_code == 200:
    faculty_list = faculty_response.json()
    print(f"Faculty found: {len(faculty_list)}")
    if faculty_list:
        print(f"First faculty: {json.dumps(faculty_list[0], indent=2)}")
else:
    print(f"ERROR: {faculty_response.json()}")

# Step 4: Get Students List
print("\n[STEP 4] Get students list...")
students_response = requests.get(
    f"{BASE_URL}/hod/students",
    headers=headers
)
print(f"Status: {students_response.status_code}")
if students_response.status_code == 200:
    students_list = students_response.json()
    print(f"Students found: {len(students_list)}")
    if students_list:
        print(f"First student: {json.dumps(students_list[0], indent=2)}")
else:
    print(f"ERROR: {students_response.json()}")

# Step 5: Get Attendance Overview
print("\n[STEP 5] Get attendance overview...")
attendance_response = requests.get(
    f"{BASE_URL}/hod/attendance-overview",
    headers=headers
)
print(f"Status: {attendance_response.status_code}")
if attendance_response.status_code == 200:
    attendance_overview = attendance_response.json()
    print(f"Classes found: {len(attendance_overview)}")
    if attendance_overview:
        print(f"First class: {json.dumps(attendance_overview[0], indent=2)}")
else:
    print(f"ERROR: {attendance_response.json()}")

# Step 6: Get Audit Logs
print("\n[STEP 6] Get audit logs...")
audit_response = requests.get(
    f"{BASE_URL}/hod/audit-logs?days=30",
    headers=headers
)
print(f"Status: {audit_response.status_code}")
if audit_response.status_code == 200:
    audit_logs = audit_response.json()
    print(f"Audit logs found: {len(audit_logs)}")
    if audit_logs:
        print(f"Most recent log: {json.dumps(audit_logs[0], indent=2)}")
else:
    print(f"ERROR: {audit_response.json()}")

# Step 7: Get Underperforming Students
print("\n[STEP 7] Get underperforming students...")
underperforming_response = requests.get(
    f"{BASE_URL}/hod/underperforming-students?attendance_threshold=75&marks_threshold=50",
    headers=headers
)
print(f"Status: {underperforming_response.status_code}")
if underperforming_response.status_code == 200:
    underperforming = underperforming_response.json()
    print(f"Underperforming students: {json.dumps(underperforming, indent=2)}")
else:
    print(f"ERROR: {underperforming_response.json()}")

print("\n" + "=" * 70)
print("[SUCCESS] All HOD API tests completed!")
print("=" * 70)
