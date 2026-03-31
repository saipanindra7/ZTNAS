"""
Admin Management Routes
Admin-only endpoints for user management, policy management, and log analysis
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc, or_, and_
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, timedelta
from app.models import User, Role, Permission, AuditLog, DeviceRegistry, MFAMethod
from app.routes.auth import get_current_user
from app.services.mfa_service import MFAService
from utils.rate_limiting import limiter
from config.database import get_db
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/admin", tags=["Admin Management"])

# ==================== Auth Helpers ====================

def check_admin_role(current_user: User) -> User:
    """Check if user has admin role"""
    is_admin = any(role.name.lower() == "admin" for role in current_user.roles)
    
    if not is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    return current_user

# ==================== Request/Response Models ====================

class UserCreateRequest(BaseModel):
    """Create new user"""
    email: str
    username: str
    password: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    roles: List[str] = []


class UserUpdateRequest(BaseModel):
    """Update user"""
    email: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    is_active: Optional[bool] = None
    roles: Optional[List[str]] = None


class UserDetailResponse(BaseModel):
    """User detail response"""
    id: int
    email: str
    username: str
    first_name: Optional[str]
    last_name: Optional[str]
    is_active: bool
    is_locked: bool
    created_at: str
    last_login: Optional[str]
    roles: List[str]
    mfa_configured: bool


class PolicyCreateRequest(BaseModel):
    """Create access policy"""
    name: str
    description: Optional[str] = None
    resource: str
    action: str
    role_id: int


class AuditLogResponse(BaseModel):
    """Audit log response"""
    id: int
    user_id: Optional[int]
    username: Optional[str]
    action: str
    resource: Optional[str]
    status: str
    ip_address: Optional[str]
    details: Optional[str]
    timestamp: str


class UserMFAStatusUpdateRequest(BaseModel):
    """Enable or disable MFA methods for a user."""
    is_enabled: bool
    method_ids: Optional[List[int]] = None
    reset_trusted_devices: bool = True


# ==================== User Management ====================

@router.get("/users", response_model=list)
def get_all_users(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    search: Optional[str] = None
):
    """Get all users (admin only)"""
    
    admin = check_admin_role(current_user)
    
    try:
        query = db.query(User)
        
        # Apply search filter
        if search:
            query = query.filter(
                or_(
                    User.username.ilike(f"%{search}%"),
                    User.email.ilike(f"%{search}%"),
                    User.first_name.ilike(f"%{search}%"),
                    User.last_name.ilike(f"%{search}%")
                )
            )
        
        total = query.count()
        users = query.offset(skip).limit(limit).all()
        
        return [{
            "id": user.id,
            "email": user.email,
            "username": user.username,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "is_active": user.is_active,
            "is_locked": user.is_locked,
            "created_at": user.created_at.isoformat() if user.created_at else None,
            "last_login": user.last_login.isoformat() if user.last_login else None,
            "roles": [role.name for role in user.roles],
            "mfa_configured": bool(user.mfa_methods),
            "total": total
        } for user in users]
    except Exception as e:
        logger.error(f"Error getting users: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve users"
        )


@router.get("/users/{user_id}", response_model=dict)
def get_user_detail(
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user details (admin only)"""
    
    admin = check_admin_role(current_user)
    
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return {
        "id": user.id,
        "email": user.email,
        "username": user.username,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "is_active": user.is_active,
        "is_locked": user.is_locked,
        "failed_login_attempts": user.failed_login_attempts,
        "created_at": user.created_at.isoformat() if user.created_at else None,
        "last_login": user.last_login.isoformat() if user.last_login else None,
        "roles": [{"id": role.id, "name": role.name} for role in user.roles],
        "mfa_methods": [
            {
                "id": method.id,
                "type": method.method_type.value,
                "is_enabled": method.is_enabled,
                "is_primary": method.is_primary
            }
            for method in user.mfa_methods
        ],
        "devices": [
            {
                "id": device.id,
                "device_name": device.device_name,
                "device_type": device.device_type,
                "os_name": device.os_name,
                "browser_name": device.browser_name,
                "is_trusted": device.is_trusted,
                "last_seen": device.last_seen.isoformat() if device.last_seen else None
            }
            for device in user.devices
        ]
    }


