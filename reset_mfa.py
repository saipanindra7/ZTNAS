#!/usr/bin/env python3
"""
ZTNAS Database Reset Script
Resets MFA setup status for all users
"""

import sys
sys.path.insert(0, '/d/projects/ztnas/backend')

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models import User, MFAMethod
from app.config import database_url

# Create database connection
engine = create_engine(database_url)
Session = sessionmaker(bind=engine)
db = Session()

try:
    print("🔄 Resetting MFA setup status for all users...")
    
    # Get all users
    users = db.query(User).all()
    print(f"Found {len(users)} users")
    
    # Delete all MFA methods for non-admin users
    for user in users:
        if user.username != 'admin':
            # Delete existing MFA methods
            mfa_methods = db.query(MFAMethod).filter_by(user_id=user.id).all()
            for method in mfa_methods:
                db.delete(method)
                print(f"  ✓ Deleted MFA method for {user.username}")
    
    db.commit()
    print("\n✅ MFA setup reset complete!")
    print(f"All non-admin users can now setup MFA fresh.")
    
    # Print user list
    print("\n📋 User List:")
    users = db.query(User).all()
    for user in users:
        mfa_count = db.query(MFAMethod).filter_by(user_id=user.id).count()
        print(f"  • {user.username} ({user.email}) - MFA Methods: {mfa_count}")

except Exception as e:
    print(f"❌ Error: {str(e)}")
    db.rollback()

finally:
    db.close()
