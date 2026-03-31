from fastapi import APIRouter, Depends, HTTPException, Header, status
from sqlalchemy.orm import Session
from typing import Optional
import logging
from datetime import datetime, timedelta

from config.database import get_db
from app.models import MFAMethod, User, MFAMethodType
from app.schemas.mfa import (
    TOTPSetupRequest, TOTPSetupResponse, TOTPVerifyRequest,
    SMSOTPSetupRequest, EmailOTPSetupRequest, OTPVerifyRequest, ResendOTPRequest, OTPResponse,
    PicturePasswordSetupRequest, PicturePasswordSetupResponse, PicturePasswordDefineRequest,
    PicturePasswordVerifyRequest, TapCoordinate,
    BackupCodesResponse, BackupCodeVerifyRequest,
    MFAMethodResponse, MFAListResponse, MFAVerifyRequest, MFADisableRequest, SetPrimaryMFARequest
)
from app.services.mfa_service import MFAService
from utils.security import verify_access_token

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/mfa", tags=["MFA"])

# ==================== Dependency: Extract token from Authorization header ====================

def get_token_from_header(authorization: Optional[str] = Header(None)) -> str:
    """Extract Bearer token from Authorization header"""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid authorization header")
    return authorization.replace("Bearer ", "")

def get_current_user(
    token: str = Depends(get_token_from_header),
    db: Session = Depends(get_db)
) -> User:
    """Get current user from token"""
    payload = verify_access_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    user = db.query(User).filter(User.id == int(user_id)).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return user

# ==================== TOTP Endpoints ====================

