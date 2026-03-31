#!/usr/bin/env python3
"""
Unlock user account and optionally reset password
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
print("ACCOUNT UNLOCK & PASSWORD RESET TOOL")
print("=" * 70)

# Find the test user
user = db.query(User).filter(
    (User.username == "test") | (User.email == "test@test.com")
).first()

if not user:
    print("ERROR: User not found!")
    db.close()
    sys.exit(1)

print(f"\nUser found:")
print(f"  Username: {user.username}")
print(f"  Email: {user.email}")
print(f"  Is Locked: {user.is_locked}")
print(f"  Failed Attempts: {user.failed_login_attempts}")

# Unlock the account
print(f"\nUnlocking account...")
user.is_locked = False
user.failed_login_attempts = 0
user.last_locked_time = None
db.commit()

print("✓ Account unlocked!")
print(f"  Is Locked: {user.is_locked}")
print(f"  Failed Attempts: {user.failed_login_attempts}")

# Option to reset password
print("\n" + "=" * 70)
print("Password Reset")
print("=" * 70)
print("\nWhat would you like to do?")
print("1. Keep current password and just unlock")
print("2. Reset password to a new password")

while True:
    choice = input("\nEnter your choice (1 or 2): ").strip()
    if choice in ['1', '2']:
        break
    print("Invalid choice. Please enter 1 or 2.")

if choice == '2':
    new_password = input("Enter new password (minimum 8 characters): ").strip()
    
    if len(new_password) < 8:
        print("ERROR: Password must be at least 8 characters!")
        db.close()
        sys.exit(1)
    
    print(f"\nResetting password...")
    user.password_hash = hash_password(new_password)
    db.commit()
    
    print("✓ Password reset successfully!")
    print(f"\nNew login credentials:")
    print(f"  USERNAME/EMAIL: {user.email}")
    print(f"  PASSWORD: {new_password}")
    print(f"\nTry logging in with these credentials now.")

elif choice == '1':
    print("\n✓ Account unlocked without password change.")
    print(f"\nYour current login is:")
    print(f"  USERNAME/EMAIL: {user.email}")
    print(f"  PASSWORD: (the password you registered with)")
    
    print("\n⚠️  IMPORTANT: You need to remember what password you used during registration!")
    print("If you don't remember, please choose option 2 next time to reset the password.")

db.close()

print("\n" + "=" * 70)
print("✓ Done! Try logging in now.")
print("=" * 70)
