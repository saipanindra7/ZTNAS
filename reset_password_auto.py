#!/usr/bin/env python3
"""
Automated password reset for test user
"""

import sys
from pathlib import Path

# Add backend to path
backend_path = str(Path(__file__).parent / "backend")
sys.path.insert(0, backend_path)

from config.database import SessionLocal
from app.models import User
from utils.security import hash_password

db = SessionLocal()

print("=" * 70)
print("PASSWORD RESET - AUTOMATED")
print("=" * 70)

# Find the test user
user = db.query(User).filter(User.email == "test@test.com").first()

if not user:
    print("ERROR: User not found!")
    db.close()
    sys.exit(1)

print(f"\nResetting password for:")
print(f"  Username: {user.username}")
print(f"  Email: {user.email}")

# Set a new password
new_password = "TestPassword@123"

print(f"\nSetting password to: {new_password}")
user.password_hash = hash_password(new_password)
db.commit()

print("Password reset successfully!")
print(f"\n" + "=" * 70)
print("NEW LOGIN CREDENTIALS")
print("=" * 70)
print(f"Email/Username: test@test.com")
print(f"Password: {new_password}")
print("=" * 70)
print("\nYou can now login with these credentials at:")
print("http://localhost:5500")

db.close()
