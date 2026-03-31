#!/usr/bin/env python3
"""Simple database connectivity check for ZTNAS"""
import sys
import logging
from pathlib import Path

# Suppress SQLAlchemy logging
logging.getLogger('sqlalchemy').setLevel(logging.ERROR)
logging.getLogger('sqlalchemy.engine').setLevel(logging.ERROR)
logging.getLogger('sqlalchemy.pool').setLevel(logging.ERROR)

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent / "backend"))

try:
    from config.database import SessionLocal, engine
    from app.models import User
    
    # Test database connection
    print("✓ Attempting database connection...")
    with engine.connect() as conn:
        print("✓ Database connection successful!")
    
    # Get session and check users
    session = SessionLocal()
    user_count = session.query(User).count()
    print(f"✓ Users in database: {user_count}")
    
    # List users
    users = session.query(User).all()
    if users:
        for user in users:
            print(f"\n  Username: {user.username}")
            print(f"  Email: {user.email}")
            print(f"  Active: {user.is_active}")
            print(f"  Role: {user.role if hasattr(user, 'role') else 'N/A'}")
    else:
        print("  (No users found - database exists but is empty)")
    
    session.close()
    print("\n✓ Database verification PASSED")
    sys.exit(0)
    
except ConnectionRefusedError as e:
    print(f"✗ Connection refused - PostgreSQL not running on localhost:5432")
    sys.exit(1)
except Exception as e:
    print(f"✗ Database error: {type(e).__name__}: {str(e)}")
    sys.exit(1)
