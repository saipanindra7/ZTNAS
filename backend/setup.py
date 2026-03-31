#!/usr/bin/env python
"""
ZTNAS Setup Script - Initialize default admin account
Run this after deploying the application
"""

import os
import sys

# Set up path
backend_path = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, backend_path)

os.chdir(backend_path)

# Now import after path is set
from app.database import SessionLocal
from app.models import User, Role, MFAMethod
from app.utils.security import hash_password
from datetime import datetime

def setup_admin():
    """Setup default admin account"""
    db = SessionLocal()
    
    try:
        print("=" * 60)
        print("ZTNAS System Setup")
        print("=" * 60)
        
        # Create admin role if it doesn't exist
        print("\n[1/4] Checking admin role...")
        admin_role = db.query(Role).filter(Role.name == "admin").first()
        if not admin_role:
            print("  Creating admin role...")
            admin_role = Role(
                name="admin",
                description="System Administrator with full access"
            )
            db.add(admin_role)
            db.commit()
            print("  ✓ Admin role created")
        else:
            print("  ✓ Admin role already exists")
        
        # Check if admin user exists
        print("\n[2/4] Checking admin user...")
        admin_user = db.query(User).filter(User.username == "admin").first()
        if admin_user:
            print("  ⚠ Admin user 'admin' already exists")
            print(f"  Email: {admin_user.email}")
            print(f"  Created: {admin_user.created_at}")
        else:
            print("  Creating admin user...")
            admin_user = User(
                username="admin",
                email="admin@ztnas.local",
                password_hash=hash_password("Admin@123456"),
                first_name="System",
                last_name="Administrator",
                is_active=True,
                created_at=datetime.utcnow()
            )
            admin_user.roles.append(admin_role)
            db.add(admin_user)
            db.commit()
            print("  ✓ Admin user created")
        
        # Reset MFA methods
        print("\n[3/4] Resetting MFA methods...")
        mfa_count = db.query(MFAMethod).count()
        if mfa_count > 0:
            print(f"  Deleting {mfa_count} existing MFA methods...")
            db.query(MFAMethod).delete()
            db.commit()
            print(f"  ✓ Deleted {mfa_count} MFA methods")
        else:
            print("  No MFA methods to delete")
        
        # Get user count
        print("\n[4/4] System status...")
        user_count = db.query(User).count()
        role_count = db.query(Role).count()
        print(f"  Total users: {user_count}")
        print(f"  Total roles: {role_count}")
        
        print("\n" + "=" * 60)
        print("✓ Setup completed successfully!")
        print("=" * 60)
        print("\nDefault Admin Credentials:")
        print("─" * 60)
        print("  Username: admin")
        print("  Password: Admin@123456")
        print("  Email: admin@ztnas.local")
        print("─" * 60)
        print("\n⚠️  IMPORTANT:")
        print("  1. Change the default password immediately in production!")
        print("  2. All users need to setup MFA on next login")
        print("  3. The backend MFA setup endpoints are now available")
        print("\n")
        
    except Exception as e:
        db.rollback()
        print(f"\n✗ Error during setup: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()
    
    return True

if __name__ == "__main__":
    try:
        success = setup_admin()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"Fatal error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
