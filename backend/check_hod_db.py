"""
Check HOD user in database
"""
import sys
import os

backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, backend_dir)

from config.database import SessionLocal
from app.models import User, Role

db = SessionLocal()

try:
    # Check if hod1 exists
    hod_user = db.query(User).filter_by(username="hod1").first()
    if not hod_user:
        print("[ERROR] hod1 user not found")
    else:
        print(f"[+] hod1 user found:")
        print(f"    ID: {hod_user.id}")
        print(f"    Email: {hod_user.email}")
        print(f"    Password hash (first 50 chars): {hod_user.password_hash[:50]}")
        print(f"    Is active: {hod_user.is_active}")
        print(f"    Is locked: {hod_user.is_locked}")
        print(f"    Roles: {[r.name for r in hod_user.roles]}")
    
    # Check if HOD role exists
    hod_role = db.query(Role).filter_by(name="hod").first()
    if hod_role:
        print(f"\n[+] HOD role found:")
        print(f"    ID: {hod_role.id}")
        print(f"    Name: {hod_role.name}")
        print(f"    Users with HOD role: {len(hod_role.users)}")
        for user in hod_role.users:
            print(f"      - {user.username}")
    else:
        print("[ERROR] HOD role not found")
    
    # List all users and their roles
    print("\n[+] All users in database:")
    all_users = db.query(User).all()
    for user in all_users:
        roles = [r.name for r in user.roles]
        print(f"    {user.username} - {user.email} - Roles: {roles}")
    
except Exception as e:
    print(f"[ERROR] {e}")
    import traceback
    traceback.print_exc()
finally:
    db.close()
