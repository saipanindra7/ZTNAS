"""
Check admin role and create admin user if needed
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
    # Check if admin role exists
    admin_role = db.query(Role).filter(Role.name == "admin").first()
    
    if not admin_role:
        print("[+] Creating admin role...")
        admin_role = Role(name="admin", description="Administrator with full system access")
        db.add(admin_role)
        db.commit()
    else:
        print("[+] Admin role exists")
    
    # Check if admin user exists
    admin_user = db.query(User).filter_by(username="admin1").first()
    
    if not admin_user:
        print("[+] Creating admin user...")
        admin_user = User(
            username="admin1",
            email="admin1@college.edu",
            password_hash=hash_password("password123"),
            first_name="System",
            last_name="Administrator",
            is_active=True
        )
        admin_user.roles.append(admin_role)
        db.add(admin_user)
        db.commit()
        print("[SUCCESS] Admin user created!")
    else:
        print("[+] Admin user already exists")
        # Ensure admin role is assigned
        if admin_role not in admin_user.roles:
            admin_user.roles.append(admin_role)
            db.commit()
            print("[+] Admin role assigned to admin1")
    
    print(f"\nAdmin User Info:")
    print(f"  Username: {admin_user.username}")
    print(f"  Email: {admin_user.email}")
    print(f"  Password: password123")
    print(f"  Roles: {[r.name for r in admin_user.roles]}")
    
except Exception as e:
    print(f"[ERROR] {e}")
    import traceback
    traceback.print_exc()
finally:
    db.close()
