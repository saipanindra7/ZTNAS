import sys
import os

# Add backend directory to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.database import SessionLocal, engine, Base
from app.models import Role, Permission
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def seed_data():
    """Seed the database with default roles and permissions"""
    db = SessionLocal()
    
    try:
        # Define default permissions
        default_permissions = [
            # User permissions
            {"name": "user.create", "description": "Create users", "resource": "users", "action": "create"},
            {"name": "user.read", "description": "Read users", "resource": "users", "action": "read"},
            {"name": "user.update", "description": "Update users", "resource": "users", "action": "update"},
            {"name": "user.delete", "description": "Delete users", "resource": "users", "action": "delete"},
            
            # Role permissions
            {"name": "role.create", "description": "Create roles", "resource": "roles", "action": "create"},
            {"name": "role.read", "description": "Read roles", "resource": "roles", "action": "read"},
            {"name": "role.update", "description": "Update roles", "resource": "roles", "action": "update"},
            {"name": "role.delete", "description": "Delete roles", "resource": "roles", "action": "delete"},
            
            # Permission permissions
            {"name": "permission.create", "description": "Create permissions", "resource": "permissions", "action": "create"},
            {"name": "permission.read", "description": "Read permissions", "resource": "permissions", "action": "read"},
            
            # MFA permissions
            {"name": "mfa.setup", "description": "Setup MFA", "resource": "mfa", "action": "setup"},
            {"name": "mfa.manage", "description": "Manage MFA methods", "resource": "mfa", "action": "manage"},
            
            # Audit permissions
            {"name": "audit.read", "description": "Read audit logs", "resource": "audit_logs", "action": "read"},
            {"name": "audit.export", "description": "Export audit logs", "resource": "audit_logs", "action": "export"},
            
            # Device permissions
            {"name": "device.manage", "description": "Manage devices", "resource": "devices", "action": "manage"},
            
            # Access control
            {"name": "access.all", "description": "Full access", "resource": "all", "action": "all"},
        ]
        
        # Create or update permissions
        for perm_data in default_permissions:
            existing = db.query(Permission).filter(
                Permission.name == perm_data["name"]
            ).first()
            
            if not existing:
                permission = Permission(
                    name=perm_data["name"],
                    description=perm_data["description"],
                    resource=perm_data["resource"],
                    action=perm_data["action"]
                )
                db.add(permission)
                logger.info(f"Created permission: {perm_data['name']}")
            else:
                logger.info(f"Permission already exists: {perm_data['name']}")
        
        db.commit()
        
        # Define default roles
        default_roles = [
            {
                "name": "Admin",
                "description": "Administrator with full access",
                "permissions": ["access.all"]
            },
            {
                "name": "Manager",
                "description": "Manager role for organizational oversight",
                "permissions": ["user.read", "user.create", "user.update", "mfa.setup", "audit.read", "device.manage"]
            },
            {
                "name": "User",
                "description": "Regular user with limited permissions",
                "permissions": ["user.read", "mfa.setup", "mfa.manage", "device.manage"]
            },
            {
                "name": "Guest",
                "description": "Guest role with minimal permissions",
                "permissions": ["user.read"]
            },
        ]
        
        # Create or update roles
        for role_data in default_roles:
            existing_role = db.query(Role).filter(
                Role.name == role_data["name"]
            ).first()
            
            if not existing_role:
                role = Role(
                    name=role_data["name"],
                    description=role_data["description"]
                )
                
                # Assign permissions
                for perm_name in role_data["permissions"]:
                    permission = db.query(Permission).filter(
                        Permission.name == perm_name
                    ).first()
                    if permission:
                        role.permissions.append(permission)
                
                db.add(role)
                logger.info(f"Created role: {role_data['name']}")
            else:
                logger.info(f"Role already exists: {role_data['name']}")
        
        db.commit()
        logger.info("Database seeded successfully!")
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error seeding database: {str(e)}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    seed_data()
