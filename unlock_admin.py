#!/usr/bin/env python3
"""Unlock admin account from lockout"""

import psycopg2
from psycopg2.extras import RealDictCursor
import hashlib
import bcrypt

def hash_password(password: str) -> str:
    """Hash password using bcrypt"""
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')

try:
    # Connect to PostgreSQL
    conn = psycopg2.connect(
        host='localhost',
        database='ztnas_db',
        user='postgres',
        password='Admin@12'
    )
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    # Check if admin user exists
    cursor.execute('SELECT id, username FROM users WHERE username = %s', ('admin',))
    admin = cursor.fetchone()
    
    if admin:
        # Unlock the account
        cursor.execute('''
            UPDATE users 
            SET failed_login_attempts = 0, 
                is_locked = FALSE,
                locked_until = NULL,
                last_locked_time = NULL,
                lockout_count = 0
            WHERE id = %s
        ''', (admin['id'],))
        conn.commit()
        print('✅ Admin account unlocked successfully!')
        print(f'   User ID: {admin["id"]}')
        print(f'   Username: admin')
        print('   Try logging in now with: admin / admin')
    else:
        print('❌ Admin user not found in database')
        print('   The admin account needs to be created first')
        print('   Running creation script...')
        
        # Try to create admin account
        cursor.execute('''
            INSERT INTO users (username, email, password_hash, first_name, last_name, is_locked, failed_login_attempts)
            VALUES (%s, %s, %s, %s, %s, FALSE, 0)
            RETURNING id
        ''', ('admin', 'admin@ztnas.local', hash_password('admin'), 'System', 'Administrator'))
        
        admin_id = cursor.fetchone()['id']
        
        # Assign admin role
        cursor.execute('SELECT id FROM roles WHERE name = %s', ('admin',))
        admin_role = cursor.fetchone()
        
        if admin_role:
            cursor.execute('''
                INSERT INTO user_roles (user_id, role_id)
                VALUES (%s, %s)
            ''', (admin_id, admin_role['id']))
        
        conn.commit()
        print('✅ Admin account created successfully!')
        print(f'   Username: admin')
        print(f'   Password: admin')
    
    cursor.close()
    conn.close()
    
except Exception as e:
    print(f'❌ Error: {e}')
    print('Make sure:')
    print('  1. PostgreSQL is running')
    print('  2. Database "ztnas" exists')
    print('  3. User "postgres" password is "postgres"')
