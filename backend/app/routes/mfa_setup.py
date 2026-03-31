"""
MFA Setup Routes
Handles mandatory MFA setup and configuration
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.models import User, MFAMethodType
from app.services.mfa_service import MFAService
from app.routes.auth import get_current_user, get_token
from utils.rate_limiting import limiter
from config.database import get_db
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/mfa", tags=["MFA Management"])

# ==================== Request/Response Models ====================

class MFAStatusResponse(BaseModel):
    mfa_required: bool
    mfa_configured: bool
    mfa_verified: bool
    methods_count: int
    methods: list


class TOTPSetupRequest(BaseModel):
    """Request to setup TOTP"""
    pass


class TOTPSetupResponse(BaseModel):
    """Response for TOTP setup"""
    secret: str
    qr_code: str
    manual_entry_key: str


class TOTPVerifyRequest(BaseModel):
    """Request to verify TOTP setup"""
    code: str


class MFASetupCompleteRequest(BaseModel):
    """Mark MFA setup as complete"""
    pass


# ==================== Endpoints ====================

@router.get("/status", response_model=MFAStatusResponse)
def get_mfa_status(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current user's MFA status"""
    status_data = MFAService.get_mfa_setup_status(current_user, db)
    return status_data


@router.post("/required")
def check_mfa_required(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Check if user MUST setup MFA"""
    status_data = MFAService.get_mfa_setup_status(current_user, db)
    return {
        "mfa_required": status_data["mfa_required"],
        "message": "MFA setup is required" if status_data["mfa_required"] else "MFA setup not required"
    }


@router.get("/methods")
def get_available_methods():
    """Get list of available MFA methods"""
    return {"methods": MFAService.get_available_mfa_methods()}


@router.post("/totp/setup", response_model=TOTPSetupResponse)
@limiter.limit("10/hour")
def setup_totp(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Initiate TOTP setup
    Returns QR code and secret for user to scan
    """
    try:
        success, result = MFAService.setup_totp(current_user.id, db)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.get("message", "Failed to setup TOTP")
            )
        
        return {
            "secret": result.get("secret"),
            "qr_code": result.get("qr_code"),
            "manual_entry_key": result.get("secret")
        }
    except Exception as e:
        logger.error(f"Error in TOTP setup: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to initiate TOTP setup"
        )


@router.post("/totp/verify")
@limiter.limit("5/minute")
def verify_totp(
    request_data: TOTPVerifyRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Verify TOTP setup with 6-digit code
    """
    try:
        if not request_data.code or len(request_data.code) != 6:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid code format"
            )
        
        success, message = MFAService.verify_totp(current_user.id, request_data.code, db)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=message
            )
        
        logger.info(f"User {current_user.id} verified TOTP MFA")
        
        return {
            "success": True,
            "message": "TOTP verified and enabled",
            "mfa_setup_complete": MFAService.has_verified_mfa(current_user)
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error verifying TOTP: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to verify TOTP"
        )


@router.post("/email/setup")
@limiter.limit("3/hour")
def setup_email_otp(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Initiate Email OTP setup
    Sends verification code to user's email
    """
    try:
        success, message, result = MFAService.send_email_otp(current_user.id, db)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=message
            )
        
        logger.info(f"Email OTP sent to user {current_user.id}")
        
        return {
            "success": True,
            "message": "Verification code sent to your email",
            "method_id": result.get("method_id")
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error setting up email OTP: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to setup email OTP"
        )


@router.post("/email/verify")
@limiter.limit("5/minute")
def verify_email_otp(
    request_data: TOTPVerifyRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Verify Email OTP with code received
    """
    try:
        # Find the email OTP method
        from app.models import MFAMethod
        email_method = db.query(MFAMethod).filter(
            MFAMethod.user_id == current_user.id,
            MFAMethod.method_type == MFAMethodType.EMAIL_OTP
        ).first()
        
        if not email_method:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Email OTP not setup"
            )
        
        success, message = MFAService.verify_otp(email_method.id, request_data.code, db)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=message
            )
        
        logger.info(f"User {current_user.id} verified Email OTP")
        
        return {
            "success": True,
            "message": "Email OTP verified and enabled",
            "mfa_setup_complete": MFAService.has_verified_mfa(current_user)
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error verifying email OTP: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to verify email OTP"
        )


@router.post("/setup-complete")
def mark_mfa_setup_complete(
    request_data: MFASetupCompleteRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Mark MFA setup as complete for user
    User can proceed to main application after this
    """
    try:
        if not MFAService.has_verified_mfa(current_user):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="You must verify at least one MFA method first"
            )
        
        # Record in audit log
        from app.models import AuditLog
        audit_log = AuditLog(
            user_id=current_user.id,
            action="mfa_setup_complete",
            resource="mfa",
            status="success",
            ip_address="",  # TODO: get from request
            details="User completed mandatory MFA setup"
        )
        db.add(audit_log)
        db.commit()
        
        logger.info(f"User {current_user.id} completed MFA setup")
        
        return {
            "success": True,
            "message": "MFA setup complete. You can now access the application.",
            "redirect_to": "/dashboard"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error completing MFA setup: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to complete MFA setup"
        )


@router.get("/methods/list")
def get_user_mfa_methods(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all MFA methods configured by user"""
    from app.models import MFAMethod
    
    methods = db.query(MFAMethod).filter(
        MFAMethod.user_id == current_user.id
    ).all()
    
    return {
        "methods": [
            {
                "id": method.id,
                "type": method.method_type.value,
                "is_enabled": method.is_enabled,
                "is_primary": method.is_primary,
                "created_at": method.created_at.isoformat() if method.created_at else None,
                "last_used": method.last_used.isoformat() if method.last_used else None
            }
            for method in methods
        ]
    }


@router.delete("/methods/{method_id}")
def delete_mfa_method(
    method_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete an MFA method"""
    from app.models import MFAMethod
    
    try:
        method = db.query(MFAMethod).filter(
            MFAMethod.id == method_id,
            MFAMethod.user_id == current_user.id
        ).first()
        
        if not method:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="MFA method not found"
            )
        
        # Don't allow deletion of last verified method
        verified_methods = sum(
            1 for m in current_user.mfa_methods
            if m.is_enabled and m != method
        )
        
        if verified_methods == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot delete your only MFA method"
            )
        
        db.delete(method)
        db.commit()
        
        logger.info(f"User {current_user.id} deleted MFA method {method_id}")
        
        return {
            "success": True,
            "message": "MFA method deleted"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting MFA method: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete MFA method"
        )
