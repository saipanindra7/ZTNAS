#!/usr/bin/env python3
"""Create necessary tables for marks, attendance, and fees"""

import psycopg2
from datetime import datetime

try:
    conn = psycopg2.connect(
        host='localhost',
        database='ztnas_db',
        user='postgres',
        password='Admin@12'
    )
    cursor = conn.cursor()
    
    # Drop existing tables if they exist (for fresh setup)
    cursor.execute('DROP TABLE IF EXISTS student_fees CASCADE')
    cursor.execute('DROP TABLE IF EXISTS marks_records CASCADE')
    cursor.execute('DROP TABLE IF EXISTS attendance_records CASCADE')
    cursor.execute('DROP TABLE IF EXISTS classes CASCADE')
    
    print('🗑️  Dropped existing tables')
    
    # Create classes table
    cursor.execute('''
        CREATE TABLE classes (
            id SERIAL PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            subject VARCHAR(100) NOT NULL,
            faculty_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
            semester INTEGER,
            total_students INTEGER DEFAULT 0,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    print('✅ Created classes table')
    
    # Create attendance_records table
    cursor.execute('''
        CREATE TABLE attendance_records (
            id SERIAL PRIMARY KEY,
            student_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            class_id INTEGER NOT NULL REFERENCES classes(id) ON DELETE CASCADE,
            attendance_date DATE NOT NULL,
            status VARCHAR(20) DEFAULT 'ABSENT',  -- PRESENT, ABSENT, LEAVE, SICK
            remarks TEXT,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(student_id, class_id, attendance_date)
        )
    ''')
    print('✅ Created attendance_records table')
    
    # Create marks_records table
    cursor.execute('''
        CREATE TABLE marks_records (
            id SERIAL PRIMARY KEY,
            student_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            class_id INTEGER NOT NULL REFERENCES classes(id) ON DELETE CASCADE,
            exam_type VARCHAR(50) NOT NULL,  -- MID_TERM, END_TERM, QUIZ1, QUIZ2, ASSIGNMENT
            marks_obtained DECIMAL(5, 2),
            total_marks DECIMAL(5, 2) DEFAULT 100,
            grade VARCHAR(5),  -- A, A-, B+, B, etc
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    print('✅ Created marks_records table')
    
    # Create student_fees table
    cursor.execute('''
        CREATE TABLE student_fees (
            id SERIAL PRIMARY KEY,
            student_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            academic_year VARCHAR(10) NOT NULL,  -- 2024-25, 2025-26
            semester INTEGER NOT NULL,
            total_fee DECIMAL(10, 2) NOT NULL,
            paid_amount DECIMAL(10, 2) DEFAULT 0,
            fee_status VARCHAR(20) DEFAULT 'PENDING',  -- PENDING, PARTIAL, PAID
            due_date DATE,
            payment_date DATE,
            receipt_number VARCHAR(50),
            remarks TEXT,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(student_id, academic_year, semester)
        )
    ''')
    print('✅ Created student_fees table')
    
    # Create indexes for better query performance
    cursor.execute('CREATE INDEX idx_attendance_student ON attendance_records(student_id)')
    cursor.execute('CREATE INDEX idx_attendance_class ON attendance_records(class_id)')
    cursor.execute('CREATE INDEX idx_attendance_date ON attendance_records(attendance_date)')
    
    cursor.execute('CREATE INDEX idx_marks_student ON marks_records(student_id)')
    cursor.execute('CREATE INDEX idx_marks_class ON marks_records(class_id)')
    cursor.execute('CREATE INDEX idx_marks_exam ON marks_records(exam_type)')
    
    cursor.execute('CREATE INDEX idx_fees_student ON student_fees(student_id)')
    cursor.execute('CREATE INDEX idx_fees_year ON student_fees(academic_year)')
    
    print('✅ Created indexes')
    
    conn.commit()
    print('\n✅ All tables created successfully!')
    print('   Tables: classes, attendance_records, marks_records, student_fees')
    
    cursor.close()
    conn.close()
    
except Exception as e:
    print(f'❌ Error: {e}')
    import traceback
    traceback.print_exc()
