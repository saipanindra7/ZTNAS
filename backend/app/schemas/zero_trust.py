from pydantic import BaseModel, Field
from typing import Optional, Dict, List
from datetime import datetime
from enum import Enum

# ==================== Enums ====================

class TrustLevel(str, Enum):
    """Device trust levels"""
    UNKNOWN = "unknown"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    TRUSTED = "trusted"

class RiskLevel(str, Enum):
    """Access risk levels"""
    MINIMAL = "minimal"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class AnomalyType(str, Enum):
    """Types of detected anomalies"""
    UNUSUAL_TIME = "unusual_time"
    UNUSUAL_LOCATION = "unusual_location"
    NEW_DEVICE = "new_device"
    IMPOSSIBLE_TRAVEL = "impossible_travel"
    MULTIPLE_FAILURES = "multiple_failures"
    SUSPICIOUS_ACTIVITY = "suspicious_activity"
    GEO_VELOCITY = "geo_velocity"
    DEVICE_MISMATCH = "device_mismatch"

# ==================== Device Context ====================

class DeviceInfo(BaseModel):
    """Device information for trust evaluation"""
    device_id: str = Field(..., description="Unique device identifier")
    device_name: str = Field(..., description="User-friendly device name")
    device_type: str = Field(..., pattern="^(desktop|mobile|tablet|other)$")
    os: str = Field(..., description="Operating system")
    os_version: str = Field(..., description="OS version")
    browser: Optional[str] = None
    browser_version: Optional[str] = None

class NetworkContext(BaseModel):
    """Network/location context"""
    ip_address: str
    ip_reputation: Optional[float] = Field(None, ge=0.0, le=1.0)
    asn: Optional[str] = None  # Autonomous System Number
    country: str = Field(..., max_length=2)  # ISO 3166-1 alpha-2
    city: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    is_vpn: bool = False
    is_proxy: bool = False
    is_datacenter: bool = False

class AuthenticationContext(BaseModel):
    """Authentication/session context"""
    mfa_used: bool
    mfa_type: Optional[str] = None
    password_age_days: Optional[int] = None
    is_new_session: bool
    session_duration_minutes: Optional[int] = None

# ==================== Device Trust ====================

class DeviceRegistrationRequest(BaseModel):
    """Register a new trusted device"""
    device_name: str = Field(..., min_length=1, max_length=100)
    device_info: DeviceInfo

class DeviceTrustResponse(BaseModel):
    """Device trust evaluation response"""
    device_id: str
    trust_score: float = Field(..., ge=0.0, le=1.0)
    trust_level: TrustLevel
    is_registered: bool
    days_since_last_use: Optional[int]
    recommendations: List[str]

class TrustedDeviceResponse(BaseModel):
    """Trusted device details"""
    id: int
    device_id: str
    device_name: str
    device_type: str
    trust_score: float
    last_used: datetime
    registered_at: datetime
    
    class Config:
        from_attributes = True

# ==================== Behavior Analysis ====================

class LoginPattern(BaseModel):
    """User's typical login patterns"""
    typical_hours: List[int]  # Hour of day (0-23)
    typical_days: List[int]   # Day of week (0-6, 0=Monday)
    typical_locations: List[str]  # Typical countries/cities
    typical_devices: List[str]  # Device IDs
    login_frequency_per_day: float

class BehaviorProfile(BaseModel):
    """User's behavioral profile"""
    user_id: int
    login_pattern: LoginPattern
    avg_session_duration_minutes: float
    total_logins: int
    unique_devices: int
    unique_locations: int
    last_updated: datetime

class BehaviorAnalysisRequest(BaseModel):
    """Analyze user behavior"""
    user_id: int
    device_info: DeviceInfo
    network_context: NetworkContext
    auth_context: AuthenticationContext

class BehaviorAnalysisResponse(BaseModel):
    """Behavior analysis results"""
    behavior_score: float = Field(..., ge=0.0, le=1.0)
    is_anomalous: bool
    detected_anomalies: List[str]
    risk_factors: List[str]
    confidence: float = Field(..., ge=0.0, le=1.0)

