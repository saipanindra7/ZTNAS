from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

# ==================== TOTP (Google Authenticator) ====================

class TOTPSetupRequest(BaseModel):
    """Request to setup TOTP MFA"""
    pass

class TOTPSetupResponse(BaseModel):
    """TOTP setup response with QR code"""
    secret: str
    qr_code_url: str
    manual_entry_key: str
    
    class Config:
        example = {
            "secret": "JBSWY3DPEBLW64TMMQ======",
            "qr_code_url": "data:image/png;base64,iVBORw0KGgoAAAANS...",
            "manual_entry_key": "JBSWY3DPEBLW64TMMQ======"
        }

class TOTPVerifyRequest(BaseModel):
    """Verify TOTP code"""
    totp_code: str = Field(..., min_length=6, max_length=6)

# ==================== SMS/Email OTP ====================

class SMSOTPSetupRequest(BaseModel):
    """Setup SMS OTP MFA"""
    phone_number: str = Field(..., pattern=r"^\+?1?\d{9,15}$")
    country_code: Optional[str] = None

class EmailOTPSetupRequest(BaseModel):
    """Setup Email OTP MFA"""
    email: Optional[str] = None  # If not provided, use user's registered email

class OTPVerifyRequest(BaseModel):
    """Verify OTP code"""
    otp_code: str = Field(..., min_length=6, max_length=6)
    method_id: int

class ResendOTPRequest(BaseModel):
    """Request to resend OTP"""
    method_id: int

class OTPResponse(BaseModel):
    """OTP sent response"""
    message: str
    method_id: int
    expires_in: int  # seconds

# ==================== FIDO2 Hardware Token ====================

class FIDO2RegistrationStart(BaseModel):
    """Start FIDO2 registration challenge"""
    device_name: str = Field(..., min_length=1, max_length=100)

class FIDO2RegistrationStartResponse(BaseModel):
    """FIDO2 registration challenge"""
    challenge: str
    rp: dict
    user: dict
    pubKeyCredParams: list

class FIDO2RegistrationComplete(BaseModel):
    """Complete FIDO2 registration"""
    id: str
    rawId: str
    response: dict
    type: str = "public-key"

class FIDO2AuthenticationStart(BaseModel):
    """Start FIDO2 authentication challenge"""
    pass

class FIDO2AuthenticationStartResponse(BaseModel):
    """FIDO2 authentication challenge"""
    challenge: str
    timeout: int
    rpId: str
    allowCredentials: list
    userVerification: str

class FIDO2AuthenticationComplete(BaseModel):
    """Complete FIDO2 authentication"""
    id: str
    rawId: str
    response: dict
    type: str = "public-key"

# ==================== Biometric Authentication ====================

class BiometricSetupRequest(BaseModel):
    """Setup biometric authentication"""
    biometric_type: str = Field(..., pattern="^(fingerprint|face|iris|palm)$")
    device_name: Optional[str] = None

class BiometricVerifyRequest(BaseModel):
    """Verify biometric authentication"""
    biometric_data: str  # Base64 encoded biometric template
    biometric_type: str = Field(..., pattern="^(fingerprint|face|iris|palm)$")

# ==================== Picture Password ====================

class PicturePasswordSetupRequest(BaseModel):
    """Setup picture password MFA"""
    image_data: str
    image_format: str = Field(..., pattern="^(jpeg|png|jpg)$")

class PicturePasswordSetupResponse(BaseModel):
    """Picture password setup response"""
    image_hash: str
    setup_complete: bool
    next_step: str  # "define_taps"
    
    class Config:
        example = {
            "image_hash": "abc123def456...",
            "setup_complete": False,
            "next_step": "define_taps"
        }

class TapCoordinate(BaseModel):
    """Single tap coordinate"""
    x: float = Field(..., ge=0, le=1)  # Normalized 0-1
    y: float = Field(..., ge=0, le=1)  # Normalized 0-1
    sequence: int  # Order of tap

class PicturePasswordDefineRequest(BaseModel):
    """Define picture password taps"""
    image_hash: str
    taps: list[TapCoordinate] = Field(..., min_items=3, max_items=5)
    tolerance_radius: float = Field(default=0.05, ge=0.01, le=0.2)  # Normalized

class PicturePasswordVerifyRequest(BaseModel):
    """Verify picture password"""
    method_id: int
    image_hash: str
    taps: list[TapCoordinate] = Field(..., min_items=3, max_items=5)

# ==================== Push Notifications ====================

class PushNotificationSetupRequest(BaseModel):
    """Setup push notification MFA"""
    device_name: str = Field(..., min_length=1, max_length=100)
    device_token: Optional[str] = None  # For mobile apps

class PushNotificationResponse(BaseModel):
    """Push notification approval/denial"""
    request_id: str
    approved: bool
    action: str = Field(..., pattern="^(approve|deny)$")

class PushNotificationStatusRequest(BaseModel):
    """Check push notification status"""
    request_id: str

# ==================== Backup Codes ====================

class BackupCodesResponse(BaseModel):
    """Backup codes response"""
    method_id: int
    codes: list[str]
    generated_at: datetime
    message: str

class BackupCodeVerifyRequest(BaseModel):
    """Verify backup code"""
    backup_code: str = Field(..., min_length=8, max_length=12)

# ==================== Generic MFA ====================

class MFAMethodSetupResponse(BaseModel):
    """Generic MFA method setup response"""
    method_id: int
    method_type: str
    is_enabled: bool
    is_primary: bool
    created_at: datetime

class MFAMethodResponse(BaseModel):
    """MFA method details"""
    id: int
    method_type: str
    is_enabled: bool
    is_primary: bool
    last_used: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True

class MFAListResponse(BaseModel):
    """List of MFA methods"""
    method_type: str
    is_enabled: bool
    is_primary: bool
    last_used: Optional[datetime]

    class Config:
        from_attributes = True

class MFAVerifyRequest(BaseModel):
    """Generic MFA verification"""
    method_id: int
    verification_code: Optional[str] = None
    verification_data: Optional[dict] = None

class MFADisableRequest(BaseModel):
    """Disable MFA method"""
    method_id: int
    password: str  # Require password to disable MFA

class SetPrimaryMFARequest(BaseModel):
    """Set primary MFA method"""
    method_id: int
