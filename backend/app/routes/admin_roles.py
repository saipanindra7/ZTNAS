"""
ZTNAS Admin Roles & Privileges Management
ORM-based endpoints for admins to manage roles, permissions, and assignments.
"""

from datetime import datetime, timedelta
from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.models import AuditLog, Permission, Role, User
from config.database import get_db

import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/admin", tags=["Admin"])


class PermissionSchema(BaseModel):
    id: int
    name: str
    description: str | None = None
    resource: str


class RoleSchema(BaseModel):
    id: int
    name: str
    description: str | None = None
    is_active: bool
    user_count: int
    permissions: List[PermissionSchema]


class RoleCreateUpdate(BaseModel):
    name: str
    description: str
    is_active: bool = True


class PermissionAssignment(BaseModel):
    role_id: int
    permission_ids: List[int]


def _log_audit(
    db: Session,
    user_id: int,
    action: str,
    resource: str,
    status_value: str,
    resource_id: int | None = None,
    details: str | None = None,
) -> None:
    log = AuditLog(
        user_id=user_id,
        action=action,
        resource=resource,
        resource_id=resource_id,
        status=status_value,
        details=details,
    )
    db.add(log)
    db.commit()


def get_current_user(request: Request, db: Session = Depends(get_db)) -> User:
    """Get current authenticated user from bearer token."""
    from utils.security import verify_access_token

    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid authorization header",
        )

    token = auth_header[7:]
    payload = verify_access_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )

    user_id = payload.get("sub")
    user = db.query(User).filter(User.id == int(user_id)).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )

    return user


def check_admin_role(current_user: User = Depends(get_current_user)) -> User:
    """Ensure user has admin role."""
    roles = [role.name.lower() for role in current_user.roles]
    if "admin" not in roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can access this endpoint",
        )
    return current_user


@router.get("/roles", response_model=List[RoleSchema])
async def list_roles(
    current_user: User = Depends(check_admin_role),
    db: Session = Depends(get_db),
):
    """List all system roles with user counts and permissions."""
    try:
        roles = db.query(Role).order_by(Role.name.asc()).all()
        return [
            {
                "id": role.id,
                "name": role.name,
                "description": role.description,
                "is_active": True,
                "user_count": len(role.users),
                "permissions": [
                    {
                        "id": perm.id,
                        "name": perm.name,
                        "description": perm.description,
                        "resource": perm.resource,
                    }
                    for perm in role.permissions
                ],
            }
            for role in roles
        ]
    except Exception as exc:
        logger.error(f"Error listing roles: {exc}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list roles",
        )


@router.post("/roles", status_code=201)
async def create_role(
    role_data: RoleCreateUpdate,
    current_user: User = Depends(check_admin_role),
    db: Session = Depends(get_db),
):
    """Create a new role."""
    existing = db.query(Role).filter(Role.name == role_data.name).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Role '{role_data.name}' already exists",
        )

    role = Role(name=role_data.name, description=role_data.description)
    db.add(role)
    db.commit()
    db.refresh(role)

    _log_audit(
        db,
        current_user.id,
        "create_role",
        "roles",
        "success",
        role.id,
        f"Created role {role_data.name}",
    )

    return {
        "success": True,
        "message": f"Role '{role_data.name}' created successfully",
        "role_id": role.id,
    }


@router.put("/roles/{role_id}", status_code=200)
async def update_role(
    role_id: int,
    role_data: RoleCreateUpdate,
    current_user: User = Depends(check_admin_role),
    db: Session = Depends(get_db),
):
    """Update an existing role."""
    role = db.query(Role).filter(Role.id == role_id).first()
    if not role:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role not found")

    role.name = role_data.name
    role.description = role_data.description
    db.commit()

    _log_audit(
        db,
        current_user.id,
        "update_role",
        "roles",
        "success",
        role_id,
        f"Updated role {role_data.name}",
    )

    return {"success": True, "message": f"Role {role_id} updated successfully"}


@router.delete("/roles/{role_id}", status_code=200)
async def delete_role(
    role_id: int,
    current_user: User = Depends(check_admin_role),
    db: Session = Depends(get_db),
):
    """Delete a role if no users are assigned to it."""
    role = db.query(Role).filter(Role.id == role_id).first()
    if not role:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role not found")

    if len(role.users) > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot delete role with {len(role.users)} assigned users. Remove users first.",
        )

    db.delete(role)
    db.commit()

    _log_audit(
        db,
        current_user.id,
        "delete_role",
        "roles",
        "success",
        role_id,
        "Deleted role",
    )

    return {"success": True, "message": f"Role {role_id} deleted successfully"}


