from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from app.schemas.auth import (
    UserRegisterRequest,
    UserLoginRequest,
    TokenResponse,
    RefreshTokenRequest,
    ChangePasswordRequest,
    UserDetail,
    SuccessResponse,
    ErrorResponse
)
from app.services.auth_service import AuthService
from utils.security import verify_access_token, verify_refresh_token, create_access_token
from utils.rate_limiting import limiter
from utils.account_lockout import AccountLockoutPolicy
from config.database import get_db
from config.settings import settings
from datetime import timedelta
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/auth", tags=["Authentication"])


def _is_admin_user(user) -> bool:
    """Return True if the user has admin role."""
    return any(role.name.lower() == "admin" for role in user.roles)


def _is_mfa_exempt_path(path: str) -> bool:
    """Allow unverified users to access MFA setup and limited auth endpoints."""
    allowed_exact_paths = {
        "/api/v1/auth/me",
        "/api/v1/auth/logout",
        "/api/v1/auth/refresh",
    }
    if path in allowed_exact_paths:
        return True
    return path.startswith("/api/v1/mfa")

def get_token(request: Request) -> str:
    """Extract token from Authorization header"""
    auth_header = request.headers.get("Authorization", "")
    if not auth_header:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authorization header",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not auth_header.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization header",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return auth_header[7:]  # Remove "Bearer " prefix

def get_current_user(
    request: Request,
    token: str = Depends(get_token),
    db: Session = Depends(get_db)
):
    """Dependency to get current authenticated user"""
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    payload = verify_access_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        )
    
    from app.models import User
    user = db.query(User).filter(User.id == int(user_id)).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )

    # Enforce mandatory MFA for all non-admin users except MFA setup/status endpoints.
    if settings.MFA_REQUIRED and not _is_admin_user(user):
        from app.services.mfa_service import MFAService
        has_verified_mfa = MFAService.has_verified_mfa(user)
        if not has_verified_mfa and not _is_mfa_exempt_path(request.url.path):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "code": "MFA_REQUIRED",
                    "message": "MFA setup is required before accessing this resource.",
                    "setup_endpoint": "/api/v1/mfa/status"
                }
            )
    
    return user

@router.post("/register", response_model=UserDetail, status_code=status.HTTP_201_CREATED)
@limiter.limit("3/hour")  # Rate limit: 3 registrations per hour per IP
def register(
    user_data: UserRegisterRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    """Register a new user - Rate limited to 3 per hour per IP"""
    
    ip_address = request.client.host if request.client else None
    device_info = {
        "user_agent": request.headers.get("user-agent", "Unknown")
    }
    
    success, message, user = AuthService.register_user(
        db=db,
        user_data=user_data,
        ip_address=ip_address,
        device_info=device_info
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=message
        )
    
    return user

@router.post("/login", response_model=TokenResponse)
@limiter.limit("5/minute")  # Rate limit: 5 attempts per minute per IP
def login(
    login_data: UserLoginRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    """User login and token generation - Rate limited to 5/minute per IP"""
    
    ip_address = request.client.host if request.client else None
    device_info = {
        "user_agent": request.headers.get("user-agent", "Unknown"),
        "device_name": login_data.device_name if login_data.device_name else "Unknown Device"
    }
    
    # Check account lockout before attempting login
    from app.models import User
    user = db.query(User).filter(User.username == login_data.username).first()
    
    if user:
        is_locked, lock_message = AccountLockoutPolicy.check_account_locked(user, db)
        if is_locked:
            logger.warning(
                f"Login attempt on locked account: {user.username}",
                extra={
                    "user_id": user.id,
                    "ip_address": ip_address,
                    "event": "LOGIN_ATTEMPT_LOCKED_ACCOUNT"
                }
            )
            raise HTTPException(
                status_code=status.HTTP_423_LOCKED,
                detail=lock_message
            )
    
    success, message, token_data = AuthService.login_user(
        db=db,
        login_data=login_data,
        ip_address=ip_address,
        device_info=device_info
    )
    
    if not success:
        # Record failed login attempt
        if user:
            should_lock, lock_msg = AccountLockoutPolicy.record_failed_login(
                user, db, ip_address, device_info
            )
            if should_lock:
                raise HTTPException(
                    status_code=status.HTTP_423_LOCKED,
                    detail=lock_msg
                )
        
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=message
        )
    
    # Reset failed attempts on successful login
    if user:
        AccountLockoutPolicy.record_successful_login(user, db)
    
    return TokenResponse(
        access_token=token_data["access_token"],
        refresh_token=token_data["refresh_token"],
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )

@router.post("/refresh", response_model=TokenResponse)
@limiter.limit("10/minute")  # Rate limit: 10 refresh attempts per minute per IP
def refresh_token(
    request: Request,
    refresh_request: RefreshTokenRequest,
    db: Session = Depends(get_db)
):
    """Refresh access token using refresh token - Rate limited to 10/minute per IP"""
    
    payload = verify_refresh_token(refresh_request.refresh_token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token"
        )
    
    user_id = payload.get("sub")
    
    from app.models import User
    user = db.query(User).filter(User.id == int(user_id)).first()
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive"
        )
    
    # Create new access token
    token_data = {
        "sub": str(user.id),
        "email": user.email,
        "username": user.username,
        "roles": [role.name for role in user.roles]
    }
    
    new_access_token = create_access_token(token_data)
    new_refresh_token = create_access_token(
        token_data,
        expires_delta=timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    )
    
    logger.info(f"Access token refreshed for user: {user.username}")
    
    return TokenResponse(
        access_token=new_access_token,
        refresh_token=new_refresh_token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )

