#!/usr/bin/env python3
"""Check admin user role assignment"""

import psycopg2
from psycopg2.extras import RealDictCursor

try:
    conn = psycopg2.connect(
        host='localhost',
        database='ztnas_db',
        user='postgres',
        password='Admin@12'
    )
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    # Check admin user
    cursor.execute('SELECT id, username, email FROM users WHERE username = %s', ('admin',))
    user = cursor.fetchone()
    
    if not user:
        print('❌ Admin user not found')
        cursor.close()
        conn.close()
        exit(1)
    
    print(f'✅ Admin user found: ID={user["id"]}, Username={user["username"]}')
    
    # Check roles assigned to admin
    cursor.execute('''
        SELECT r.id, r.name, r.description
        FROM user_roles ur
        JOIN roles r ON ur.role_id = r.id
        WHERE ur.user_id = %s
    ''', (user['id'],))
    
    roles = cursor.fetchall()
    
    if roles:
        print(f'\n✅ Roles assigned to admin:')
        for role in roles:
            print(f'   - {role["name"]} (ID: {role["id"]})')
    else:
        print(f'\n❌ No roles assigned to admin!')
        print('   Assigning admin role...')
        
        # Get admin role ID
        cursor.execute('SELECT id FROM roles WHERE name = %s', ('admin',))
        admin_role = cursor.fetchone()
        
        if admin_role:
            cursor.execute('''
                INSERT INTO user_roles (user_id, role_id)
                VALUES (%s, %s)
            ''', (user['id'], admin_role['id']))
            conn.commit()
            print(f'   ✅ Admin role assigned!')
        else:
            print(f'   ❌ Admin role not found in database')
    
    cursor.close()
    conn.close()
    
except Exception as e:
    print(f'❌ Error: {e}')
    import traceback
    traceback.print_exc()
