from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime

# ==================== Authentication Request/Response Schemas ====================

class UserRegisterRequest(BaseModel):
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=100)
    password: str = Field(..., min_length=8)
    first_name: Optional[str] = Field(None, max_length=100)
    last_name: Optional[str] = Field(None, max_length=100)

    class Config:
        example = {
            "email": "user@example.com",
            "username": "johndoe",
            "password": "SecurePassword123",
            "first_name": "John",
            "last_name": "Doe"
        }

class UserLoginRequest(BaseModel):
    username: str
    password: str
    device_name: Optional[str] = None

    class Config:
        example = {
            "username": "johndoe",
            "password": "SecurePassword123",
            "device_name": "My Laptop"
        }

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds

    class Config:
        example = {
            "access_token": "eyJhbGc...",
            "refresh_token": "eyJhbGc...",
            "token_type": "bearer",
            "expires_in": 1800
        }

class RefreshTokenRequest(BaseModel):
    refresh_token: str

class PasswordResetRequest(BaseModel):
    email: EmailStr

class PasswordResetConfirm(BaseModel):
    token: str
    new_password: str = Field(..., min_length=8)

class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str = Field(..., min_length=8)

# ==================== User Response Schemas ====================

class UserBasic(BaseModel):
    id: int
    email: str
    username: str
    first_name: Optional[str]
    last_name: Optional[str]
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True

class UserDetail(UserBasic):
    is_locked: bool
    failed_login_attempts: int
    last_login: Optional[datetime]
    updated_at: datetime
    roles: list['RoleResponse'] = []

    class Config:
        from_attributes = True

class UserListResponse(BaseModel):
    id: int
    email: str
    username: str
    is_active: bool
    last_login: Optional[datetime]

    class Config:
        from_attributes = True

# ==================== Role & Permission Schemas ====================

class PermissionResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    resource: str
    action: str

    class Config:
        from_attributes = True

class RoleResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    permissions: list[PermissionResponse] = []

    class Config:
        from_attributes = True

class RoleCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None

    class Config:
        example = {
            "name": "Admin",
            "description": "Administrator role with full access"
        }

# ==================== Session & Device Schemas ====================

class SessionResponse(BaseModel):
    id: int
    user_id: int
    device_name: Optional[str]
    ip_address: Optional[str]
    is_active: bool
    created_at: datetime
    expires_at: datetime

    class Config:
        from_attributes = True

# ==================== Audit Log Schemas ====================

class AuditLogResponse(BaseModel):
    id: int
    user_id: Optional[int]
    action: str
    resource: Optional[str]
    status: str
    ip_address: Optional[str]
    timestamp: datetime
    details: Optional[str]

    class Config:
        from_attributes = True

# ==================== Standard Response Models ====================

class SuccessResponse(BaseModel):
    success: bool
    message: str
    data: Optional[dict] = None

class ErrorResponse(BaseModel):
    success: bool = False
    message: str
    error_code: Optional[str] = None
