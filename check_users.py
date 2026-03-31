#!/usr/bin/env python3
"""Check what users are in the database"""
import sys
import os
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent / "backend"))
os.chdir(str(Path(__file__).parent / "backend"))

try:
    from config.database import SessionLocal, engine, Base
    from app.models import User
    from sqlalchemy import text
    
    # Create tables just in case
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    
    # Check all users
    users = db.query(User).all()
    print(f"Total users in database: {len(users)}")
    print()
    
    if users:
        for user in users:
            print(f"Username: {user.username}")
            print(f"Email: {user.email}")
            print(f"Is Active: {user.is_active}")
            print(f"Is Locked: {user.is_locked}")
            print(f"Failed Attempts: {user.failed_login_attempts}")
            print(f"Password Hash Length: {len(user.password_hash) if user.password_hash else 'NO HASH'}")
            print(f"Password Hash Preview: {user.password_hash[:40] if user.password_hash else 'N/A'}...")
            print("-" * 60)
    else:
        print("No users found in database!")
    
    db.close()
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
