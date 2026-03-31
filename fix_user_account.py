#!/usr/bin/env python
"""Script to fix locked user account and reset password"""

import sys
sys.path.insert(0, 'd:\\projects\\ztnas\\backend')

try:
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from config.settings import settings
    from app.models import User
    from utils.security import hash_password
    
    print("=" * 60)
    print("USER ACCOUNT FIX SCRIPT")
    print("=" * 60)
    
    # Create database engine
    engine = create_engine(settings.DATABASE_URL)
    Session = sessionmaker(bind=engine)
    db = Session()
    
    # Get test user
    user = db.query(User).filter(User.username == 'test').first()
    
    if user:
        print(f"\n✓ Found user: {user.username}")
        print(f"  Email: {user.email}")
        print(f"  Before: locked={user.is_locked}, failed_attempts={user.failed_login_attempts}")
        
        # Unlock and reset
        user.is_locked = False
        user.failed_login_attempts = 0
        user.last_locked_time = None
        
        # Set password: 'college123'
        user.password_hash = hash_password('college123')
        
        db.commit()
        
        print(f"\n✓ ACCOUNT FIXED!")
        print(f"  After: locked={user.is_locked}, failed_attempts={user.failed_login_attempts}")
        print(f"\n📝 NEW LOGIN CREDENTIALS:")
        print(f"  Username: test")
        print(f"  Email: test@test.com") 
        print(f"  Password: college123")
        print()
        
    else:
        print(f"\n✗ User 'test' not found!")
        all_users = db.query(User).all()
        print(f"\nAvailable users:")
        for u in all_users:
            print(f"  - {u.username} ({u.email})")
    
    db.close()
    
except Exception as e:
    print(f"\n✗ ERROR: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("=" * 60)
