"""
Check if HOD user has MFA methods
"""
import sys
import os

backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, backend_dir)

from config.database import SessionLocal
from app.models import User, MFAMethod

db = SessionLocal()

try:
    # Check MFA methods for each user
    for username in ["student1", "faculty1", "hod1"]:
        user = db.query(User).filter_by(username=username).first()
        if user:
            mfa_methods = db.query(MFAMethod).filter_by(user_id=user.id).all()
            print(f"{username} ({user.id}):")
            if mfa_methods:
                for mfa in mfa_methods:
                    print(f"  - {mfa.method_type}: enabled={mfa.is_enabled}, primary={mfa.is_primary}")
            else:
                print("  - No MFA methods")
        else:
            print(f"{username}: NOT FOUND")
    
except Exception as e:
    print(f"[ERROR] {e}")
    import traceback
    traceback.print_exc()
finally:
    db.close()
