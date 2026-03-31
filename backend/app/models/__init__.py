from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, Float, JSON, ForeignKey, Table, Enum, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from config.database import Base
from datetime import datetime
import enum

# Association tables for Many-to-Many relationships
user_roles_association = Table(
    'user_roles',
    Base.metadata,
    Column('user_id', Integer, ForeignKey('users.id'), primary_key=True),
    Column('role_id', Integer, ForeignKey('roles.id'), primary_key=True)
)

role_permissions_association = Table(
    'role_permissions',
    Base.metadata,
    Column('role_id', Integer, ForeignKey('roles.id'), primary_key=True),
    Column('permission_id', Integer, ForeignKey('permissions.id'), primary_key=True)
)

# Enum for MFA method types
class MFAMethodType(str, enum.Enum):
    TOTP = "totp"
    SMS_OTP = "sms_otp"
    EMAIL_OTP = "email_otp"
    FIDO2 = "fido2"
    BIOMETRIC = "biometric"
    PUSH = "push"
    PICTURE_PASSWORD = "picture_password"
    BACKUP_CODES = "backup_codes"

# Enum for MFA status
class MFAStatus(str, enum.Enum):
    PENDING = "pending"
    VERIFIED = "verified"
    FAILED = "failed"

# Enum for device trust status
class DeviceTrustStatus(str, enum.Enum):
    UNTRUSTED = "untrusted"
    TRUSTED = "trusted"
    COMPROMISED = "compromised"

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    username = Column(String(100), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    first_name = Column(String(100), nullable=True)
    last_name = Column(String(100), nullable=True)
    is_active = Column(Boolean, default=True, index=True)
    is_locked = Column(Boolean, default=False)
    locked_until = Column(DateTime(timezone=True), nullable=True)  # Account locked until this time
    failed_login_attempts = Column(Integer, default=0)
    last_locked_time = Column(DateTime, nullable=True)
    lockout_count = Column(Integer, default=0)  # Number of times account has been locked
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    last_login = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    roles = relationship("Role", secondary=user_roles_association, back_populates="users")
    mfa_methods = relationship("MFAMethod", back_populates="user", cascade="all, delete-orphan")
    sessions = relationship("Session", back_populates="user", cascade="all, delete-orphan")
    devices = relationship("DeviceRegistry", back_populates="user", cascade="all, delete-orphan")
    audit_logs = relationship("AuditLog", back_populates="user", cascade="all, delete-orphan")
    behavior_profile = relationship("BehaviorProfile", back_populates="user", uselist=False, cascade="all, delete-orphan")
    anomalies = relationship("Anomaly", back_populates="user", cascade="all, delete-orphan")

class Role(Base):
    __tablename__ = "roles"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, index=True, nullable=False)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    users = relationship("User", secondary=user_roles_association, back_populates="roles")
    permissions = relationship("Permission", secondary=role_permissions_association, back_populates="roles")

class Permission(Base):
    __tablename__ = "permissions"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, index=True, nullable=False)
    description = Column(Text, nullable=True)
    resource = Column(String(100), nullable=False)  # e.g., "users", "roles", "audit_logs"
    action = Column(String(100), nullable=False)     # e.g., "create", "read", "update", "delete"
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    roles = relationship("Role", secondary=role_permissions_association, back_populates="permissions")

class MFAMethod(Base):
    __tablename__ = "mfa_methods"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, index=True)
    method_type = Column(Enum(MFAMethodType), nullable=False, index=True)
    is_enabled = Column(Boolean, default=True)
    is_primary = Column(Boolean, default=False)  # Primary MFA method
    config = Column(JSON, nullable=True)  # Store method-specific config (TOTP secret, phone number, etc.)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    last_used = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="mfa_methods")

class Session(Base):
    __tablename__ = "sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, index=True)
    token = Column(String(500), unique=True, index=True, nullable=False)
    refresh_token = Column(String(500), unique=True, nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=False, index=True)
    refresh_token_expires_at = Column(DateTime(timezone=True), nullable=True)
    device_info = Column(JSON, nullable=True)  # Store device info (OS, browser, etc.)
    ip_address = Column(String(45), nullable=True)  # IPv4 or IPv6
    user_agent = Column(String(500), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="sessions")

class DeviceRegistry(Base):
    __tablename__ = "device_registries"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, index=True)
    device_id = Column(String(255), unique=True, index=True, nullable=False)
    device_name = Column(String(255), nullable=True)
    device_fingerprint = Column(String(500), nullable=True)
    device_type = Column(String(100), nullable=True)  # "laptop", "mobile", "tablet", etc.
    os_name = Column(String(100), nullable=True)
    browser_name = Column(String(100), nullable=True)
    ip_address = Column(String(45), nullable=True)
    last_seen = Column(DateTime(timezone=True), nullable=True)
    trust_score = Column(Float, default=0.0)  # 0.0 to 1.0
    is_trusted = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="devices")

