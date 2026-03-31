from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta
from app.models import User, Role, Session as SessionModel, AuditLog
from app.schemas.auth import UserRegisterRequest, UserLoginRequest, ChangePasswordRequest
from utils.security import hash_password, verify_password, create_access_token, create_refresh_token
from config.settings import settings
from typing import Optional, Tuple
import logging
import uuid

logger = logging.getLogger(__name__)

class AuthService:
    """Service for handling authentication operations"""
    
    @staticmethod
    def register_user(
        db: Session,
        user_data: UserRegisterRequest,
        ip_address: str = None,
        device_info: dict = None
    ) -> Tuple[bool, str, Optional[User]]:
        """
        Register a new user
        Returns: (success, message, user)
        """
        try:
            # Check if email already exists
            existing_email = db.query(User).filter(User.email == user_data.email).first()
            if existing_email:
                return False, "Email already registered", None
            
            # Check if username already exists
            existing_username = db.query(User).filter(User.username == user_data.username).first()
            if existing_username:
                return False, "Username already taken", None
            
            # Validate password strength
            if len(user_data.password) < settings.PASSWORD_MIN_LENGTH:
                return False, f"Password must be at least {settings.PASSWORD_MIN_LENGTH} characters", None
            
            # Create new user
            new_user = User(
                email=user_data.email,
                username=user_data.username,
                password_hash=hash_password(user_data.password),
                first_name=user_data.first_name,
                last_name=user_data.last_name,
                is_active=True
            )
            
            # Assign default "User" role
            user_role = db.query(Role).filter(Role.name == "User").first()
            if user_role:
                new_user.roles.append(user_role)
            
            db.add(new_user)
            db.commit()
            db.refresh(new_user)
            
            # Log registration
            AuthService._log_audit(
                db=db,
                user_id=new_user.id,
                action="user_registration",
                resource="users",
                status="success",
                ip_address=ip_address,
                device_info=device_info
            )
            
            logger.info(f"User registered successfully: {user_data.email}")
            return True, "User registered successfully", new_user
            
        except Exception as e:
            db.rollback()
            logger.error(f"Error registering user: {str(e)}")
            return False, "Error registering user", None
    
    @staticmethod
    def login_user(
        db: Session,
        login_data: UserLoginRequest,
        ip_address: str = None,
        device_info: dict = None
    ) -> Tuple[bool, str, Optional[dict]]:
        """
        Authenticate user and create session
        Returns: (success, message, token_data)
        """
        try:
            logger.info(f"[LOGIN] Attempting login for username/email: {login_data.username}")
            
            # Find user by username
            user = db.query(User).filter(
                (User.username == login_data.username) | (User.email == login_data.username)
            ).first()
            
            # Check if user exists
            if not user:
                logger.warning(f"[LOGIN] User not found: {login_data.username}")
                # Log failed login attempt
                AuthService._log_audit(
                    db=db,
                    user_id=None,
                    action="login_attempt",
                    resource="auth",
                    status="failure",
                    ip_address=ip_address,
                    device_info=device_info,
                    details="User not found"
                )
                return False, "Invalid credentials", None
            
            logger.info(f"[LOGIN] User found: {user.username}, active={user.is_active}, locked={user.is_locked}")
            
            # Check if user is active
            if not user.is_active:
                logger.warning(f"[LOGIN] User inactive: {user.username}")
                AuthService._log_audit(
                    db=db,
                    user_id=user.id,
                    action="login_attempt",
                    resource="auth",
                    status="failure",
                    ip_address=ip_address,
                    device_info=device_info,
                    details="User account is inactive"
                )
                return False, "User account is inactive", None
            
            # Check if user is locked
            if user.is_locked:
                # Check if lockout period has expired
                if user.last_locked_time and datetime.utcnow() > user.last_locked_time + timedelta(
                    minutes=settings.LOCKOUT_DURATION_MINUTES
                ):
                    # Unlock user
                    logger.info(f"[LOGIN] Unlocking user after lockout period: {user.username}")
                    user.is_locked = False
                    user.failed_login_attempts = 0
                    db.commit()
                else:
                    logger.warning(f"[LOGIN] Account locked: {user.username}")
                    AuthService._log_audit(
                        db=db,
                        user_id=user.id,
                        action="login_attempt",
                        resource="auth",
                        status="failure",
                        ip_address=ip_address,
                        device_info=device_info,
                        details="Account locked due to too many failed attempts"
                    )
                    return False, "Account temporarily locked. Try again later", None
            
            # Verify password
            logger.info(f"[LOGIN] Verifying password for user: {user.username}, password_hash exists: {bool(user.password_hash)}")
            if not verify_password(login_data.password, user.password_hash):
                logger.warning(f"[LOGIN] Invalid password for user: {user.username}, failed_attempts: {user.failed_login_attempts}")
                # Increment failed login attempts
                user.failed_login_attempts += 1
                
                # Lock account if max attempts exceeded
                if user.failed_login_attempts >= settings.MAX_LOGIN_ATTEMPTS:
                    logger.warning(f"[LOGIN] Locking account after {user.failed_login_attempts} failed attempts: {user.username}")
                    user.is_locked = True
                    user.last_locked_time = datetime.utcnow()
                
                db.commit()
                
                AuthService._log_audit(
                    db=db,
                    user_id=user.id,
                    action="login_attempt",
                    resource="auth",
                    status="failure",
                    ip_address=ip_address,
                    device_info=device_info,
                    details="Invalid password"
                )
                
                return False, "Invalid credentials", None
            
            logger.info(f"[LOGIN] Password verified successfully for user: {user.username}")
            
            # Reset failed login attempts on successful login
            user.failed_login_attempts = 0
            user.is_locked = False
            user.last_login = datetime.utcnow()
            db.commit()
            
            # Create tokens
            token_data = {
                "sub": str(user.id),
                "email": user.email,
                "username": user.username,
                "roles": [role.name for role in user.roles]
            }
            
            access_token = create_access_token(token_data)
            refresh_token = create_refresh_token(token_data)
            
            # Create session
            new_session = SessionModel(
                user_id=user.id,
                token=access_token,
                refresh_token=refresh_token,
                expires_at=datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
                refresh_token_expires_at=datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
                device_info=device_info,
                ip_address=ip_address,
                user_agent=device_info.get("user_agent") if device_info else None,
                is_active=True
            )
            db.add(new_session)
            db.commit()
            
            # Log successful login
            AuthService._log_audit(
                db=db,
                user_id=user.id,
                action="login",
                resource="auth",
                status="success",
                ip_address=ip_address,
                device_info=device_info
            )
            
            logger.info(f"User logged in successfully: {user.username}")
            
            return True, "Login successful", {
                "access_token": access_token,
                "refresh_token": refresh_token,
                "user": {
                    "id": user.id,
                    "email": user.email,
                    "username": user.username,
                    "roles": [role.name for role in user.roles]
                }
            }
            
        except Exception as e:
            db.rollback()
            logger.error(f"Error during login: {str(e)}")
            return False, "Error during login", None
    
    @staticmethod
    def change_password(
        db: Session,
        user_id: int,
        change_password_data: ChangePasswordRequest,
        ip_address: str = None
    ) -> Tuple[bool, str]:
        """
        Change user password
        Returns: (success, message)
        """
        try:
            user = db.query(User).filter(User.id == user_id).first()
            
            if not user:
                return False, "User not found"
            
            # Verify current password
            if not verify_password(change_password_data.current_password, user.password_hash):
                AuthService._log_audit(
                    db=db,
                    user_id=user_id,
                    action="password_change_attempt",
                    resource="users",
                    status="failure",
                    ip_address=ip_address,
                    details="Invalid current password"
                )
                return False, "Current password is incorrect"
            
            # Update password
            user.password_hash = hash_password(change_password_data.new_password)
            db.commit()
            
            AuthService._log_audit(
                db=db,
                user_id=user_id,
                action="password_change",
                resource="users",
                status="success",
                ip_address=ip_address
            )
            
            logger.info(f"Password changed for user: {user.username}")
            return True, "Password changed successfully"
            
        except Exception as e:
            db.rollback()
            logger.error(f"Error changing password: {str(e)}")
            return False, "Error changing password"
    
    @staticmethod
    def logout_user(
        db: Session,
        user_id: int,
        token: str,
        ip_address: str = None
    ) -> Tuple[bool, str]:
        """
        Logout user and deactivate session
        Returns: (success, message)
        """
        try:
            session = db.query(SessionModel).filter(
                SessionModel.token == token,
                SessionModel.user_id == user_id
            ).first()
            
            if session:
                session.is_active = False
                db.commit()
            
            AuthService._log_audit(
                db=db,
                user_id=user_id,
                action="logout",
                resource="auth",
                status="success",
                ip_address=ip_address
            )
            
            logger.info(f"User logged out: {user_id}")
            return True, "Logged out successfully"
            
        except Exception as e:
            db.rollback()
            logger.error(f"Error during logout: {str(e)}")
            return False, "Error during logout"
    
    @staticmethod
    def _log_audit(
        db: Session,
        user_id: Optional[int],
        action: str,
        resource: str,
        status: str,
        ip_address: Optional[str] = None,
        device_info: Optional[dict] = None,
        details: Optional[str] = None
    ):
        """Log an audit event"""
        try:
            audit_log = AuditLog(
                user_id=user_id,
                action=action,
                resource=resource,
                status=status,
                ip_address=ip_address,
                device_info=device_info,
                details=details
            )
            db.add(audit_log)
            db.commit()
        except Exception as e:
            logger.error(f"Error logging audit: {str(e)}")
