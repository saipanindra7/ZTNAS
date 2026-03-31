#!/usr/bin/env python3
"""
ZTNAS Database Reset - Direct SQL Execution
Resets MFA setup status for all non-admin users
"""

import sqlite3
import os

# Database path
db_path = 'd:\\projects\\ztnas\\backend\\test.db'

if not os.path.exists(db_path):
    print(f"❌ Database not found at {db_path}")
    exit(1)

try:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("🔄 Resetting MFA setup status...")
    
    # Get list of non-admin users
    cursor.execute("""
        SELECT users.id, users.username, users.email 
        FROM users 
        LEFT JOIN user_roles ON users.id = user_roles.user_id 
        LEFT JOIN roles ON user_roles.role_id = roles.id
        WHERE roles.name IS NULL OR roles.name != 'admin'
    """)
    
    users = cursor.fetchall()
    print(f"Found {len(users)} non-admin users\n")
    
    # Delete MFA methods for non-admin users
    for user_id, username, email in users:
        cursor.execute("DELETE FROM mfa_methods WHERE user_id = ?", (user_id,))
        rows_deleted = cursor.rowcount
        if rows_deleted > 0:
            print(f"  ✓ {username} ({email}) - Removed {rows_deleted} MFA method(s)")
    
    conn.commit()
    
    # Print final status
    print("\n✅ MFA reset complete!")
    
    # Show all users and their MFA status
    print("\n📋 Final User Status:")
    cursor.execute("""
        SELECT u.username, u.email, COUNT(m.id) as mfa_count
        FROM users u
        LEFT JOIN mfa_methods m ON u.id = m.user_id
        GROUP BY u.id
    """)
    
    for row in cursor.fetchall():
        username, email, mfa_count = row
        status = "✓ MFA Ready" if mfa_count == 0 else f"MFA Methods: {mfa_count}"
        print(f"  • {username:20} ({email:30}) - {status}")
    
    conn.close()

except Exception as e:
    print(f"❌ Error: {str(e)}")
    import traceback
    traceback.print_exc()
