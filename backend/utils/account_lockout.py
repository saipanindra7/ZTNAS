# Account Lockout Policy for Enterprise Security
# Prevents brute force attacks by locking accounts after failed attempts

import logging
from datetime import datetime, timedelta
from typing import Tuple, Dict, Any
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

class AccountLockoutPolicy:
    """
    Enterprise-grade account lockout policy
    - ConfigurableThresholds for failed attempts
    - Exponential backoff for lockout duration
    - Admin unlock capability
    - Audit logging of lockout events
    """
    
    # Lockout configuration
    MAX_FAILED_ATTEMPTS = 5
    INITIAL_LOCKOUT_MINUTES = 15
    LOCKOUT_MULTIPLIER = 2  # Doubles with each subsequent lockout
    MAX_LOCKOUT_HOURS = 24
    
    @staticmethod
    def check_account_locked(user: Any, db: Session) -> Tuple[bool, str]:
        """
        Check if user account is locked
        Returns: (is_locked, reason_message)
        """
        if not user.is_locked:
            return False, ""
        
        # Check if lockout has expired
        if user.locked_until and user.locked_until < datetime.utcnow():
            # Unlock and reset counters
            user.is_locked = False
            user.locked_until = None
            user.failed_login_attempts = 0
            db.commit()
            
            logger.info(
                f"Account auto-unlocked after lockout period: user_id={user.id}",
                extra={"user_id": user.id, "event": "ACCOUNT_UNLOCKED"}
            )
            return False, ""
        
        # Account still locked
        remaining_minutes = int(
            (user.locked_until - datetime.utcnow()).total_seconds() / 60
        ) if user.locked_until else 0
        
        return True, f"Account locked. Try again in {remaining_minutes} minutes."
    
    @staticmethod
    def record_failed_login(
        user: Any,
        db: Session,
        ip_address: str = None,
        device_info: Dict = None
    ) -> Tuple[bool, str]:
        """
        Record a failed login attempt
        Returns: (should_lock_account, message)
        """
        
        # Increment failed attempts
        user.failed_login_attempts = (user.failed_login_attempts or 0) + 1
        
        logger.warning(
            f"Failed login attempt for user {user.username}",
            extra={
                "user_id": user.id,
                "username": user.username,
                "failed_attempts": user.failed_login_attempts,
                "ip_address": ip_address,
                "event": "LOGIN_FAILED"
            }
        )
        
        # Check if lockout threshold reached
        if user.failed_login_attempts >= AccountLockoutPolicy.MAX_FAILED_ATTEMPTS:
            # Calculate lockout duration (exponential backoff)
            lockout_minutes = AccountLockoutPolicy.calculate_lockout_duration(user)
            
            # Lock account
            user.is_locked = True
            user.locked_until = datetime.utcnow() + timedelta(minutes=lockout_minutes)
            
            db.commit()
            
            logger.error(
                f"Account locked due to failed login attempts: user_id={user.id}",
                extra={
                    "user_id": user.id,
                    "username": user.username,
                    "failed_attempts": user.failed_login_attempts,
                    "lockout_minutes": lockout_minutes,
                    "ip_address": ip_address,
                    "event": "ACCOUNT_LOCKED",
                    "severity": "HIGH"
                }
            )
            
            return True, (
                f"Account locked due to multiple failed attempts. "
                f"Try again after {lockout_minutes} minutes or contact support."
            )
        
        db.commit()
        return False, ""
    
    @staticmethod
    def record_successful_login(user: Any, db: Session):
        """
        Reset failed login counters after successful login
        """
        if user.failed_login_attempts > 0:
            user.failed_login_attempts = 0
            user.is_locked = False
            user.locked_until = None
            
            logger.info(
                f"Failed login attempt counter reset for user: {user.username}",
                extra={
                    "user_id": user.id,
                    "username": user.username,
                    "event": "LOGIN_SUCCEEDED_RESET_COUNTER"
                }
            )
            
            db.commit()
    
    @staticmethod
    def calculate_lockout_duration(user: Any) -> int:
        """
        Calculate lockout duration with exponential backoff
        Returns: lockout duration in minutes
        """
        # Count how many times account has been locked (from metadata if available)
        lockout_count = getattr(user, "lockout_count", 0)
        
        # Calculate exponential backoff
        lockout_minutes = (
            AccountLockoutPolicy.INITIAL_LOCKOUT_MINUTES *
            (AccountLockoutPolicy.LOCKOUT_MULTIPLIER ** lockout_count)
        )
        
        # Cap at maximum lockout duration
        max_minutes = AccountLockoutPolicy.MAX_LOCKOUT_HOURS * 60
        lockout_minutes = min(lockout_minutes, max_minutes)
        
        return int(lockout_minutes)
    
    @staticmethod
    def admin_unlock_account(user: Any, db: Session, admin_id: int = None) -> bool:
        """
        Allow admin to manually unlock an account
        """
        user.is_locked = False
        user.locked_until = None
        user.failed_login_attempts = 0
        
        db.commit()
        
        logger.warning(
            f"Account unlocked by admin",
            extra={
                "user_id": user.id,
                "username": user.username,
                "admin_id": admin_id,
                "event": "ACCOUNT_UNLOCKED_BY_ADMIN"
            }
        )
        
        return True
    
    @staticmethod
    def get_account_status(user: Any) -> Dict[str, Any]:
        """
        Get detailed account security status
        """
        return {
            "user_id": user.id,
            "username": user.username,
            "is_locked": user.is_locked,
            "locked_until": user.locked_until.isoformat() if user.locked_until else None,
            "failed_login_attempts": user.failed_login_attempts or 0,
            "last_login": user.last_login.isoformat() if user.last_login else None,
            "account_created": user.created_at.isoformat() if user.created_at else None
        }
