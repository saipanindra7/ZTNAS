#!/usr/bin/env python3
"""Insert sample data for testing"""

import psycopg2
from datetime import datetime, timedelta

try:
    conn = psycopg2.connect(
        host='localhost',
        database='ztnas_db',
        user='postgres',
        password='Admin@12'
    )
    cursor = conn.cursor()
    
    # Get admin/faculty users
    cursor.execute('SELECT id FROM users WHERE username IN (%s, %s)', ('admin', 'faculty1'))
    users = cursor.fetchall()
    
    if not users:
        print('❌ Admin/faculty users not found')
        cursor.close()
        conn.close()
        exit(1)
    
    faculty_id = users[0][0] if len(users) > 0 else 1
    
    # Insert sample classes
    cursor.execute('''
        INSERT INTO classes (name, subject, faculty_id, semester, total_students)
        VALUES 
            ('Data Structures', 'CSE-201', %s, 2, 35),
            ('Database Design', 'CSE-202', %s, 2, 32),
            ('Web Development', 'CSE-203', %s, 2, 38),
            ('Algorithms', 'CSE-301', %s, 3, 30)
        RETURNING id
    ''', (faculty_id, faculty_id, faculty_id, faculty_id))
    
    class_ids = [row[0] for row in cursor.fetchall()]
    print(f'✅ Inserted {len(class_ids)} classes')
    
    # Get a student to insert data for
    cursor.execute('SELECT id FROM users WHERE username = %s', ('student1',))
    student = cursor.fetchone()
    
    if student:
        student_id = student[0]
        
        # Insert attendance records (last 30 days)
        for i in range(30):
            date = (datetime.now() - timedelta(days=i)).date()
            status = 'PRESENT' if i % 7 != 0 else 'ABSENT'  # Mark as absent every 7th day
            
            for class_id in class_ids[:2]:  # For first 2 classes
                cursor.execute('''
                    INSERT INTO attendance_records (student_id, class_id, attendance_date, status)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (student_id, class_id, attendance_date) DO NOTHING
                ''', (student_id, class_id, date, status))
        
        print('✅ Inserted 60 attendance records')
        
        # Insert marks records
        marks_data = [
            (student_id, class_ids[0], 'MID_TERM', 85, 100, 'A'),
            (student_id, class_ids[0], 'END_TERM', 92, 100, 'A'),
            (student_id, class_ids[0], 'QUIZ1', 90, 100, 'A'),
            (student_id, class_ids[1], 'MID_TERM', 78, 100, 'B+'),
            (student_id, class_ids[1], 'END_TERM', 88, 100, 'A-'),
            (student_id, class_ids[1], 'QUIZ1', 85, 100, 'A'),
            (student_id, class_ids[2], 'MID_TERM', 95, 100, 'A+'),
            (student_id, class_ids[2], 'END_TERM', 89, 100, 'A'),
            (student_id, class_ids[2], 'ASSIGNMENT', 92, 100, 'A'),
        ]
        
        for student_id_val, class_id, exam_type, marks, total, grade in marks_data:
            cursor.execute('''
                INSERT INTO marks_records (student_id, class_id, exam_type, marks_obtained, total_marks, grade)
                VALUES (%s, %s, %s, %s, %s, %s)
            ''', (student_id_val, class_id, exam_type, marks, total, grade))
        
        print(f'✅ Inserted {len(marks_data)} marks records')
        
        # Insert fee records
        cursor.execute('''
            INSERT INTO student_fees 
            (student_id, academic_year, semester, total_fee, paid_amount, fee_status, due_date, payment_date)
            VALUES 
                (%s, '2024-25', 1, 50000, 50000, 'PAID', '2024-09-30', '2024-09-15'),
                (%s, '2024-25', 2, 50000, 35000, 'PARTIAL', '2025-03-31', '2025-02-20'),
                (%s, '2025-26', 1, 50000, 0, 'PENDING', '2025-09-30', NULL)
        ''', (student_id, student_id, student_id))
        
        print('✅ Inserted 3 fee records')
    
    conn.commit()
    print('\n✅ All sample data inserted successfully!')
    
    cursor.close()
    conn.close()
    
except Exception as e:
    print(f'❌ Error: {e}')
    import traceback
    traceback.print_exc()
