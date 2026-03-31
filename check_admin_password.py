#!/usr/bin/env python3
"""Check admin account and password hash"""

import psycopg2
from psycopg2.extras import RealDictCursor
import bcrypt

def hash_password(password: str) -> str:
    """Hash password using bcrypt"""
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')

def verify_password(password: str, hashed: str) -> bool:
    """Verify password against hash"""
    try:
        return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
    except Exception as e:
        print(f"Error verifying password: {e}")
        return False

try:
    conn = psycopg2.connect(
        host='localhost',
        database='ztnas_db',
        user='postgres',
        password='Admin@12'
    )
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    # Check if admin user exists
    cursor.execute('SELECT id, username, email, password_hash, is_locked, failed_login_attempts FROM users WHERE username = %s', ('admin',))
    admin = cursor.fetchone()
    
    if admin:
        print('✅ Admin user found:')
        print(f'   ID: {admin["id"]}')
        print(f'   Username: {admin["username"]}')
        print(f'   Email: {admin["email"]}')
        print(f'   Locked: {admin["is_locked"]}')
        print(f'   Failed attempts: {admin["failed_login_attempts"]}')
        print(f'   Password hash: {admin["password_hash"][:50]}...')
        
        # Test if password "admin" works with this hash
        test_password = "admin"
        print(f'\n🔍 Testing password "{test_password}":')
        if admin["password_hash"]:
            is_valid = verify_password(test_password, admin["password_hash"])
            print(f'   Password matches: {is_valid}')
        else:
            print(f'   ⚠️  Password hash is empty/null')
        
        # If password doesn't match, create new hash
        if not admin["password_hash"] or not verify_password(test_password, admin["password_hash"]):
            print(f'\n⚠️  Password mismatch! Fixing password hash...')
            new_hash = hash_password(test_password)
            cursor.execute(
                'UPDATE users SET password_hash = %s WHERE id = %s',
                (new_hash, admin['id'])
            )
            conn.commit()
            print(f'✅ Password hash updated!')
    else:
        print('❌ Admin user not found!')
        print('Creating admin account...')
        
        # Create admin with correct password hash
        hashed_pwd = hash_password('admin')
        cursor.execute('''
            INSERT INTO users (username, email, password_hash, first_name, last_name, is_active, is_locked, failed_login_attempts)
            VALUES (%s, %s, %s, %s, %s, TRUE, FALSE, 0)
            RETURNING id
        ''', ('admin', 'admin@ztnas.local', hashed_pwd, 'System', 'Administrator'))
        
        admin_id = cursor.fetchone()['id']
        
        # Assign admin role
        cursor.execute('SELECT id FROM roles WHERE name = %s', ('admin',))
        admin_role = cursor.fetchone()
        
        if admin_role:
            cursor.execute('''
                INSERT INTO user_roles (user_id, role_id)
                VALUES (%s, %s)
            ''', (admin_id, admin_role['id']))
            print(f'✅ Admin role assigned')
        
        conn.commit()
        print(f'✅ Admin account created!')
        print(f'   Username: admin')
        print(f'   Password: admin')
    
    cursor.close()
    conn.close()
    
except Exception as e:
    print(f'❌ Error: {e}')
    import traceback
    traceback.print_exc()