@router.post("/users", status_code=status.HTTP_201_CREATED)
@limiter.limit("10/hour")
def create_user(
    user_data: UserCreateRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create new user (admin only)"""
    
    admin = check_admin_role(current_user)
    
    try:
        # Check if user exists
        existing = db.query(User).filter(
            or_(User.email == user_data.email, User.username == user_data.username)
        ).first()
        
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="User with that email or username already exists"
            )
        
        # Create new user
        from utils.security import hash_password
        
        new_user = User(
            email=user_data.email,
            username=user_data.username,
            password_hash=hash_password(user_data.password),
            first_name=user_data.first_name,
            last_name=user_data.last_name,
            is_active=True
        )
        
        # Assign roles
        if user_data.roles:
            roles = db.query(Role).filter(Role.name.in_(user_data.roles)).all()
            new_user.roles = roles
        
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        
        # Audit log
        audit_log = AuditLog(
            user_id=admin.id,
            action="user_created",
            resource="users",
            resource_id=new_user.id,
            status="success",
            ip_address=request.client.host if request.client else None,
            details=f"Admin {admin.username} created user {new_user.username}"
        )
        db.add(audit_log)
        db.commit()
        
        logger.info(f"Admin {admin.id} created user {new_user.id}")
        
        return {
            "success": True,
            "message": "User created",
            "user_id": new_user.id
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating user: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create user"
        )


@router.patch("/users/{user_id}")
def update_user(
    user_id: int,
    user_data: UserUpdateRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update user (admin only)"""
    
    admin = check_admin_role(current_user)
    
    try:
        user = db.query(User).filter(User.id == user_id).first()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Update fields
        if user_data.email:
            user.email = user_data.email
        if user_data.first_name:
            user.first_name = user_data.first_name
        if user_data.last_name:
            user.last_name = user_data.last_name
        if user_data.is_active is not None:
            user.is_active = user_data.is_active
        
        # Update roles
        if user_data.roles:
            roles = db.query(Role).filter(Role.name.in_(user_data.roles)).all()
            user.roles = roles
        
        db.commit()
        
        # Audit log
        audit_log = AuditLog(
            user_id=admin.id,
            action="user_updated",
            resource="users",
            resource_id=user_id,
            status="success",
            ip_address=request.client.host if request.client else None,
            details=f"Admin {admin.username} updated user {user.username}"
        )
        db.add(audit_log)
        db.commit()
        
        logger.info(f"Admin {admin.id} updated user {user_id}")
        
        return {
            "success": True,
            "message": "User updated"
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating user: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update user"
        )


@router.post("/users/{user_id}/unlock")
def unlock_user(
    user_id: int,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Unlock user account (admin only)"""
    
    admin = check_admin_role(current_user)
    
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    user.is_locked = False
    user.locked_until = None
    user.failed_login_attempts = 0
    db.commit()
    
    # Audit log
    audit_log = AuditLog(
        user_id=admin.id,
        action="user_unlocked",
        resource="users",
        resource_id=user_id,
        status="success",
        ip_address=request.client.host if request.client else None,
        details=f"Admin {admin.username} unlocked user {user.username}"
    )
    db.add(audit_log)
    db.commit()
    
    logger.info(f"Admin {admin.id} unlocked user {user_id}")
    
    return {
        "success": True,
        "message": "User account unlocked"
    }


@router.delete("/users/{user_id}")
def delete_user(
    user_id: int,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete user (admin only)"""
    
    admin = check_admin_role(current_user)
    
    if user_id == admin.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete your own account"
        )
    
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Audit log (before deletion)
    audit_log = AuditLog(
        user_id=admin.id,
        action="user_deleted",
        resource="users",
        resource_id=user_id,
        status="success",
        ip_address=request.client.host if request.client else None,
        details=f"Admin {admin.username} deleted user {user.username}"
    )
    db.add(audit_log)
    
    db.delete(user)
    db.commit()
    
    logger.info(f"Admin {admin.id} deleted user {user_id}")
    
    return {
        "success": True,
        "message": "User deleted"
    }


# ==================== MFA Management ====================

@router.get("/users/{user_id}/mfa-status", response_model=dict)
def get_user_mfa_status(
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get MFA status for a specific user (admin only)."""
    admin = check_admin_role(current_user)

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    is_target_admin = any(role.name.lower() == "admin" for role in user.roles)

    return {
        "user_id": user.id,
        "username": user.username,
        "roles": [role.name for role in user.roles],
        "is_admin": is_target_admin,
        "mfa_verified": MFAService.has_verified_mfa(user),
        "mfa_methods": [
            {
                "id": method.id,
                "type": method.method_type.value,
                "is_enabled": method.is_enabled,
                "is_primary": method.is_primary,
                "last_used": method.last_used.isoformat() if method.last_used else None,
            }
            for method in user.mfa_methods
        ],
        "trusted_devices": sum(1 for device in user.devices if device.is_trusted)
    }


@router.patch("/users/{user_id}/mfa-status", response_model=dict)
def update_user_mfa_status(
    user_id: int,
    request_data: UserMFAStatusUpdateRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Enable/disable MFA methods for a specific non-admin user (admin only)."""
    admin = check_admin_role(current_user)

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    if any(role.name.lower() == "admin" for role in user.roles):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Admin user MFA cannot be modified via this endpoint"
        )

    methods_query = db.query(MFAMethod).filter(MFAMethod.user_id == user_id)
    if request_data.method_ids:
        methods_query = methods_query.filter(MFAMethod.id.in_(request_data.method_ids))
    methods = methods_query.all()

    if request_data.method_ids and not methods:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No MFA methods found for the provided method IDs"
        )

    for method in methods:
        method.is_enabled = request_data.is_enabled
        if not request_data.is_enabled:
            method.is_primary = False

    # If enabling methods, ensure one primary method exists.
    if request_data.is_enabled and methods:
        has_primary = any(m.is_primary for m in user.mfa_methods if m.is_enabled)
        if not has_primary:
            methods[0].is_primary = True

    reset_devices_count = 0
    if request_data.reset_trusted_devices:
        for device in user.devices:
            if device.is_trusted:
                device.is_trusted = False
                device.trust_score = 0.0
                reset_devices_count += 1

    db.commit()

    audit_log = AuditLog(
        user_id=admin.id,
        action="user_mfa_status_updated",
        resource="mfa",
        resource_id=user_id,
        status="success",
        ip_address=request.client.host if request.client else None,
        details=(
            f"Admin {admin.username} set MFA is_enabled={request_data.is_enabled} "
            f"for user {user.username}; methods_updated={len(methods)}; "
            f"trusted_devices_reset={reset_devices_count}"
        )
    )
    db.add(audit_log)
    db.commit()

    db.refresh(user)
    return {
        "success": True,
        "message": "User MFA status updated",
        "user_id": user.id,
        "mfa_verified": MFAService.has_verified_mfa(user),
        "methods_updated": len(methods),
        "trusted_devices_reset": reset_devices_count
    }


