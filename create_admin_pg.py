#!/usr/bin/env python3
"""
Create Admin Account in PostgreSQL Database
"""

import psycopg2
from psycopg2.extras import RealDictCursor
import hashlib
import os

# Database connection
try:
    conn = psycopg2.connect(
        host="localhost",
        database="ztnas",
        user="postgres",
        password="postgres",
        port=5432
    )
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    print("✅ Connected to PostgreSQL\n")
    
    # Check if admin user exists
    cursor.execute("SELECT id FROM users WHERE username = %s", ("admin",))
    admin_exists = cursor.fetchone()
    
    if admin_exists:
        print("⚠️ Admin user already exists")
    else:
        # Hash password
        password_hash = hashlib.sha256("admin".encode()).hexdigest()
        
        # Create admin user
        cursor.execute("""
            INSERT INTO users (username, email, password_hash, first_name, last_name, is_active)
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING id
        """, ("admin", "admin@ztnas.local", password_hash, "System", "Administrator", True))
        
        admin_id = cursor.fetchone()['id']
        print(f"✅ Admin user created (ID: {admin_id})")
        
        # Get admin role ID
        cursor.execute("SELECT id FROM roles WHERE name = %s", ("admin",))
        admin_role = cursor.fetchone()
        
        if admin_role:
            admin_role_id = admin_role['id']
            
            # Assign admin role to user
            cursor.execute("""
                INSERT INTO user_roles (user_id, role_id)
                VALUES (%s, %s)
            """, (admin_id, admin_role_id))
            
            print(f"✅ Admin role assigned")
        else:
            print("⚠️ Admin role not found, creating...")
            
            # Create admin role if it doesn't exist
            cursor.execute("""
                INSERT INTO roles (name, description)
                VALUES (%s, %s)
                RETURNING id
            """, ("admin", "System Administrator"))
            
            admin_role_id = cursor.fetchone()['id']
            
            # Assign role
            cursor.execute("""
                INSERT INTO user_roles (user_id, role_id)
                VALUES (%s, %s)
            """, (admin_id, admin_role_id))
            
            print(f"✅ Admin role created and assigned")
    
    conn.commit()
    
    # Show admin account details
    cursor.execute("""
        SELECT u.id, u.username, u.email, STRING_AGG(r.name, ', ') as roles
        FROM users u
        LEFT JOIN user_roles ur ON u.id = ur.user_id
        LEFT JOIN roles r ON ur.role_id = r.id
        WHERE u.username = %s
        GROUP BY u.id, u.username, u.email
    """, ("admin",))
    
    admin = cursor.fetchone()
    print(f"\n📋 Admin Account Details:")
    print(f"   Username: {admin['username']}")
    print(f"   Email: {admin['email']}")
    print(f"   Roles: {admin['roles']}")
    
    cursor.close()
    conn.close()
    
    print("\n✅ Admin account setup complete!")
    
except Exception as e:
    print(f"❌ Error: {str(e)}")
    import traceback
    traceback.print_exc()
