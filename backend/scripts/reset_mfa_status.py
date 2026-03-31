"""Disable MFA for all non-admin users to force re-verification."""

import os
import sys

backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, backend_dir)

from config.database import SessionLocal
from app.models import User


def reset_non_admin_mfa():
    """Set all non-admin MFA methods inactive and clear trusted devices."""
    db = SessionLocal()
    try:
        users = db.query(User).all()

        affected_users = 0
        methods_disabled = 0
        trusted_devices_reset = 0

        for user in users:
            if any(role.name.lower() == "admin" for role in user.roles):
                continue

            user_changed = False

            for method in user.mfa_methods:
                if method.is_enabled or method.is_primary:
                    method.is_enabled = False
                    method.is_primary = False
                    methods_disabled += 1
                    user_changed = True

            for device in user.devices:
                if device.is_trusted:
                    device.is_trusted = False
                    device.trust_score = 0.0
                    trusted_devices_reset += 1
                    user_changed = True

            if user_changed:
                affected_users += 1

        db.commit()

        print("MFA reset completed for non-admin users.")
        print(f"Users affected: {affected_users}")
        print(f"MFA methods disabled: {methods_disabled}")
        print(f"Trusted devices reset: {trusted_devices_reset}")

    except Exception as exc:
        db.rollback()
        print(f"Error resetting MFA status: {exc}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    reset_non_admin_mfa()
