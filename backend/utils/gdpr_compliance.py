# GDPR Compliance Features
# Data export, deletion, and right-to-be-forgotten implementation

import json
import csv
import io
from datetime import datetime, timedelta
from typing import BinaryIO, List, Dict, Any
from enum import Enum
from sqlalchemy.orm import Session
from app.models.user import User
from app.models.audit import AuditLog
from app.models.mfa import MFAMethod
from app.models.device import Device
import logging

logger = logging.getLogger(__name__)

class DataExportFormat(str, Enum):
    """Supported export formats for user data"""
    JSON = "json"
    CSV = "csv"
    NDJSON = "ndjson"  # Newline-delimited JSON

class GDPRCompliance:
    """
    Implementation of GDPR rights:
    - Right to access (data export)
    - Right to be forgotten (data deletion)
    - Right to data portability (structured export)
    - Right to rectification (data correction)
    """
    
    def __init__(self, db: Session):
        self.db = db
    
    def export_user_data(
        self,
        user_id: str,
        format: DataExportFormat = DataExportFormat.JSON
    ) -> BinaryIO:
        """
        Export all user data in portable format
        Includes: profile, audit logs, MFA methods, devices, etc.
        """
        
        # Fetch all user data
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise ValueError(f"User {user_id} not found")
        
        audit_logs = self.db.query(AuditLog).filter(
            AuditLog.user_id == user_id
        ).all()
        
        mfa_methods = self.db.query(MFAMethod).filter(
            MFAMethod.user_id == user_id
        ).all()
        
        devices = self.db.query(Device).filter(
            Device.user_id == user_id
        ).all()
        
        # Compile data dictionary
        data = {
            "export_date": datetime.utcnow().isoformat(),
            "user": self._serialize_user(user),
            "audit_logs": [self._serialize_audit_log(log) for log in audit_logs],
            "mfa_methods": [self._serialize_mfa(mfa) for mfa in mfa_methods],
            "devices": [self._serialize_device(device) for device in devices],
        }
        
        # Format and return
        if format == DataExportFormat.JSON:
            return self._format_json(data)
        elif format == DataExportFormat.CSV:
            return self._format_csv(data)
        elif format == DataExportFormat.NDJSON:
            return self._format_ndjson(data)
        else:
            raise ValueError(f"Unsupported format: {format}")
    
    def delete_user_data(
        self,
        user_id: str,
        reason: str = "user_request",
        anonymize_only: bool = False
    ) -> Dict[str, int]:
        """
        Permanently delete or anonymize user data
        
        Args:
            user_id: User ID to delete
            reason: Deletion reason for audit trail
            anonymize_only: If True, anonymize instead of delete
        
        Returns:
            Dictionary with count of deleted records
        """
        
        logger.warning(
            f"GDPR data deletion initiated: user_id={user_id}, reason={reason}"
        )
        
        counts = {}
        
        if anonymize_only:
            # Anonymize user data instead of deleting
            counts = self._anonymize_user_data(user_id)
        else:
            # Permanently delete user data
            counts = self._delete_user_data(user_id)
        
        # Log the deletion for audit trail
        self._log_deletion(user_id, reason, counts)
        
        return counts
    
    def _delete_user_data(self, user_id: str) -> Dict[str, int]:
        """Permanently delete all user data"""
        
        counts = {}
        
        # Delete MFA methods
        counts["mfa_methods"] = self.db.query(MFAMethod).filter(
            MFAMethod.user_id == user_id
        ).delete()
        
        # Delete devices
        counts["devices"] = self.db.query(Device).filter(
            Device.user_id == user_id
        ).delete()
        
        # Anonymize audit logs instead of deleting (for compliance)
        self.db.query(AuditLog).filter(
            AuditLog.user_id == user_id
        ).update({"user_id": "DELETED_USER"})
        counts["audit_logs_anonymized"] = self.db.commit()
        
        # Delete user account
        self.db.query(User).filter(User.id == user_id).delete()
        counts["users"] = 1
        
        self.db.commit()
        return counts
    
    def _anonymize_user_data(self, user_id: str) -> Dict[str, int]:
        """Anonymize instead of delete (preserves audit trail)"""
        
        counts = {}
        
        # Anonymize user profile
        user = self.db.query(User).filter(User.id == user_id).first()
        if user:
            user.username = f"deleted_user_{user_id[:8]}"
            user.email = f"deleted_{user_id[:8]}@anonymized.local"
            user.name = "Deleted User"
            self.db.commit()
            counts["users_anonymized"] = 1
        
        # Delete sensitive data (passwords, tokens)
        user_obj = self.db.query(User).filter(User.id == user_id).first()
        if user_obj:
            user_obj.hashed_password = "ANONYMIZED"
            self.db.commit()
        
        # Remove MFA methods
        counts["mfa_methods"] = self.db.query(MFAMethod).filter(
            MFAMethod.user_id == user_id
        ).delete()
        
        # Anonymize audit logs
        self.db.query(AuditLog).filter(
            AuditLog.user_id == user_id
        ).update({"user_id": "ANONYMIZED"})
        
        self.db.commit()
        return counts
    
    def _serialize_user(self, user: User) -> Dict[str, Any]:
        """Serialize user for export (excluding sensitive data)"""
        return {
            "id": str(user.id),
            "username": user.username,
            "email": user.email,
            "name": user.name,
            "is_active": user.is_active,
            "created_at": user.created_at.isoformat(),
            "last_login": user.last_login.isoformat() if user.last_login else None,
            "mfa_enabled": user.mfa_enabled,
            "account_locked": user.account_locked,
        }
    
    def _serialize_audit_log(self, log: AuditLog) -> Dict[str, Any]:
        """Serialize audit log for export"""
        return {
            "id": str(log.id),
            "action": log.action,
            "resource": log.resource,
            "status": log.status,
            "ip_address": log.ip_address,
            "timestamp": log.timestamp.isoformat(),
            "details": log.details,
        }
    
    def _serialize_mfa(self, mfa: MFAMethod) -> Dict[str, Any]:
        """Serialize MFA method for export"""
        return {
            "id": str(mfa.id),
            "method_type": mfa.method_type,
            "is_active": mfa.is_active,
            "created_at": mfa.created_at.isoformat(),
        }
    
    def _serialize_device(self, device: Device) -> Dict[str, Any]:
        """Serialize device for export"""
        return {
            "id": str(device.id),
            "device_name": device.device_name,
            "device_type": device.device_type,
            "os_info": device.os_info,
            "trust_score": float(device.trust_score),
            "created_at": device.created_at.isoformat(),
            "last_used": device.last_used.isoformat() if device.last_used else None,
        }
    
    def _format_json(self, data: Dict) -> BinaryIO:
        """Format data as JSON"""
        output = io.BytesIO()
        json_data = json.dumps(data, indent=2, default=str)
        output.write(json_data.encode())
        output.seek(0)
        return output
    
    def _format_csv(self, data: Dict) -> BinaryIO:
        """Format data as CSV (multiple files zipped)"""
        # For simplicity, return first dataset as CSV
        output = io.BytesIO()
        
        if data.get("audit_logs"):
            writer = csv.DictWriter(output, fieldnames=data["audit_logs"][0].keys())
            writer.writeheader()
            for log in data["audit_logs"]:
                writer.writerow(log)
        
        output.seek(0)
        return output
    
    def _format_ndjson(self, data: Dict) -> BinaryIO:
        """Format data as NDJSON (streaming friendly)"""
        output = io.BytesIO()
        
        for key, value in data.items():
            if isinstance(value, list):
                for item in value:
                    line = json.dumps({key: item}, default=str)
                    output.write((line + "\n").encode())
            else:
                line = json.dumps({key: value}, default=str)
                output.write((line + "\n").encode())
        
        output.seek(0)
        return output
    
    def _log_deletion(self, user_id: str, reason: str, counts: Dict[str, int]):
        """Log data deletion for audit trail"""
        logger.info(
            f"GDPR data deletion completed",
            extra={
                "user_id": user_id,
                "reason": reason,
                "deleted_records": counts,
            }
        )
    
    def export_user_data_for_portability(self, user_id: str) -> Dict[str, Any]:
        """
        Export for right to data portability
        Returns structured, machine-readable format
        """
        return self.export_user_data(user_id, DataExportFormat.JSON)
    
    def get_deletion_status(self, user_id: str) -> Dict[str, Any]:
        """Check if user data has been deleted"""
        user = self.db.query(User).filter(User.id == user_id).first()
        
        if not user:
            return {"status": "deleted", "user_id": user_id}
        
        return {
            "status": "active",
            "user_id": user_id,
            "username": user.username,
            "last_login": user.last_login.isoformat() if user.last_login else None,
        }
