#!/usr/bin/env python3
"""Check users table schema"""

import psycopg2

conn = psycopg2.connect(
    host='localhost',
    database='ztnas_db',
    user='postgres',
    password='Admin@12'
)
cursor = conn.cursor()

# Get table structure
cursor.execute("""
    SELECT column_name, data_type 
    FROM information_schema.columns 
    WHERE table_name = 'users'
    ORDER BY ordinal_position
""")

print('Users table columns:')
for row in cursor.fetchall():
    print(f'  - {row[0]}: {row[1]}')

cursor.close()
conn.close()
