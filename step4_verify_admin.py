#!/usr/bin/env python3
"""Step 4: Create and test admin credentials"""
import sys
import os
from pathlib import Path

root_dir = Path(__file__).parent
backend_dir = root_dir / "backend"

sys.path.insert(0, str(backend_dir))
os.chdir(str(backend_dir))

from config.database import SessionLocal, engine
from app.models import User, Role
from utils.security import hash_password, verify_password
import datetime

print("\n" + "="*60)
print("STEP 4: Admin Account Verification")
print("="*60)

db = SessionLocal()

try:
    # Check if admin user exists
    admin = db.query(User).filter(User.username == "admin").first()
    
    if not admin:
        print("\nCreating admin account...")
        
        # Create admin user
        admin = User(
            username="admin",
            email="admin@ztnas.local",
            first_name="ZTNAS",
            last_name="Administrator",
            is_active=True,
            password_hash=hash_password("Admin@Pass123")
        )
        
        # Assign admin role
        admin_role = db.query(Role).filter(Role.name == "Admin").first()
        if admin_role:
            admin.roles.append(admin_role)
        else:
            print("  [WARNING] Admin role not found in database")
        
        db.add(admin)
        db.commit()
        db.refresh(admin)
        print(f"  [SUCCESS] Admin user created!")
    else:
        print(f"\n[FOUND] Admin user exists: {admin.username}")
        print(f"  Email: {admin.email}")
        print(f"  Active: {admin.is_active}")
        print(f"  Locked: {admin.is_locked}")
    
    # List all available users for testing
    print(f"\n\nAvailable test users in database:")
    print("-" * 60)
    users = db.query(User).limit(10).all()
    for user in users:
        print(f"  Username: {user.username:20} | Email: {user.email}")
    
    print(f"\nTotal users: {db.query(User).count()}")
    
    # Test password verification
    print(f"\n\n[TEST] Testing password hashing/verification...")
    test_password = "TestPassword123"
    hashed = hash_password(test_password)
    verified = verify_password(test_password, hashed)
    print(f"  Password: {test_password}")
    print(f"  Hashed:   {hashed[:40]}...")
    print(f"  Verified: {verified}")
    
    if verified:
        print(f"  [SUCCESS] Password system working!")
    else:
        print(f"  [ERROR] Password verification failed!")
    
    # Connection test
    print(f"\n[TEST] Testing database connection...")
    with engine.connect() as conn:
        print(f"  [SUCCESS] Database connected!")
    
    print(f"\n" + "="*60)
    print("STEP 4 VERIFICATION COMPLETE")
    print("="*60)
    print(f"\n[RECOMMENDATION] Use these credentials to test login:")
    print(f"  Username: admin")
    print(f"  Password: Admin@Pass123")
    print(f"\nOr use any existing test user from the list above")
    print(f"\nCommand to test:")
    print(f"  curl -X POST http://localhost:8000/api/v1/auth/login")
    print(f"  -H 'Content-Type: application/json'")
    print(f"  -d '{{\"username\":\"admin\",\"password\":\"Admin@Pass123\"}}'")
    
    db.close()
    
except Exception as e:
    print(f"\n[ERROR] {type(e).__name__}: {str(e)}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