@router.post("/mfa/reset-non-admin", response_model=dict)
def reset_non_admin_mfa_status(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Disable MFA for all non-admin users, forcing re-verification (admin only)."""
    admin = check_admin_role(current_user)

    users = db.query(User).all()
    affected_users = 0
    affected_methods = 0
    affected_devices = 0

    for user in users:
        if any(role.name.lower() == "admin" for role in user.roles):
            continue

        user_method_count = 0
        for method in user.mfa_methods:
            if method.is_enabled or method.is_primary:
                method.is_enabled = False
                method.is_primary = False
                user_method_count += 1

        for device in user.devices:
            if device.is_trusted:
                device.is_trusted = False
                device.trust_score = 0.0
                affected_devices += 1

        if user_method_count > 0:
            affected_users += 1
            affected_methods += user_method_count

    db.commit()

    audit_log = AuditLog(
        user_id=admin.id,
        action="bulk_mfa_reset_non_admin",
        resource="mfa",
        status="success",
        ip_address=request.client.host if request.client else None,
        details=(
            f"Admin {admin.username} reset MFA for non-admin users; "
            f"users_affected={affected_users}; methods_disabled={affected_methods}; "
            f"trusted_devices_reset={affected_devices}"
        )
    )
    db.add(audit_log)
    db.commit()

    return {
        "success": True,
        "message": "MFA reset completed for all non-admin users",
        "users_affected": affected_users,
        "methods_disabled": affected_methods,
        "trusted_devices_reset": affected_devices
    }


# ==================== Audit Log Analysis ====================

@router.get("/logs", response_model=list)
def get_audit_logs(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    action: Optional[str] = None,
    resource: Optional[str] = None,
    status: Optional[str] = None,
    user_id: Optional[int] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
):
    """Get audit logs with filtering (admin only)"""
    
    admin = check_admin_role(current_user)
    
    try:
        query = db.query(AuditLog)
        
        # Apply filters
        if action:
            query = query.filter(AuditLog.action == action)
        if resource:
            query = query.filter(AuditLog.resource == resource)
        if status:
            query = query.filter(AuditLog.status == status)
        if user_id:
            query = query.filter(AuditLog.user_id == user_id)
        
        # Date range filter
        if start_date:
            try:
                start_dt = datetime.fromisoformat(start_date)
                query = query.filter(AuditLog.timestamp >= start_dt)
            except ValueError:
                pass
        
        if end_date:
            try:
                end_dt = datetime.fromisoformat(end_date)
                query = query.filter(AuditLog.timestamp <= end_dt)
            except ValueError:
                pass
        
        total = query.count()
        logs = query.order_by(desc(AuditLog.timestamp)).offset(skip).limit(limit).all()
        
        result = []
        for log in logs:
            user = db.query(User).filter(User.id == log.user_id).first() if log.user_id else None
            result.append({
                "id": log.id,
                "user_id": log.user_id,
                "username": user.username if user else "System",
                "action": log.action,
                "resource": log.resource,
                "status": log.status,
                "ip_address": log.ip_address,
                "details": log.details,
                "timestamp": log.timestamp.isoformat() if log.timestamp else None,
                "total": total
            })
        
        return result
    except Exception as e:
        logger.error(f"Error getting audit logs: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve audit logs"
        )


@router.get("/logs/stats")
def get_audit_log_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    days: int = Query(7, ge=1, le=90)
):
    """Get audit log statistics (admin only)"""
    
    admin = check_admin_role(current_user)
    
    try:
        start_date = datetime.utcnow() - timedelta(days=days)
        
        # Total logs
        total_logs = db.query(AuditLog).filter(
            AuditLog.timestamp >= start_date
        ).count()
        
        # Success/Failure breakdown
        from sqlalchemy import func
        
        stats_query = db.query(
            AuditLog.status,
            func.count(AuditLog.id).label("count")
        ).filter(
            AuditLog.timestamp >= start_date
        ).group_by(AuditLog.status).all()
        
        status_breakdown = {item[0]: item[1] for item in stats_query}
        
        # Action breakdown
        action_query = db.query(
            AuditLog.action,
            func.count(AuditLog.id).label("count")
        ).filter(
            AuditLog.timestamp >= start_date
        ).group_by(AuditLog.action).all()
        
        action_breakdown = {item[0]: item[1] for item in action_query}
        
        # Most active users
        user_query = db.query(
            AuditLog.user_id,
            func.count(AuditLog.id).label("count")
        ).filter(
            AuditLog.timestamp >= start_date
        ).group_by(AuditLog.user_id).order_by(
            func.count(AuditLog.id).desc()
        ).limit(10).all()
        
        most_active = []
        for user_id, count in user_query:
            user = db.query(User).filter(User.id == user_id).first() if user_id else None
            most_active.append({
                "user_id": user_id,
                "username": user.username if user else "System",
                "action_count": count
            })
        
        return {
            "period_days": days,
            "total_logs": total_logs,
            "status_breakdown": status_breakdown,
            "action_breakdown": action_breakdown,
            "most_active_users": most_active
        }
    except Exception as e:
        logger.error(f"Error getting audit stats: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve audit statistics"
        )


# ==================== Policy Management ====================

@router.get("/policies")
def get_policies(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get access control policies (admin only)"""
    
    admin = check_admin_role(current_user)
    
    try:
        roles = db.query(Role).all()
        
        result = []
        for role in roles:
            result.append({
                "id": role.id,
                "name": role.name,
                "description": role.description,
                "permissions_count": len(role.permissions),
                "permissions": [
                    {
                        "id": perm.id,
                        "name": perm.name,
                        "resource": perm.resource,
                        "action": perm.action
                    }
                    for perm in role.permissions
                ]
            })
        
        return result
    except Exception as e:
        logger.error(f"Error getting policies: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve policies"
        )


@router.post("/policies/role/{role_id}/permissions")
def add_permission_to_role(
    role_id: int,
    permission_id: int,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Add permission to role (admin only)"""
    
    admin = check_admin_role(current_user)
    
    try:
        role = db.query(Role).filter(Role.id == role_id).first()
        permission = db.query(Permission).filter(Permission.id == permission_id).first()
        
        if not role or not permission:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Role or permission not found"
            )
        
        if permission not in role.permissions:
            role.permissions.append(permission)
            db.commit()
        
        # Audit log
        audit_log = AuditLog(
            user_id=admin.id,
            action="permission_added",
            resource="roles",
            resource_id=role_id,
            status="success",
            ip_address=request.client.host if request.client else None,
            details=f"Added permission {permission.name} to role {role.name}"
        )
        db.add(audit_log)
        db.commit()
        
        logger.info(f"Admin {admin.id} added permission {permission_id} to role {role_id}")
        
        return {
            "success": True,
            "message": "Permission added to role"
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error adding permission: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to add permission"
        )