@router.get("/permissions")
async def list_all_permissions(
    current_user: User = Depends(check_admin_role),
    db: Session = Depends(get_db),
):
    """List all available permissions in the system."""
    try:
        perms = db.query(Permission).order_by(Permission.resource.asc(), Permission.name.asc()).all()
        return [
            {
                "id": perm.id,
                "name": perm.name,
                "description": perm.description,
                "resource": perm.resource,
            }
            for perm in perms
        ]
    except Exception as exc:
        logger.error(f"Error listing permissions: {exc}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list permissions",
        )


@router.post("/permissions")
async def create_permission(
    permission: Dict[str, Any],
    current_user: User = Depends(check_admin_role),
    db: Session = Depends(get_db),
):
    """Create a new permission."""
    name = (permission.get("name") or "").strip()
    description = (permission.get("description") or "").strip()
    resource = (permission.get("resource") or "").strip()

    if not name or not resource:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Permission name and resource are required",
        )

    existing = db.query(Permission).filter(Permission.name == name).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Permission '{name}' already exists",
        )

    perm = Permission(name=name, description=description, resource=resource, action="manage")
    db.add(perm)
    db.commit()
    db.refresh(perm)

    _log_audit(
        db,
        current_user.id,
        "create_permission",
        "permissions",
        "success",
        perm.id,
        f"Created permission {name}",
    )

    return {
        "success": True,
        "message": f"Permission '{name}' created successfully",
        "permission_id": perm.id,
    }


@router.post("/roles/{role_id}/permissions", status_code=200)
async def assign_permissions_to_role(
    role_id: int,
    permission_data: PermissionAssignment,
    current_user: User = Depends(check_admin_role),
    db: Session = Depends(get_db),
):
    """Assign permissions to a role."""
    role = db.query(Role).filter(Role.id == role_id).first()
    if not role:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role not found")

    permissions = []
    if permission_data.permission_ids:
        permissions = (
            db.query(Permission)
            .filter(Permission.id.in_(permission_data.permission_ids))
            .all()
        )

    role.permissions = permissions
    db.commit()

    _log_audit(
        db,
        current_user.id,
        "assign_permissions",
        "roles",
        "success",
        role_id,
        f"Assigned {len(permissions)} permissions",
    )

    return {
        "success": True,
        "message": f"Assigned {len(permissions)} permissions to role {role_id}",
    }


@router.post("/users/{user_id}/roles", status_code=200)
async def assign_roles_to_user(
    user_id: int,
    roles_data: Dict[str, Any],
    current_user: User = Depends(check_admin_role),
    db: Session = Depends(get_db),
):
    """Assign roles to a user."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    role_ids = roles_data.get("role_ids", [])
    roles = []
    if role_ids:
        roles = db.query(Role).filter(Role.id.in_(role_ids)).all()

    user.roles = roles
    db.commit()

    _log_audit(
        db,
        current_user.id,
        "assign_roles",
        "users",
        "success",
        user_id,
        f"Assigned {len(roles)} roles",
    )

    return {"success": True, "message": f"Assigned {len(roles)} roles to user {user_id}"}


@router.get("/users/{user_id}/roles")
async def get_user_roles(
    user_id: int,
    current_user: User = Depends(check_admin_role),
    db: Session = Depends(get_db),
):
    """Get all roles assigned to a user."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    return [{"id": role.id, "name": role.name} for role in user.roles]


@router.get("/privilege-changes")
async def get_privilege_changes(
    current_user: User = Depends(check_admin_role),
    db: Session = Depends(get_db),
    days: int = 30,
):
    """Get privilege-related audit log entries."""
    try:
        start_time = datetime.utcnow() - timedelta(days=days)
        target_actions = [
            "assign_roles",
            "assign_permissions",
            "create_role",
            "update_role",
            "delete_role",
            "create_permission",
        ]

        logs = (
            db.query(AuditLog)
            .filter(AuditLog.action.in_(target_actions), AuditLog.timestamp >= start_time)
            .order_by(AuditLog.timestamp.desc())
            .all()
        )

        result = []
        for log in logs:
            admin_name = "system"
            if log.user_id:
                user = db.query(User).filter(User.id == log.user_id).first()
                if user:
                    admin_name = user.username

            result.append(
                {
                    "timestamp": log.timestamp.isoformat() if log.timestamp else "",
                    "admin": admin_name,
                    "action": log.action,
                    "resource_type": log.resource or "",
                    "resource_id": log.resource_id,
                    "status": (log.status or "success").upper(),
                }
            )

        return result
    except Exception as exc:
        logger.error(f"Error getting privilege changes: {exc}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get privilege changes",
        )
