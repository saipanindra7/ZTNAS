"""
Drop and recreate all database tables (for development/testing only)
WARNING: This will DELETE all data in the database!
"""

import sys
import os

# Add parent directory to path
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, backend_dir)

from config.database import Base, engine
from app.models import (
    User, Role, Permission, MFAMethod, Session, 
    DeviceRegistry, AuditLog, BehaviorProfile, Anomaly,
    Class, AttendanceRecord, MarksRecord, StudentFees,
    user_roles_association, role_permissions_association
)

def reset_database(skip_confirm=False):
    """Drop all tables and recreate them"""
    
    if not skip_confirm:
        print("[WARNING] This will DELETE all data from the database!")
        response = input("[?] Continue? (yes/no): ").lower().strip()
        
        if response != "yes":
            print("[CANCEL] Database reset cancelled")
            return False
    else:
        print("[WARNING] Resetting database (all data will be lost)...")
    
    try:
        print("\n[*] Dropping all tables...")
        Base.metadata.drop_all(bind=engine)
        print("[OK] All tables dropped")
        
        print("\n[*] Creating new tables...")
        Base.metadata.create_all(bind=engine)
        print("[OK] All tables created")
        
        print("\n[SUCCESS] Database reset complete!")
        return True
        
    except Exception as e:
        print(f"[ERROR] Error resetting database: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("[*] ZTNAS Database Reset Utility")
    print("=" * 50)
    # Skip confirmation if --force flag provided
    skip_confirm = "--force" in sys.argv
    success = reset_database(skip_confirm=skip_confirm)
    sys.exit(0 if success else 1)
