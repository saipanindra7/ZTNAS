import os
import base64
import qrcode
import json
import uuid
import hashlib
from io import BytesIO
from datetime import datetime, timedelta
from typing import Optional
from PIL import Image
import pyotp
from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import flag_modified
from app.models import MFAMethod, User, AuditLog, MFAMethodType
from config.settings import settings
import logging

logger = logging.getLogger(__name__)

class MFAService:
    """Service for handling MFA operations"""
    
    # ==================== TOTP (Google Authenticator) ====================
    
    @staticmethod
    def setup_totp(user_id: int, db: Session) -> dict:
        """
        Setup TOTP (Time-based One-Time Password)
        Returns: {"secret": str, "qr_code_url": str}
        """
        try:
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                return {"success": False, "message": "User not found"}
            
            # Generate TOTP secret
            secret = pyotp.random_base32()
            
            # Create provisioning URI for QR code
            totp = pyotp.TOTP(secret)
            provisioning_uri = totp.provisioning_uri(
                name=user.email,
                issuer_name="ZTNAS"
            )
            
            # Generate QR code
            qr = qrcode.QRCode(version=1, box_size=10, border=5)
            qr.add_data(provisioning_uri)
            qr.make(fit=True)
            
            img = qr.make_image(fill_color="black", back_color="white")
            buffer = BytesIO()
            img.save(buffer, format="PNG")
            img_str = base64.b64encode(buffer.getvalue()).decode()
            qr_code_url = f"data:image/png;base64,{img_str}"
            
            return {
                "success": True,
                "secret": secret,
                "qr_code_url": qr_code_url,
                "manual_entry_key": secret
            }
        except Exception as e:
            logger.error(f"Error setting up TOTP: {str(e)}")
            return {"success": False, "message": str(e)}
    
    @staticmethod
    def verify_totp(secret: str, totp_code: str) -> bool:
        """Verify TOTP code"""
        try:
            totp = pyotp.TOTP(secret)
            # Allow 1 time step backward for clock skew
            return totp.verify(totp_code, valid_window=1)
        except Exception as e:
            logger.error(f"Error verifying TOTP: {str(e)}")
            return False
    
    @staticmethod
    def enroll_totp(user_id: int, secret: str, totp_code: str, db: Session) -> tuple[bool, str, dict]:
        """
        Enroll user in TOTP
        Returns: (success, message, mfa_method)
        """
        try:
            # Verify the code before enrolling
            if not MFAService.verify_totp(secret, totp_code):
                return False, "Invalid TOTP code", {}
            
            # Create MFA method
            mfa_method = MFAMethod(
                user_id=user_id,
                method_type=MFAMethodType.TOTP,
                is_enabled=True,
                config={"secret": secret},
                is_primary=False
            )
            
            db.add(mfa_method)
            db.commit()
            db.refresh(mfa_method)
            
            logger.info(f"TOTP MFA enrolled for user {user_id}")
            return True, "TOTP MFA enrolled", {"id": mfa_method.id}
        except Exception as e:
            db.rollback()
            logger.error(f"Error enrolling TOTP: {str(e)}")
            return False, str(e), {}
    
    # ==================== SMS/Email OTP ====================
    
    @staticmethod
    def generate_otp() -> str:
        """Generate a 6-digit OTP"""
        import random
        return str(random.randint(100000, 999999))
    
    @staticmethod
    def setup_sms_otp(user_id: int, phone_number: str, db: Session) -> tuple[bool, str, dict]:
        """Setup SMS OTP"""
        try:
            # Check if SMS OTP already exists
            existing = db.query(MFAMethod).filter(
                MFAMethod.user_id == user_id,
                MFAMethod.method_type == MFAMethodType.SMS_OTP
            ).first()
            
            if existing:
                return False, "SMS OTP already setup", {}
            
            otp_code = MFAService.generate_otp()
            otp_expires = datetime.utcnow() + timedelta(minutes=5)
            
            # In production, send OTP via Twilio
            logger.info(f"SMS OTP for verification (DEV): {otp_code}")
            
            # Store temporarily in config
            mfa_method = MFAMethod(
                user_id=user_id,
                method_type=MFAMethodType.SMS_OTP,
                is_enabled=False,  # Wait for verification
                config={
                    "phone_number": phone_number,
                    "pending_otp": otp_code,
                    "otp_expires": otp_expires.isoformat(),
                    "verification_attempts": 0
                }
            )
            
            db.add(mfa_method)
            db.commit()
            db.refresh(mfa_method)
            
            logger.info(f"SMS OTP setup initiated for user {user_id}")
            return True, "OTP sent to phone", {"method_id": mfa_method.id}
        except Exception as e:
            db.rollback()
            logger.error(f"Error setting up SMS OTP: {str(e)}")
            return False, str(e), {}
    
    @staticmethod
    def setup_email_otp(user_id: int, email: Optional[str], db: Session) -> tuple[bool, str, dict]:
        """Setup Email OTP"""
        try:
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                return False, "User not found", {}
            
            target_email = email if email else user.email
            
            otp_code = MFAService.generate_otp()
            otp_expires = datetime.utcnow() + timedelta(minutes=10)
            
            # In production, send OTP via email
            logger.info(f"Email OTP for verification (DEV): {otp_code} to {target_email}")
            
            mfa_method = MFAMethod(
                user_id=user_id,
                method_type=MFAMethodType.EMAIL_OTP,
                is_enabled=False,
                config={
                    "email": target_email,
                    "pending_otp": otp_code,
                    "otp_expires": otp_expires.isoformat(),
                    "verification_attempts": 0
                }
            )
            
            db.add(mfa_method)
            db.commit()
            db.refresh(mfa_method)
            
            return True, "OTP sent to email", {"method_id": mfa_method.id}
        except Exception as e:
            db.rollback()
            logger.error(f"Error setting up Email OTP: {str(e)}")
            return False, str(e), {}
    
    @staticmethod
    def verify_otp(method_id: int, otp_code: str, db: Session) -> tuple[bool, str]:
        """Verify OTP code"""
        try:
            mfa_method = db.query(MFAMethod).filter(MFAMethod.id == method_id).first()
            if not mfa_method:
                return False, "MFA method not found"
            
            config = mfa_method.config
            pending_otp = config.get("pending_otp")
            otp_expires = datetime.fromisoformat(config.get("otp_expires"))
            
            # Check expiry
            if datetime.utcnow() > otp_expires:
                return False, "OTP expired"
            
            # Check code
            if pending_otp != otp_code:
                config["verification_attempts"] = config.get("verification_attempts", 0) + 1
                if config["verification_attempts"] >= 3:
                    db.delete(mfa_method)
                db.commit()
                return False, "Invalid OTP"
            
            # Valid!
            mfa_method.is_enabled = True
            mfa_method.config = {k: v for k, v in config.items() if k not in ["pending_otp", "otp_expires"]}
            db.commit()
            
            logger.info(f"OTP MFA verified for method {method_id}")
            return True, "OTP verified and MFA enabled"
        except Exception as e:
            db.rollback()
            logger.error(f"Error verifying OTP: {str(e)}")
            return False, str(e)
    
    # ==================== Picture Password ====================
    
    @staticmethod
    def hash_image(image_data: str) -> str:
        """Hash image data"""
        return hashlib.sha256(image_data.encode()).hexdigest()[:16]
    
    @staticmethod
    def setup_picture_password(user_id: int, image_data: str, image_format: str, db: Session) -> tuple[bool, str, dict]:
        """Setup picture password MFA"""
        try:
            # Validate image
            try:
                img_bytes = base64.b64decode(image_data)
                img = Image.open(BytesIO(img_bytes))
                img.verify()
            except Exception as e:
                return False, f"Invalid image: {str(e)}", {}
            
            # Hash the image
            image_hash = MFAService.hash_image(image_data)
            
            mfa_method = MFAMethod(
                user_id=user_id,
                method_type=MFAMethodType.PICTURE_PASSWORD,
                is_enabled=False,  # Wait for tap definition
                config={
                    "image_data": image_data,
                    "image_format": image_format,
                    "image_hash": image_hash,
                    "setup_complete": False
                }
            )
            
            db.add(mfa_method)
            db.commit()
            db.refresh(mfa_method)
            
            return True, "Picture uploaded", {
                "method_id": mfa_method.id,
                "image_hash": image_hash
            }
        except Exception as e:
            db.rollback()
            logger.error(f"Error setting up picture password: {str(e)}")
            return False, str(e), {}
    
    @staticmethod
    def define_picture_password(method_id: int, taps: list, tolerance_radius: float, db: Session) -> tuple[bool, str]:
        """Define picture password tap sequence"""
        try:
            mfa_method = db.query(MFAMethod).filter(MFAMethod.id == method_id).first()
            if not mfa_method or mfa_method.method_type != MFAMethodType.PICTURE_PASSWORD:
                return False, "Invalid MFA method"
            
            # Validate tap sequence (3-5 taps)
            if len(taps) < 3 or len(taps) > 5:
                return False, "Tap sequence must be 3-5 taps"
            
            # Store tap pattern
            mfa_method.config.update({
                "taps": [{
                    "x": tap.x,
                    "y": tap.y,
                    "sequence": tap.sequence
                } for tap in taps],
                "tolerance_radius": tolerance_radius,
                "setup_complete": True
            })
            
            mfa_method.is_enabled = True
            db.commit()
            
            logger.info(f"Picture password taps defined for method {method_id}")
            return True, "Picture password configured successfully"
        except Exception as e:
            db.rollback()
            logger.error(f"Error defining picture password: {str(e)}")
            return False, str(e)
    
    @staticmethod
    def verify_picture_password(method_id: int, taps: list, db: Session) -> tuple[bool, str]:
        """Verify picture password tap sequence"""
        try:
            mfa_method = db.query(MFAMethod).filter(MFAMethod.id == method_id).first()
            if not mfa_method or mfa_method.method_type != MFAMethodType.PICTURE_PASSWORD:
                return False, "Invalid MFA method"
            
            config = mfa_method.config
            stored_taps = config.get("taps", [])
            tolerance = config.get("tolerance_radius", 0.05)
            
            # Verify tap count
            if len(taps) != len(stored_taps):
                return False, "Incorrect number of taps"
            
            # Verify each tap within tolerance
            for i, (input_tap, stored_tap) in enumerate(zip(taps, stored_taps)):
                dx = abs(input_tap.x - stored_tap["x"])
                dy = abs(input_tap.y - stored_tap["y"])
                distance = (dx**2 + dy**2)**0.5
                
                if distance > tolerance:
                    return False, f"Tap {i+1} is incorrect"
            
            logger.info(f"Picture password verified for method {method_id}")
            return True, "Picture password verified"
        except Exception as e:
            logger.error(f"Error verifying picture password: {str(e)}")
            return False, str(e)
    
    # ==================== Backup Codes ====================
    
    @staticmethod
    def generate_backup_codes(count: int = 10) -> list[str]:
        """Generate backup codes"""
        codes = []
        for _ in range(count):
            code = ''.join([str(uuid.uuid4().int % 10) for _ in range(10)])
            codes.append(f"{code[:5]}-{code[5:]}")
        return codes
    
    @staticmethod
    def enable_backup_codes(user_id: int, db: Session) -> tuple[bool, str, dict]:
        """Enable backup codes"""
        try:
            codes = MFAService.generate_backup_codes()
            hashed_codes = [hashlib.sha256(code.encode()).hexdigest() for code in codes]
            
            mfa_method = MFAMethod(
                user_id=user_id,
                method_type=MFAMethodType.BACKUP_CODES,
                is_enabled=True,
                config={
                    "codes": hashed_codes,
                    "used_codes": []
                }
            )
            
            db.add(mfa_method)
            db.commit()
            
            logger.info(f"Backup codes enabled for user {user_id}")
            return True, "Backup codes generated", {"codes": codes}
        except Exception as e:
            db.rollback()
            logger.error(f"Error generating backup codes: {str(e)}")
            return False, str(e), {}
    
    @staticmethod
    def verify_backup_code(method_id: int, backup_code: str, db: Session) -> tuple[bool, str]:
        """Verify backup code"""
        try:
            mfa_method = db.query(MFAMethod).filter(MFAMethod.id == method_id).first()
            if not mfa_method or mfa_method.method_type != MFAMethodType.BACKUP_CODES:
                return False, "Invalid MFA method"
            
            config = mfa_method.config
            code_hash = hashlib.sha256(backup_code.encode()).hexdigest()
            
            if code_hash not in config.get("codes", []):
                return False, "Invalid backup code"
            
            if code_hash in config.get("used_codes", []):
                return False, "Backup code already used"
            
            # Mark as used
            config["used_codes"].append(code_hash)
            mfa_method.config = config
            flag_modified(mfa_method, "config")
            db.commit()
            
            logger.info(f"Backup code used for method {method_id}")
            return True, "Backup code verified"
        except Exception as e:
            db.rollback()
            logger.error(f"Error verifying backup code: {str(e)}")
            return False, str(e)
    
    # ==================== Mandatory MFA Setup ====================
    
    @staticmethod
    def has_verified_mfa(user: User) -> bool:
        """Check if user has any verified/enabled MFA method"""
        if not user or not user.mfa_methods:
            return False
        
        for method in user.mfa_methods:
            if not method.is_enabled:
                continue

            config = method.config or {}

            # TOTP and backup codes are verified by default when enabled.
            if method.method_type in [MFAMethodType.TOTP, MFAMethodType.BACKUP_CODES]:
                return True

            # OTP methods are considered verified once enabled and no pending OTP remains.
            if method.method_type in [MFAMethodType.SMS_OTP, MFAMethodType.EMAIL_OTP]:
                if "pending_otp" not in config:
                    return True
                continue

            # Picture password is verified when setup is complete and taps are stored.
            if method.method_type == MFAMethodType.PICTURE_PASSWORD:
                if config.get("setup_complete") and config.get("taps"):
                    return True
                continue

            # Fallback for future/other methods.
            if config.get("verified") or config.get("setup_complete"):
                return True
        
        return False
    
    @staticmethod
    def get_mfa_setup_status(user: User, db: Session) -> dict:
        """Get MFA setup status for user"""
        has_configured = bool(user.mfa_methods)
        has_verified = MFAService.has_verified_mfa(user)
        
        return {
            "mfa_required": not has_verified,  # New users or users without verified MFA
            "mfa_configured": has_configured,
            "mfa_verified": has_verified,
            "methods_count": len(user.mfa_methods),
            "methods": [
                {
                    "id": method.id,
                    "type": method.method_type.value,
                    "is_enabled": method.is_enabled,
                    "is_primary": method.is_primary
                }
                for method in user.mfa_methods
            ]
        }
    
    @staticmethod
    def get_available_mfa_methods() -> list:
        """Get list of available MFA methods"""
        return [
            {
                "type": "totp",
                "name": "Authenticator App",
                "description": "Use Google Authenticator or similar app",
                "icon": "🔐"
            },
            {
                "type": "email_otp",
                "name": "Email OTP",
                "description": "Receive code via email",
                "icon": "📧"
            },
            {
                "type": "sms_otp",
                "name": "SMS OTP",
                "description": "Receive code via SMS",
                "icon": "📱"
            },
            {
                "type": "backup_codes",
                "name": "Backup Codes",
                "description": "Use one-time backup codes",
                "icon": "💾"
            }
        ]
