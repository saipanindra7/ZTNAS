#!/usr/bin/env python3
"""Fix admin password with correct PBKDF2-SHA256 hashing"""

import psycopg2
from psycopg2.extras import RealDictCursor
import hashlib
import secrets

HASH_METHOD = "pbkdf2_sha256"
HASH_ITERATIONS = 100000

def hash_password(password: str) -> str:
    """Hash password using PBKDF2-SHA256 (same as backend)"""
    salt = secrets.token_hex(32)  # 64-character hex salt (32 bytes)
    hash_obj = hashlib.pbkdf2_hmac(
        'sha256',
        password.encode('utf-8'),
        salt.encode('utf-8'),
        HASH_ITERATIONS
    )
    hashed = f"{HASH_METHOD}${HASH_ITERATIONS}${salt}${hash_obj.hex()}"
    return hashed

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against PBKDF2-SHA256 hash (same as backend)"""
    try:
        if not hashed_password.startswith('pbkdf2_sha256$'):
            return False
        
        parts = hashed_password.split('$')
        if len(parts) != 4:
            return False
        
        method, iterations_str, salt, stored_hash = parts
        iterations = int(iterations_str)
        
        hash_obj = hashlib.pbkdf2_hmac(
            'sha256',
            plain_password.encode('utf-8'),
            salt.encode('utf-8'),
            iterations
        )
        computed_hash = hash_obj.hex()
        
        result = secrets.compare_digest(computed_hash, stored_hash)
        return result
    except Exception as e:
        print(f"Verification error: {e}")
        return False

try:
    conn = psycopg2.connect(
        host='localhost',
        database='ztnas_db',
        user='postgres',
        password='Admin@12'
    )
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    # Create correct password hash using PBKDF2-SHA256
    correct_hash = hash_password('admin')
    
    print('🔐 Regenerating admin password with PBKDF2-SHA256...')
    print(f'   Hash: {correct_hash[:50]}...')
    
    # Update admin password
    cursor.execute('''
        UPDATE users
        SET password_hash = %s,
            failed_login_attempts = 0,
            is_locked = FALSE,
            locked_until = NULL,
            last_locked_time = NULL,
            lockout_count = 0
        WHERE username = 'admin'
    ''', (correct_hash,))
    
    conn.commit()
    
    # Verify it was updated correctly
    cursor.execute('SELECT password_hash FROM users WHERE username = %s', ('admin',))
    updated = cursor.fetchone()
    
    if updated:
        stored_hash = updated['password_hash']
        is_valid = verify_password('admin', stored_hash)
        
        print('\n✅ Admin password updated with PBKDF2-SHA256!')
        print(f'   Password "admin" matches hash: {is_valid}')
        print(f'   Failed attempts: 0')
        print(f'   Account locked: FALSE')
        print('\n   Ready to login with: admin / admin')
    
    cursor.close()
    conn.close()
    
except Exception as e:
    print(f'❌ Error: {e}')
    import traceback
    traceback.print_exc()
