#!/usr/bin/env python3
"""
Standalone test to simulate registration and login flow
This will help us identify exactly where credentials are failing
"""

import sys
import os
from pathlib import Path

# Add backend to path
backend_path = str(Path(__file__).parent / "backend")
sys.path.insert(0, backend_path)
os.chdir(backend_path)

try:
    print("=" * 70)
    print("STANDALONE LOGIN DIAGNOSTIC TEST")
    print("=" * 70)
    
    from config.database import SessionLocal, engine, Base
    from app.models import User, Role
    from app.services.auth_service import AuthService
    from app.schemas.auth import UserRegisterRequest, UserLoginRequest
    from utils.security import hash_password, verify_password
    
    # Initialize database
    print("\n[SETUP] Creating database tables...")
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    
    # Clean up test user if exists
    print("[SETUP] Cleaning up previous test data...")
    existing = db.query(User).filter(User.username == "testdiag").first()
    if existing:
        db.delete(existing)
        db.commit()
        print("[SETUP] Deleted existing test user")
    
    # Ensure User role exists
    print("[SETUP] Checking for User role...")
    user_role = db.query(Role).filter(Role.name == "User").first()
    if not user_role:
        print("[SETUP] Creating User role...")
        user_role = Role(name="User", description="Standard user role")
        db.add(user_role)
        db.commit()
    else:
        print("[SETUP] User role already exists")
    
    # TEST 1: Direct password hashing
    print("\n" + "=" * 70)
    print("TEST 1: Direct Password Hashing")
    print("=" * 70)
    
    test_password = "TestDiag@123"
    print(f"Original password: {test_password}")
    
    hashed = hash_password(test_password)
    print(f"Hashed password: {hashed[:50]}...")
    
    verify_result = verify_password(test_password, hashed)
    status = "PASS" if verify_result else "FAIL"
    print(f"Verify with correct password: {verify_result} ({status})")
    
    if not verify_result:
        print("CRITICAL: Password hashing/verification is broken!")
        db.close()
        sys.exit(1)
    
    # TEST 2: Direct user registration via AuthService
    print("\n" + "=" * 70)
    print("TEST 2: User Registration via AuthService")
    print("=" * 70)
    
    register_data = UserRegisterRequest(
        email="testdiag@example.com",
        username="testdiag",
        password=test_password,
        first_name="Test",
        last_name="Diag"
    )
    
    print(f"Registering user: {register_data.username}")
    print(f"Email: {register_data.email}")
    print(f"Password: {register_data.password}")
    
    success, message, user = AuthService.register_user(
        db=db,
        user_data=register_data,
        ip_address="127.0.0.1",
        device_info={"user_agent": "test"}
    )
    
    print(f"Register result: {success} - {message}")
    
    if not success:
        print("CRITICAL: Registration failed!")
        print(f"Error: {message}")
        db.close()
        sys.exit(1)
    
    print(f"User created with ID: {user.id}")
    print(f"User password_hash: {user.password_hash[:50]}...")
    print(f"User is_active: {user.is_active}")
    
    # TEST 3: Query user back from database
    print("\n" + "=" * 70)
    print("TEST 3: Query User from Database")
    print("=" * 70)
    
    queried_user = db.query(User).filter(User.username == "testdiag").first()
    
    if not queried_user:
        print("CRITICAL: Could not query user from database!")
        db.close()
        sys.exit(1)
    
    print(f"User found: {queried_user.username}")
    print(f"Stored hash: {queried_user.password_hash[:50]}...")
    print(f"Is active: {queried_user.is_active}")
    print(f"Is locked: {queried_user.is_locked}")
    print(f"Failed attempts: {queried_user.failed_login_attempts}")
    
    # TEST 4: Direct password verification against stored hash
    print("\n" + "=" * 70)
    print("TEST 4: Direct Password Verification Against Stored Hash")
    print("=" * 70)
    
    stored_verify = verify_password(test_password, queried_user.password_hash)
    status = "PASS" if stored_verify else "FAIL"
    print(f"Verify against stored hash: {stored_verify} ({status})")
    
    if not stored_verify:
        print("CRITICAL: Cannot verify password against stored hash!")
        print(f"Password: {test_password}")
        print(f"Stored hash: {queried_user.password_hash}")
        db.close()
        sys.exit(1)
    
    # TEST 5: Login via AuthService
    print("\n" + "=" * 70)
    print("TEST 5: Login via AuthService")
    print("=" * 70)
    
    login_data = UserLoginRequest(
        username="testdiag",
        password=test_password
    )
    
    print(f"Attempting login with: {login_data.username}")
    print(f"Password: {login_data.password}")
    
    success, message, token_data = AuthService.login_user(
        db=db,
        login_data=login_data,
        ip_address="127.0.0.1",
        device_info={"user_agent": "test"}
    )
    
    print(f"Login result: {success} - {message}")
    
    if success:
        print(f"LOGIN SUCCESSFUL!")
        print(f"Token data: {token_data}")
    else:
        print(f"LOGIN FAILED!")
        print(f"Error message: {message}")
        
        # Additional diagnostics
        db.refresh(queried_user)
        print(f"\nUser state after failed login:")
        print(f"  is_active: {queried_user.is_active}")
        print(f"  is_locked: {queried_user.is_locked}")
        print(f"  failed_attempts: {queried_user.failed_login_attempts}")
        
        db.close()
        sys.exit(1)
    
    # TEST 6: Wrong password
    print("\n" + "=" * 70)
    print("TEST 6: Login with Wrong Password")
    print("=" * 70)
    
    wrong_login = UserLoginRequest(
        username="testdiag",
        password="WrongPassword@123"
    )
    
    print(f"Attempting login with wrong password...")
    
    success, message, token_data = AuthService.login_user(
        db=db,
        login_data=wrong_login,
        ip_address="127.0.0.1",
        device_info={"user_agent": "test"}
    )
    
    print(f"Login result: {success} - {message}")
    
    if success:
        print("CRITICAL: Wrong password was accepted!")
        db.close()
        sys.exit(1)
    else:
        print(f"Correctly rejected wrong password")
    
    # Cleanup
    print("\n" + "=" * 70)
    print("CLEANUP")
    print("=" * 70)
    
    db.delete(queried_user)
    db.commit()
    db.close()
    
    print("\n" + "=" * 70)
    print("ALL TESTS PASSED - LOGIN SYSTEM IS WORKING CORRECTLY")
    print("=" * 70)
    
except Exception as e:
    print(f"\nERROR: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