# ==================== Anomaly Detection ====================

class AnomalyReport(BaseModel):
    """Detected anomaly"""
    user_id: int
    anomaly_type: AnomalyType
    severity: float = Field(..., ge=0.0, le=1.0)
    description: str
    metadata: Dict

class DetectedAnomaly(BaseModel):
    """Anomaly detection result"""
    id: int
    user_id: int
    anomaly_type: str
    severity: float
    description: str
    is_acknowledged: bool
    detected_at: datetime
    
    class Config:
        from_attributes = True

# ==================== Risk Scoring ====================

class RiskFactors(BaseModel):
    """Components of risk score"""
    device_risk: float = Field(..., ge=0.0, le=1.0, description="Device-based risk")
    behavior_risk: float = Field(..., ge=0.0, le=1.0, description="Behavior-based risk")
    network_risk: float = Field(..., ge=0.0, le=1.0, description="Network-based risk")
    time_risk: float = Field(..., ge=0.0, le=1.0, description="Temporal anomaly risk")
    authentication_risk: float = Field(..., ge=0.0, le=1.0, description="Auth method risk")

class AdaptiveRiskScore(BaseModel):
    """Adaptive risk assessment"""
    overall_risk_score: float = Field(..., ge=0.0, le=1.0)
    risk_level: RiskLevel
    risk_factors: RiskFactors
    access_decision: str = Field(..., pattern="^(allow|challenge|block)$")
    required_actions: List[str]  # e.g., ["require_mfa", "re_authenticate", "notify_user"]
    confidence: float = Field(..., ge=0.0, le=1.0)

# ==================== Zero Trust Policy ====================

class AccessPolicy(BaseModel):
    """Zero Trust access policy"""
    user_id: int
    require_mfa: bool
    allowed_countries: Optional[List[str]] = None
    block_countries: Optional[List[str]] = None
    require_device_registration: bool
    max_risk_score: float = Field(default=0.7, ge=0.0, le=1.0)
    require_recent_password: bool
    password_age_limit_days: int = Field(default=90)
    session_timeout_minutes: int = Field(default=30)
    concurrent_sessions_limit: int = Field(default=3)

class AccessRequest(BaseModel):
    """Zero Trust access request"""
    user_id: int
    device_info: DeviceInfo
    network_context: NetworkContext
    auth_context: AuthenticationContext
    requested_resource: Optional[str] = None

class AccessDecision(BaseModel):
    """Zero Trust access decision"""
    user_id: int
    access_granted: bool
    decision_reason: str
    required_actions: List[str]
    risk_score: float
    risk_level: RiskLevel
    challenges: List[str]  # e.g., ["/mfa/verify", "/re-auth"]
    session_duration_minutes: Optional[int]
    metadata: Dict

# ==================== Micro-segmentation ====================

class ResourceSegment(BaseModel):
    """Network resource segment"""
    segment_id: str
    name: str
    description: str
    required_trust_level: TrustLevel
    required_mfa: bool
    allowed_user_roles: List[str]
    max_concurrent_users: int

class SegmentAccessRequest(BaseModel):
    """Request access to resource segment"""
    segment_id: str
    resource_path: str
    operation: str = Field(..., pattern="^(read|write|execute|admin)$")

class SegmentAccessDecision(BaseModel):
    """Segment access decision"""
    segment_id: str
    access_granted: bool
    reason: str
    tunnel_endpoint: Optional[str] = None
    bandwidth_limit_mbps: Optional[int] = None
    duration_minutes: Optional[int] = None

# ==================== Audit & Monitoring ====================

class AccessLog(BaseModel):
    """Access attempt log"""
    user_id: int
    decision: str
    risk_score: float
    device_id: str
    ip_address: str
    location: str
    timestamp: datetime
    duration_seconds: Optional[int]

class RiskTimeline(BaseModel):
    """User's risk history"""
    user_id: int
    recent_events: List[Dict]  # List of recent access attempts
    risk_trend: str = Field(..., pattern="^(increasing|stable|decreasing)$")
    avg_risk_last_7_days: float
    avg_risk_last_30_days: float