@router.post("/totp/setup", response_model=TOTPSetupResponse)
async def totp_setup(
    request: TOTPSetupRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Setup TOTP (Google Authenticator)
    Returns QR code and secret for scanning
    """
    result = MFAService.setup_totp(current_user.id, db)
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("message"))
    
    return {
        "secret": result["secret"],
        "qr_code_url": result["qr_code_url"],
        "manual_entry_key": result["manual_entry_key"]
    }

@router.post("/totp/enroll")
async def totp_enroll(
    request: TOTPVerifyRequest,
    secret: str = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Verify TOTP code and enroll MFA
    """
    if not secret:
        raise HTTPException(status_code=400, detail="Secret required")
    
    success, message, mfa_data = MFAService.enroll_totp(current_user.id, secret, request.totp_code, db)
    if not success:
        raise HTTPException(status_code=400, detail=message)
    
    return {
        "success": True,
        "message": message,
        "method_id": mfa_data.get("id")
    }

# ==================== SMS OTP Endpoints ====================

@router.post("/sms/setup", response_model=OTPResponse)
async def sms_otp_setup(
    request: SMSOTPSetupRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Setup SMS OTP MFA"""
    success, message, mfa_data = MFAService.setup_sms_otp(current_user.id, request.phone_number, db)
    if not success:
        raise HTTPException(status_code=400, detail=message)
    
    return {
        "message": message,
        "method_id": mfa_data.get("method_id"),
        "expires_in": 300
    }

# ==================== Email OTP Endpoints ====================

@router.post("/email/setup", response_model=OTPResponse)
async def email_otp_setup(
    request: EmailOTPSetupRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Setup Email OTP MFA"""
    success, message, mfa_data = MFAService.setup_email_otp(current_user.id, request.email, db)
    if not success:
        raise HTTPException(status_code=400, detail=message)
    
    return {
        "message": message,
        "method_id": mfa_data.get("method_id"),
        "expires_in": 600
    }

@router.post("/otp/verify")
async def otp_verify(
    request: OTPVerifyRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Verify OTP code"""
    success, message = MFAService.verify_otp(request.method_id, request.otp_code, db)
    if not success:
        raise HTTPException(status_code=400, detail=message)
    
    return {"success": True, "message": message}

@router.post("/otp/resend")
async def resend_otp(
    request: ResendOTPRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Resend OTP code"""
    # Get the MFA method
    mfa_method = db.query(MFAMethod).filter(
        MFAMethod.id == request.method_id,
        MFAMethod.user_id == current_user.id
    ).first()
    
    if not mfa_method:
        raise HTTPException(status_code=404, detail="MFA method not found")
    
    # Generate new OTP
    new_otp = MFAService.generate_otp()
    config = mfa_method.config
    config["pending_otp"] = new_otp
    config["otp_expires"] = (datetime.utcnow() + timedelta(minutes=5)).isoformat()
    config["verification_attempts"] = 0
    mfa_method.config = config
    db.commit()
    
    logger.info(f"OTP resent (DEV): {new_otp}")
    
    return {
        "success": True,
        "message": "OTP resent",
        "expires_in": 300
    }

# ==================== Picture Password Endpoints ====================

@router.post("/picture/setup", response_model=PicturePasswordSetupResponse)
async def picture_password_setup(
    request: PicturePasswordSetupRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Upload image for picture password setup"""
    success, message, mfa_data = MFAService.setup_picture_password(
        current_user.id, request.image_data, request.image_format, db
    )
    if not success:
        raise HTTPException(status_code=400, detail=message)
    
    return {
        "image_hash": mfa_data.get("image_hash"),
        "setup_complete": False,
        "next_step": "define_taps"
    }

@router.post("/picture/define")
async def picture_password_define(
    request: PicturePasswordDefineRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Define tap sequence for picture password"""
    # In a real implementation, you'd pass method_id in the request
    # For now, we'll need to get it from image_hash or handle differently
    # This is a simplified version - in production, include method_id in request
    
    mfa_method = db.query(MFAMethod).filter(
        MFAMethod.user_id == current_user.id,
        MFAMethod.method_type == "PICTURE_PASSWORD"
    ).order_by(MFAMethod.id.desc()).first()
    
    if not mfa_method:
        raise HTTPException(status_code=404, detail="MFA method not found")
    
    success, message = MFAService.define_picture_password(
        mfa_method.id, request.taps, request.tolerance_radius, db
    )
    if not success:
        raise HTTPException(status_code=400, detail=message)
    
    return {
        "success": True,
        "message": message,
        "method_id": mfa_method.id
    }

# ==================== Backup Codes Endpoints ====================

@router.post("/backup-codes/generate", response_model=BackupCodesResponse)
async def generate_backup_codes(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Generate backup codes"""
    success, message, backup_data = MFAService.enable_backup_codes(current_user.id, db)
    if not success:
        raise HTTPException(status_code=400, detail=message)
    
    # Get the method_id of the newly created backup codes method
    mfa_method = db.query(MFAMethod).filter(
        MFAMethod.user_id == current_user.id,
        MFAMethod.method_type == "BACKUP_CODES"
    ).order_by(MFAMethod.id.desc()).first()
    
    return {
        "method_id": mfa_method.id if mfa_method else None,
        "codes": backup_data.get("codes"),
        "generated_at": datetime.utcnow(),
        "message": message
    }

@router.post("/backup-codes/verify")
async def verify_backup_code(
    request: BackupCodeVerifyRequest,
    method_id: int = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Verify backup code"""
    if not method_id:
        raise HTTPException(status_code=400, detail="Method ID required")
    
    success, message = MFAService.verify_backup_code(method_id, request.backup_code, db)
    if not success:
        raise HTTPException(status_code=400, detail=message)
    
    return {"success": True, "message": message}

# ==================== MFA Management Endpoints ====================

@router.get("/status")
async def get_mfa_status(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Check MFA setup status for user"""
    methods = db.query(MFAMethod).filter(MFAMethod.user_id == current_user.id).all()
    primary_method = next((m for m in methods if m.is_primary), None)
    is_admin = any(role.name.lower() == "admin" for role in current_user.roles)
    mfa_verified = MFAService.has_verified_mfa(current_user)
    
    return {
        "mfa_required": (not is_admin) and (not mfa_verified),
        "mfa_verified": mfa_verified,
        "is_admin": is_admin,
        "method_count": len(methods),
        "methods": [m.method_type for m in methods],
        "primary_method": primary_method.method_type if primary_method else None
    }

@router.get("/methods")
async def list_mfa_methods(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List all MFA methods for user"""
    methods = db.query(MFAMethod).filter(MFAMethod.user_id == current_user.id).all()
    
    return {
        "methods": [
            {
                "id": m.id,
                "method_type": m.method_type,
                "is_enabled": m.is_enabled,
                "is_primary": m.is_primary,
                "last_used": m.last_used,
                "created_at": m.created_at
            }
            for m in methods
        ]
    }

@router.delete("/methods/{method_id}")
async def disable_mfa_method(
    method_id: int,
    request: MFADisableRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Disable MFA method"""
    mfa_method = db.query(MFAMethod).filter(
        MFAMethod.id == method_id,
        MFAMethod.user_id == current_user.id
    ).first()
    
    if not mfa_method:
        raise HTTPException(status_code=404, detail="MFA method not found")
    
    # Verify password
    from utils.security import verify_password
    if not verify_password(request.password, current_user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid password")
    
    db.delete(mfa_method)
    db.commit()
    
    logger.info(f"MFA method {method_id} disabled for user {current_user.id}")
    
    return {"success": True, "message": "MFA method disabled"}

@router.post("/methods/{method_id}/set-primary")
async def set_primary_mfa(
    method_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Set MFA method as primary"""
    # Find the method
    mfa_method = db.query(MFAMethod).filter(
        MFAMethod.id == method_id,
        MFAMethod.user_id == current_user.id
    ).first()
    
    if not mfa_method:
        raise HTTPException(status_code=404, detail="MFA method not found")
    
    # Remove primary from all other methods
    db.query(MFAMethod).filter(
        MFAMethod.user_id == current_user.id,
        MFAMethod.id != method_id
    ).update({"is_primary": False})
    
    # Set as primary
    mfa_method.is_primary = True
    db.commit()
    
    logger.info(f"MFA method {method_id} set as primary for user {current_user.id}")
    
    return {"success": True, "message": "Primary MFA method updated"}

# ==================== MFA Verification (During Login) ====================

@router.post("/verify")
async def verify_mfa(
    request: MFAVerifyRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Verify MFA during login
    This endpoint is called after password authentication succeeds
    """
    mfa_method = db.query(MFAMethod).filter(MFAMethod.id == request.method_id).first()
    if not mfa_method:
        raise HTTPException(status_code=404, detail="MFA method not found")
    
    # Route to appropriate verification method
    method_type = mfa_method.method_type
    
    if method_type == MFAMethodType.TOTP:
        success, message = (
            MFAService.verify_totp(mfa_method.config["secret"], request.verification_code),
            "TOTP verified"
        ) if MFAService.verify_totp(mfa_method.config["secret"], request.verification_code) else (False, "Invalid TOTP")
    
    elif method_type in [MFAMethodType.SMS_OTP, MFAMethodType.EMAIL_OTP]:
        success, message = MFAService.verify_otp(request.method_id, request.verification_code, db)
    
    elif method_type == MFAMethodType.PICTURE_PASSWORD:
        # verification_data should contain taps
        taps_data = request.verification_data.get("taps", [])
        taps = [TapCoordinate(x=t["x"], y=t["y"], sequence=t["sequence"]) for t in taps_data]
        success, message = MFAService.verify_picture_password(request.method_id, taps, db)
    
    elif method_type == MFAMethodType.BACKUP_CODES:
        success, message = MFAService.verify_backup_code(request.method_id, request.verification_code, db)
    
    else:
        raise HTTPException(status_code=400, detail="Unsupported MFA method")
    
    if not success:
        raise HTTPException(status_code=400, detail=message)
    
    # Update last_used
    mfa_method.last_used = datetime.utcnow()
    db.commit()
    
    return {"success": True, "message": message}