@router.post("/change-password", response_model=SuccessResponse)
def change_password(
    change_password_data: ChangePasswordRequest,
    request: Request,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Change user password - requires authentication"""
    
    ip_address = request.client.host if request.client else None
    
    success, message = AuthService.change_password(
        db=db,
        user_id=current_user.id,
        change_password_data=change_password_data,
        ip_address=ip_address
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=message
        )
    
    return SuccessResponse(
        success=True,
        message=message
    )

@router.post("/logout", response_model=SuccessResponse)
def logout(
    request: Request,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Logout user"""
    
    token = request.headers.get("Authorization", "").replace("Bearer ", "")
    ip_address = request.client.host if request.client else None
    
    success, message = AuthService.logout_user(
        db=db,
        user_id=current_user.id,
        token=token,
        ip_address=ip_address
    )
    
    return SuccessResponse(
        success=success,
        message=message
    )

@router.post("/admin/unlock-account/{user_id}", response_model=SuccessResponse, tags=["Admin"])
def admin_unlock_account(
    user_id: int,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Admin endpoint to unlock a locked user account - Requires admin role"""
    
    # Check if current user is admin
    from app.models import User
    if not any(role.name.lower() == "admin" for role in current_user.roles):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can unlock accounts"
        )
    
    # Get the user to unlock
    user_to_unlock = db.query(User).filter(User.id == user_id).first()
    if not user_to_unlock:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Unlock the account
    AccountLockoutPolicy.admin_unlock_account(
        user_to_unlock,
        db,
        admin_id=current_user.id
    )
    
    logger.info(
        f"Account unlocked by admin: {user_to_unlock.username}",
        extra={
            "user_id": user_to_unlock.id,
            "admin_id": current_user.id,
            "event": "ADMIN_UNLOCK_ACCOUNT"
        }
    )
    
    return SuccessResponse(
        success=True,
        message=f"Account '{user_to_unlock.username}' has been unlocked successfully"
    )

@router.get("/admin/account-status/{user_id}", tags=["Admin"])
def admin_get_account_status(
    user_id: int,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Admin endpoint to view account security status - Requires admin role"""
    
    # Check if current user is admin
    from app.models import User
    if not any(role.name.lower() == "admin" for role in current_user.roles):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can view account status"
        )
    
    # Get the user
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Return account status
    return AccountLockoutPolicy.get_account_status(user)

# DEBUG ENDPOINT - Remove in production
@router.get("/debug/users", tags=["Debug"])
def debug_list_users(db: Session = Depends(get_db)):
    """DEBUG: List all users and their info (remove in production!)"""
    from app.models import User
    users = db.query(User).all()
    
    result = []
    for user in users:
        result.append({
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "is_active": user.is_active,
            "is_locked": user.is_locked,
            "failed_attempts": user.failed_login_attempts,
            "password_hash_length": len(user.password_hash) if user.password_hash else 0,
            "password_hash_preview": user.password_hash[:40] if user.password_hash else None,
            "created_at": user.created_at,
            "last_login": user.last_login
        })
    
    return {
        "total_users": len(users),
        "users": result
    }

@router.post("/debug/test-login/{username}/{password}", tags=["Debug"])
def debug_test_login(username: str, password: str, db: Session = Depends(get_db)):
    """DEBUG: Test password verification manually"""
    from app.models import User
    from utils.security import verify_password
    
    user = db.query(User).filter(User.username == username).first()
    
    if not user:
        return {"success": False, "message": f"User '{username}' not found"}
    
    if not user.password_hash:
        return {"success": False, "message": f"User has no password hash"}
    
    result = verify_password(password, user.password_hash)
    
    return {
        "username": username,
        "user_found": True,
        "password_correct": result,
        "is_active": user.is_active,
        "is_locked": user.is_locked,
        "failed_attempts": user.failed_login_attempts,
        "password_hash_preview": user.password_hash[:40]
    }

@router.get("/me", response_model=UserDetail)
def get_current_user_info(current_user = Depends(get_current_user)):
    """Get current authenticated user info"""
    return current_user

@router.get("/users")
def list_users(
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List all users - requires authentication"""
    from app.models import User
    
    users = db.query(User).all()
    
    result = []
    for user in users:
        result.append({
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "first_name": user.first_name or "",
            "last_name": user.last_name or "",
            "is_active": user.is_active,
            "is_locked": user.is_locked,
            "created_at": user.created_at,
            "last_login": user.last_login
        })
    
    return {
        "total_users": len(users),
        "users": result
    }

@router.delete("/users/{user_id}")
def delete_user(
    user_id: int,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a user - requires authentication"""
    from app.models import User
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    db.delete(user)
    db.commit()
    
    logger.info(f"User '{user.username}' deleted by '{current_user.username}'")
    
    return SuccessResponse(
        success=True,
        message=f"User '{user.username}' has been deleted"
    )

# ========================================
# AUDIT LOGS & POLICIES (For Dashboard)
# ========================================

@router.get("/audit/logs")
def get_audit_logs(
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db),
    limit: int = 50
):
    """Get audit logs for dashboard"""
    from app.models import AuditLog
    
    logs = db.query(AuditLog).order_by(
        AuditLog.timestamp.desc()
    ).limit(limit).all()
    
    return {
        "logs": [
            {
                "id": log.id,
                "user_id": log.user_id,
                "action": log.action,
                "status": log.status,
                "timestamp": log.timestamp,
                "ip_address": log.ip_address,
                "details": log.details if log.details else {}
            }
            for log in logs
        ],
        "total": len(logs)
    }

@router.get("/policies")
def get_access_policies(
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get access policies for dashboard"""
    return {
        "policies": [
            {
                "id": 1,
                "name": "HOD Access Policy",
                "description": "Full access for HOD - All department resources",
                "risk_threshold": 0.7,
                "required_mfa": True,
                "session_timeout": 480,
                "roles": ["hod"],
                "active": True
            },
            {
                "id": 2,
                "name": "Faculty Access Policy",
                "description": "Access to teaching resources and student data",
                "risk_threshold": 0.5,
                "required_mfa": True,
                "session_timeout": 300,
                "roles": ["faculty"],
                "active": True
            },
            {
                "id": 3,
                "name": "Student Access Policy",
                "description": "Limited access - Course materials and grades only",
                "risk_threshold": 0.3,
                "required_mfa": False,
                "session_timeout": 180,
                "roles": ["student"],
                "active": True
            },
            {
                "id": 4,
                "name": "Admin Access Policy",
                "description": "System-wide admin access",
                "risk_threshold": 0.9,
                "required_mfa": True,
                "session_timeout": 600,
                "roles": ["admin"],
                "active": True
            }
        ]
    }

