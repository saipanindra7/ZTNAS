"""
Create HOD user manually
"""
import sys
import os

backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, backend_dir)

from config.database import SessionLocal
from app.models import User, Role
from utils.security import hash_password

db = SessionLocal()

try:
    # Get or create HOD role
    hod_role = db.query(Role).filter_by(name="hod").first()
    if not hod_role:
        hod_role = Role(name="hod", description="Head of Department")
        db.add(hod_role)
        db.commit()
        print("[+] Created HOD role")
    else:
        print("[+] HOD role exists")
    
    # Create or update HOD user
    hod_user = db.query(User).filter_by(username="hod1").first()
    if hod_user:
        print("[+] hod1 user already exists")
        db.close()
        sys.exit(0)
    
    # Create new HOD user
    hod_user = User(
        username="hod1",
        email="hod1@college.edu",
        password_hash=hash_password("password123"),
        first_name="Head",
        last_name="Department",
        is_active=True
    )
    hod_user.roles.append(hod_role)
    db.add(hod_user)
    db.commit()
    
    print("[SUCCESS] HOD user created!")
    print(f"  Username: hod1")
    print(f"  Email: hod1@college.edu")
    print(f"  Password: password123")
    
except Exception as e:
    print(f"[ERROR] {e}")
    import traceback
    traceback.print_exc()
finally:
    db.close()
