"""
Create default admin account for ZTNAS
"""

import sys
import os

# Add parent directory to path to import app modules
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, backend_dir)

from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models import User, Role
from app.utils.security import hash_password
from datetime import datetime

def create_default_admin():
    """Create default admin account"""
    db = SessionLocal()
    
    try:
        # Check if admin role exists
        admin_role = db.query(Role).filter(Role.name == "admin").first()
        if not admin_role:
            print("❌ Admin role not found. Creating...")
            admin_role = Role(
                name="admin",
                description="System Administrator with full access"
            )
            db.add(admin_role)
            db.commit()
            print("✓ Admin role created")
        
        # Check if admin user already exists
        admin_user = db.query(User).filter(User.username == "admin").first()
        if admin_user:
            print("⚠ Admin user already exists!")
            print(f"  Username: {admin_user.username}")
            print(f"  Email: {admin_user.email}")
            print(f"  Created: {admin_user.created_at}")
            db.close()
            return
        
        # Create default admin user
        admin_user = User(
            username="admin",
            email="admin@ztnas.local",
            password_hash=hash_password("Admin@123456"),  # Change this in production!
            first_name="System",
            last_name="Administrator",
            is_active=True,
            created_at=datetime.utcnow()
        )
        
        # Add admin role
        admin_user.roles.append(admin_role)
        
        db.add(admin_user)
        db.commit()
        
        print("✓ Default admin account created successfully!")
        print("\n  Credentials:")
        print("  ─────────────")
        print(f"  Username: admin")
        print(f"  Email: admin@ztnas.local")
        print(f"  Password: Admin@123456")
        print("\n  ⚠️  IMPORTANT: Change this password immediately in production!")
        
    except Exception as e:
        db.rollback()
        print(f"❌ Error creating admin user: {str(e)}")
    finally:
        db.close()

if __name__ == "__main__":
    create_default_admin()
