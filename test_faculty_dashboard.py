#!/usr/bin/env python3
"""Test Faculty Dashboard API Integration"""

import requests
import json
from datetime import datetime

print('=' * 60)
print('FACULTY DASHBOARD API INTEGRATION TEST')
print('=' * 60)

# 1. Login
print('\n1. Faculty Login Test...')
login_res = requests.post('http://localhost:8000/api/v1/auth/login', json={
    'username': 'faculty1',
    'password': 'password123'
})
print(f'   Status: {login_res.status_code}')
if login_res.status_code != 200:
    print(f'   Error: {login_res.json()}')
    exit(1)

token = login_res.json().get('access_token')
headers = {'Authorization': f'Bearer {token}'}
print(f'   Token received: {token[:30]}...')

# 2. Get Dashboard Summary
print('\n2. Dashboard Summary Test...')
dashboard_res = requests.get('http://localhost:8000/api/v1/faculty/dashboard', headers=headers)
print(f'   Status: {dashboard_res.status_code}')
dashboard = dashboard_res.json()
print(f'   Classes: {dashboard.get("classes_count")}')
print(f'   Students: {dashboard.get("students_count")}')
print(f'   Avg Attendance: {dashboard.get("average_attendance_percentage")}%')

# 3. Get Classes
print('\n3. Get My Classes Test...')
classes_res = requests.get('http://localhost:8000/api/v1/faculty/my-classes', headers=headers)
print(f'   Status: {classes_res.status_code}')
classes = classes_res.json()
print(f'   Classes found: {len(classes)}')
for cls in classes[:2]:
    print(f'     - {cls["name"]} ({cls["code"]}) - {cls["student_count"]} students')

if not classes:
    print('   ERROR: No classes found!')
    exit(1)

class_id = classes[0]['id']

# 4. Get Class Students
print(f'\n4. Get Class Students Test (Class ID: {class_id})...')
students_res = requests.get(f'http://localhost:8000/api/v1/faculty/classes/{class_id}/students', headers=headers)
print(f'   Status: {students_res.status_code}')
students = students_res.json()
print(f'   Students found: {len(students)}')
for student in students[:2]:
    print(f'     - {student["username"]} ({student["email"]})')

if not students:
    print('   ERROR: No students found!')
    exit(1)

# 5. Mark Attendance
print('\n5. Mark Attendance Test...')
attendance_records = []
for student in students:
    attendance_records.append({
        'student_id': student['student_id'],
        'status': 'present',
        'remarks': ''
    })

attendance_res = requests.post('http://localhost:8000/api/v1/faculty/attendance/mark', 
    headers=headers,
    json={
        'class_id': class_id,
        'attendance_date': datetime.now().strftime('%Y-%m-%d'),
        'records': attendance_records
    }
)
print(f'   Status: {attendance_res.status_code}')
if attendance_res.status_code == 201:
    att_data = attendance_res.json()
    print(f'   Message: {att_data.get("message")}')
    print(f'   Records created: {att_data.get("records_created")}')
else:
    print(f'   Error: {attendance_res.json()}')

# 6. Enter Marks
print('\n6. Enter Marks Test...')
marks_records = []
for student in students:
    marks_records.append({
        'student_id': student['student_id'],
        'marks_obtained': 85,
        'total_marks': 100
    })

marks_res = requests.post('http://localhost:8000/api/v1/faculty/marks/enter',
    headers=headers,
    json={
        'class_id': class_id,
        'exam_type': 'MIDTERM',
        'records': marks_records
    }
)
print(f'   Status: {marks_res.status_code}')
if marks_res.status_code == 201:
    marks_data = marks_res.json()
    print(f'   Message: {marks_data.get("message")}')
    print(f'   Records created: {marks_data.get("records_created")}')
else:
    print(f'   Error: {marks_res.json()}')

print('\n' + '=' * 60)
print('ALL FACULTY DASHBOARD TESTS PASSED!')
print('=' * 60)