class AuditLog(Base):
    __tablename__ = "audit_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=True, index=True)
    action = Column(String(100), nullable=False, index=True)  # "login", "logout", "password_change", etc.
    resource = Column(String(100), nullable=True)  # "users", "roles", "permissions", etc.
    resource_id = Column(Integer, nullable=True)
    status = Column(String(50), nullable=False)  # "success", "failure"
    ip_address = Column(String(45), nullable=True)
    device_info = Column(JSON, nullable=True)
    details = Column(Text, nullable=True)  # Additional info
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    
    # Relationships
    user = relationship("User", back_populates="audit_logs")
    
    # Indexes for common queries
    __table_args__ = (
        Index('ix_audit_logs_user_timestamp', 'user_id', 'timestamp'),
        Index('ix_audit_logs_action_timestamp', 'action', 'timestamp'),
    )

class BehaviorProfile(Base):
    __tablename__ = "behavior_profiles"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), unique=True, nullable=False, index=True)
    login_patterns = Column(JSON, nullable=True)  # Store common login times, days, hours
    device_patterns = Column(JSON, nullable=True)  # Store common devices, browsers, OS
    location_patterns = Column(JSON, nullable=True)  # Store common locations, IPs
    typical_actions = Column(JSON, nullable=True)  # Store typical user actions
    last_updated = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="behavior_profile")

class Anomaly(Base):
    __tablename__ = "anomalies"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, index=True)
    anomaly_type = Column(String(100), nullable=False)  # "impossible_travel", "unusual_location", "unusual_time", etc.
    risk_score = Column(Float, default=0.0)  # 0.0 to 1.0
    severity = Column(String(50), nullable=False)  # "low", "medium", "high", "critical"
    details = Column(JSON, nullable=True)  # Store anomaly-specific details
    is_resolved = Column(Boolean, default=False)
    resolution_notes = Column(Text, nullable=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    
    # Relationships
    user = relationship("User", back_populates="anomalies")

# ==================== ACADEMIC DATA MODELS ====================

class Class(Base):
    """Course/Class model for student academic tracking"""
    __tablename__ = "classes"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    code = Column(String(50), unique=True, nullable=False, index=True)
    description = Column(Text, nullable=True)
    faculty_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    department = Column(String(100), nullable=True)
    academic_year = Column(String(50), nullable=False)
    semester = Column(Integer, nullable=False)  # 1, 2, etc.
    max_attendance_required = Column(Integer, default=75)  # Minimum attendance percentage
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    attendance_records = relationship("AttendanceRecord", back_populates="class_obj", cascade="all, delete-orphan")
    marks_records = relationship("MarksRecord", back_populates="class_obj", cascade="all, delete-orphan")

class AttendanceRecord(Base):
    """Student attendance tracking for classes"""
    __tablename__ = "attendance_records"
    
    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey('users.id'), nullable=False, index=True)
    class_id = Column(Integer, ForeignKey('classes.id'), nullable=False, index=True)
    attendance_date = Column(DateTime(timezone=True), nullable=False, index=True)
    status = Column(String(20), nullable=False)  # "PRESENT", "ABSENT", "LEAVE", "LATE"
    remarks = Column(Text, nullable=True)
    marked_by = Column(Integer, ForeignKey('users.id'), nullable=True)  # Faculty who marked attendance
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    class_obj = relationship("Class", back_populates="attendance_records")

class MarksRecord(Base):
    """Student marks/grades for assessments"""
    __tablename__ = "marks_records"
    
    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey('users.id'), nullable=False, index=True)
    class_id = Column(Integer, ForeignKey('classes.id'), nullable=False, index=True)
    exam_type = Column(String(100), nullable=False)  # "mid_term", "final", "quiz", "assignment"
    marks_obtained = Column(Float, nullable=False)
    total_marks = Column(Float, nullable=False, default=100)
    percentage = Column(Float, nullable=True)  # Auto-calculated
    grade = Column(String(10), nullable=True)  # "A+", "A", "B+", "B", "C", "D", "F"
    remarks = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    class_obj = relationship("Class", back_populates="marks_records")

class StudentFees(Base):
    """Student fee payment tracking"""
    __tablename__ = "student_fees"
    
    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey('users.id'), nullable=False, index=True)
    academic_year = Column(String(50), nullable=False, index=True)
    semester = Column(Integer, nullable=False)
    total_fee = Column(Float, nullable=False)
    paid_amount = Column(Float, default=0.0)
    fee_status = Column(String(50), nullable=False)  # "PAID", "PENDING", "PARTIAL", "OVERDUE"
    due_date = Column(DateTime(timezone=True), nullable=False)
    payment_date = Column(DateTime(timezone=True), nullable=True)  # First payment date
    last_payment_date = Column(DateTime(timezone=True), nullable=True)
    payment_method = Column(String(50), nullable=True)  # "BANK_TRANSFER", "CASH", "CHEQUE", "UPI"
    transaction_ref = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

# Import for convenience
__all__ = [
    'User',
    'Role',
    'Permission',
    'MFAMethod',
    'Session',
    'DeviceRegistry',
    'AuditLog',
    'BehaviorProfile',
    'Anomaly',
    'Class',
    'AttendanceRecord',
    'MarksRecord',
    'StudentFees',
    'MFAMethodType',
    'MFAStatus',
    'DeviceTrustStatus',
]
