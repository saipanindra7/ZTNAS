"""
Quick seed script - populate ZTNAS with test academic data
"""

import sys
import os
from datetime import datetime, timedelta
from random import randint

backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, backend_dir)

from config.database import SessionLocal, init_db
from app.models import User, Role, Class, AttendanceRecord, MarksRecord, StudentFees
from utils.security import hash_password

print("[*] ZTNAS Academic Data Seeder")
print("=" * 60)

try:
    # Step 1: Initialize DB
    print("[1/6] Initializing database...")
    init_db()
    print("     [OK] Tables created")
    
    db = SessionLocal()
    
    # Step 2: Create roles (or fetch existing)
    print("\n[2/6] Creating roles...")
    student_role = db.query(Role).filter_by(name="student").first()
    if not student_role:
        student_role = Role(name="student", description="Student")
        db.add(student_role)
    
    faculty_role = db.query(Role).filter_by(name="faculty").first()
    if not faculty_role:
        faculty_role = Role(name="faculty", description="Faculty")
        db.add(faculty_role)
    
    hod_role = db.query(Role).filter_by(name="hod").first()
    if not hod_role:
        hod_role = Role(name="hod", description="Head of Department")
        db.add(hod_role)
    
    db.commit()
    print("     [OK] Roles ready")
    
    # Step 3: Create test users
    print("\n[3/6] Creating test users...")
    students_data = [
        ("student1", "student1@college.edu", "Alice", "Johnson"),
        ("student2", "student2@college.edu", "Bob", "Smith"),
        ("student3", "student3@college.edu", "Charlie", "Brown"),
        ("student4", "student4@college.edu", "Diana", "Prince"),
        ("student5", "student5@college.edu", "Eve", "Taylor"),
    ]
    
    students = []
    for username, email, first, last in students_data:
        user = db.query(User).filter_by(username=username).first()
        if not user:
            user = User(
                username=username,
                email=email,
                password_hash=hash_password("password123"),
                first_name=first,
                last_name=last,
                is_active=True
            )
            user.roles.append(student_role)
            db.add(user)
        students.append(user)
    
    faculty_data = [
        ("faculty1", "prof1@college.edu", "Dr.", "Smith"),
        ("faculty2", "prof2@college.edu", "Prof.", "Johnson"),
    ]
    
    faculty = []
    for username, email, first, last in faculty_data:
        user = db.query(User).filter_by(username=username).first()
        if not user:
            user = User(
                username=username,
                email=email,
                password_hash=hash_password("password123"),
                first_name=first,
                last_name=last,
                is_active=True
            )
            user.roles.append(faculty_role)
            db.add(user)
        faculty.append(user)
    
    # Create HOD user
    hod_user = db.query(User).filter_by(username="hod1").first()
    if not hod_user:
        hod_user = User(
            username="hod1",
            email="hod1@college.edu",
            password_hash=hash_password("password123"),
            first_name="Head",
            last_name="Department",
            is_active=True
        )
        hod_user.roles.append(hod_role)
        db.add(hod_user)
    
    db.commit()
    print(f"     [OK] Ensured {len(students)} students + {len(faculty)} faculty + 1 HOD")
    
    # Step 4: Create classes
    print("\n[4/6] Creating classes...")
    classes_data = [
        ("Data Structures", "CS101", faculty[0].id, 1),
        ("Database Design", "CS102", faculty[0].id, 1),
        ("Web Development", "CS103", faculty[1].id, 1),
        ("Software Engineering", "CS104", faculty[1].id, 2),
        ("Machine Learning", "CS201", faculty[0].id, 2),
    ]
    
    classes = []
    for name, code, fid, sem in classes_data:
        cls = db.query(Class).filter_by(code=code).first()
        if not cls:
            cls = Class(
                name=name,
                code=code,
                faculty_id=fid,
                department="Computer Science",
                academic_year="2025-2026",
                semester=sem,
                max_attendance_required=75
            )
            db.add(cls)
        classes.append(cls)
    
    db.commit()
    print(f"     [OK] Ensured {len(classes)} classes")
    
    # Step 5: Clean existing academic data
    print("\n[5/6] Cleaning existing academic data...")
    db.query(AttendanceRecord).delete()
    db.query(MarksRecord).delete()
    db.query(StudentFees).delete()
    db.commit()
    print("     [OK] Existing academic data cleared")
   
    att_count = 0
    marks_count = 0
    fees_count = 0
    
    # Attendance records (30 days, 5 students, 3 classes)
    print("     [+] Attendance records...")
    for student in students[:5]:
        for cls in classes[:3]:
            for day_off in range(1, 31):
                rec_date = datetime.utcnow() - timedelta(days=day_off)
                status = "PRESENT" if randint(1, 100) <= 85 else "ABSENT"
                att = AttendanceRecord(
                    student_id=student.id,
                    class_id=cls.id,
                    attendance_date=rec_date,
                    status=status,
                    marked_by=cls.faculty_id
                )
                db.add(att)
                att_count += 1
    db.commit()
    print(f"        -> {att_count} attendance records")
    
    # Marks records (6 exam types, 5 students, 3 classes)
    print("     [+] Marks records...")
    for student in students[:5]:
        for cls in classes[:3]:
            for exam in ["mid_term", "final", "quiz_1", "quiz_2", "assign1", "assign2"]:
                marks_obj = randint(60, 100)
                grade = "A+" if marks_obj >= 90 else "A" if marks_obj >= 85 else "B" if marks_obj >= 70 else "C"
                mrk = MarksRecord(
                    student_id=student.id,
                    class_id=cls.id,
                    exam_type=exam,
                    marks_obtained=float(marks_obj),
                    total_marks=100.0,
                    percentage=float(marks_obj),
                    grade=grade
                )
                db.add(mrk)
                marks_count += 1
    db.commit()
    print(f"        -> {marks_count} marks records")
    
    # Fee records (2 semesters, 5 students)
    print("     [+] Fee records...")
    for student in students[:5]:
        for sem in [1, 2]:
            paid = randint(0, 100)
            fee = StudentFees(
                student_id=student.id,
                academic_year="2025-2026",
                semester=sem,
                total_fee=50000.0,
                paid_amount=50000.0 if paid >= 60 else 25000.0 if paid >= 35 else 0,
                fee_status="PAID" if paid >= 60 else "PARTIAL" if paid >= 35 else "PENDING",
                due_date=datetime(2025, 9, 15) if sem == 1 else datetime(2026, 2, 15),
                payment_date=datetime.utcnow() - timedelta(days=15) if paid >= 35 else None
            )
            db.add(fee)
            fees_count += 1
    db.commit()
    print(f"        -> {fees_count} fee records")
    
    print("\n" + "=" * 60)
    print("[SUCCESS] Academic data seeding complete!")
    print("=" * 60)
    print(f"\nSummary:")
    print(f"  - Students: {len(students)}")
    print(f"  - Faculty: {len(faculty)}")
    print(f"  - Classes: {len(classes)}")
    print(f"  - Attendance records: {att_count}")
    print(f"  - Marks records: {marks_count}")
    print(f"  - Fee records: {fees_count}")
    print(f"\nTest Credentials:")
    print(f"  Username: student1 / Password: password123")
    print(f"  Username: faculty1 / Password: password123")
    
    db.close()
    sys.exit(0)

except Exception as e:
    print(f"\n[ERROR] {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
