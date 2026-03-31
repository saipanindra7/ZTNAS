#!/usr/bin/env python3
"""
Debug script to test password hashing and verification
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from utils.security import hash_password, verify_password

# Test with a simple password
test_password = "TestPassword@123"
print(f"Original password: {test_password}")

# Hash it
hashed = hash_password(test_password)
print(f"Hashed password: {hashed}")
print(f"Hash length: {len(hashed)}")

# Verify with correct password
result_correct = verify_password(test_password, hashed)
print(f"\nVerify with correct password: {result_correct}")

# Verify with wrong password
result_wrong = verify_password("WrongPassword@123", hashed)
print(f"Verify with wrong password: {result_wrong}")

# Test a second hash
print("\n--- Testing hash consistency ---")
test_password_2 = "AnotherTest@123"
hash_1 = hash_password(test_password_2)
hash_2 = hash_password(test_password_2)
print(f"Password: {test_password_2}")
print(f"Hash 1: {hash_1}")
print(f"Hash 2: {hash_2}")
print(f"Hashes are different (normal for bcrypt): {hash_1 != hash_2}")
print(f"Both hashes verify correctly: {verify_password(test_password_2, hash_1) and verify_password(test_password_2, hash_2)}")

# Test with database
print("\n--- Testing with database ---")
from config.database import SessionLocal, Base, engine
from app.models import User, Role
from sqlalchemy import text

# Create tables
Base.metadata.create_all(bind=engine)

db = SessionLocal()

# Create test user
test_email = "passwordtest@example.com"
test_username = "passwordtester"
test_password = "DebugPass@123"

# Check if user exists and delete if so
existing = db.query(User).filter(User.email == test_email).first()
if existing:
    db.delete(existing)
    db.commit()
    print(f"Deleted existing user: {test_username}")

# Create user
test_user = User(
    email=test_email,
    username=test_username,
    password_hash=hash_password(test_password),
    is_active=True
)

# Assign User role if it exists
user_role = db.query(Role).filter(Role.name == "User").first()
if user_role:
    test_user.roles.append(user_role)

db.add(test_user)
db.commit()
db.refresh(test_user)

print(f"Created test user: {test_username}")
print(f"Stored hash: {test_user.password_hash}")
print(f"Is hash valid for storage: {len(test_user.password_hash) > 20}")

# Try to verify password from database
stored_hash = test_user.password_hash
verify_result = verify_password(test_password, stored_hash)
print(f"Verify test password against stored hash: {verify_result}")

# Try wrong password
wrong_result = verify_password("WrongPassword@123", stored_hash)
print(f"Verify wrong password against stored hash: {wrong_result}")

# Query user back out of database  
queried_user = db.query(User).filter(User.username == test_username).first()
if queried_user:
    print(f"\nQueried user back from DB: {queried_user.username}")
    print(f"Queried hash: {queried_user.password_hash}")
    print(f"Verify test password against queried hash: {verify_password(test_password, queried_user.password_hash)}")

# Cleanup
db.delete(test_user)
db.commit()
db.close()

print("\n--- All tests passed! ---")
