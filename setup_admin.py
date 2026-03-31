import sys
import os

# Go to backend directory and update path
os.chdir('d:\\projects\\ztnas\\backend')
sys.path.insert(0, 'd:\\projects\\ztnas\\backend')

# Test import
try:
    from config.database import SessionLocal
    from app.models import User, Role, MFAMethod
    from utils.security import hash_password
    from datetime import datetime
    
    db = SessionLocal()
    
    # Check admin role
    admin_role = db.query(Role).filter(Role.name == "admin").first()
    if not admin_role:
        admin_role = Role(name="admin", description="System Administrator")
        db.add(admin_role)
        db.commit()
        print("✓ Created admin role")
    
    # Check admin user
    admin_user = db.query(User).filter(User.username == "admin").first()
    if admin_user:
        print("Admin user already exists")
    else:
        admin_user = User(
            username="admin",
            email="admin@ztnas.local",
            password_hash=hash_password("Admin@123456"),
            first_name="System",
            last_name="Administrator",
            is_active=True
        )
        admin_user.roles.append(admin_role)
        db.add(admin_user)
        db.commit()
        print("✓ Admin created: admin / Admin@123456")
    
    # Clear MFA methods
    mfa_count = db.query(MFAMethod).count()
    if mfa_count > 0:
        db.query(MFAMethod).delete()
        db.commit()
        print(f"✓ Cleared {mfa_count} MFA methods")
    
    db.close()
    print("\n✓ Setup complete!")
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
