from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from typing import Optional
import logging
from datetime import datetime

from config.database import get_db
from app.models import User, DeviceRegistry
from app.schemas.zero_trust import (
    DeviceRegistrationRequest, DeviceTrustResponse, TrustedDeviceResponse,
    BehaviorAnalysisRequest, BehaviorAnalysisResponse, AccessRequest, AccessDecision,
    DeviceInfo, NetworkContext, AuthenticationContext
)
from app.services.zero_trust_service import ZeroTrustService
from utils.security import verify_access_token

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/zero-trust", tags=["Zero Trust"])

# ==================== Dependency: Get current user ====================

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

# ==================== Device Trust Endpoints ====================

@router.post("/devices/register")
async def register_device(
    request: DeviceRegistrationRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Register a device as trusted"""
    success = ZeroTrustService.register_trusted_device(
        current_user.id,
        request.device_info.device_id,
        request.device_name,
        request.device_info,
        db
    )
    
    if not success:
        raise HTTPException(status_code=400, detail="Failed to register device")
    
    return {
        "success": True,
        "message": "Device registered successfully",
        "device_id": request.device_info.device_id
    }

@router.get("/devices/trusted")
async def list_trusted_devices(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List user's trusted devices"""
    devices = db.query(DeviceRegistry).filter(
        DeviceRegistry.user_id == current_user.id
    ).all()
    
    return {
        "devices": [
            {
                "id": d.id,
                "device_id": d.device_id,
                "device_name": d.device_name,
                "trust_score": d.trust_score,
                "last_used": d.last_used,
                "registered_at": d.created_at
            }
            for d in devices
        ]
    }

@router.delete("/devices/{device_id}")
async def remove_device(
    device_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Remove a trusted device"""
    device = db.query(DeviceRegistry).filter(
        DeviceRegistry.device_id == device_id,
        DeviceRegistry.user_id == current_user.id
    ).first()
    
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    
    db.delete(device)
    db.commit()
    
    logger.info(f"Device {device_id} removed for user {current_user.id}")
    
    return {"success": True, "message": "Device removed"}

# ==================== Behavior Analysis Endpoints ====================

@router.post("/analyze/behavior", response_model=BehaviorAnalysisResponse)
async def analyze_user_behavior(
    request: BehaviorAnalysisRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Analyze user behavior for anomalies"""
    analysis = ZeroTrustService.analyze_behavior(
        current_user.id,
        request.device_info,
        request.network_context,
        request.auth_context,
        db
    )
    
    return analysis

# ==================== Risk Assessment Endpoints ====================

@router.post("/risk/assess")
async def assess_access_risk(
    request: AccessRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Assess access risk for current context"""
    risk_score = ZeroTrustService.calculate_adaptive_risk_score(
        current_user.id,
        request.device_info.device_id,
        request.device_info,
        request.network_context,
        request.auth_context,
        db
    )
    
    return {
        "risk_score": risk_score.overall_risk_score,
        "risk_level": risk_score.risk_level,
        "decision": risk_score.access_decision,
        "required_actions": risk_score.required_actions,
        "confidence": risk_score.confidence,
        "risk_factors": {
            "device_risk": risk_score.risk_factors.device_risk,
            "behavior_risk": risk_score.risk_factors.behavior_risk,
            "network_risk": risk_score.risk_factors.network_risk,
            "time_risk": risk_score.risk_factors.time_risk,
            "auth_risk": risk_score.risk_factors.authentication_risk
        }
    }

@router.post("/access/decide")
async def make_access_decision(
    request: AccessRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Make comprehensive access control decision"""
    # Calculate risk
    risk_score = ZeroTrustService.calculate_adaptive_risk_score(
        current_user.id,
        request.device_info.device_id,
        request.device_info,
        request.network_context,
        request.auth_context,
        db
    )
    
    # Make decision
    decision = ZeroTrustService.make_access_decision(
        current_user.id,
        risk_score,
        db
    )
    
    # Update behavior profile
    ZeroTrustService.update_behavior_profile(
        current_user.id,
        request.device_info.device_id,
        request.network_context.country,
        db
    )
    
    return {
        "access_granted": decision.access_granted,
        "decision_reason": decision.decision_reason,
        "risk_level": decision.risk_level,
        "risk_score": decision.risk_score,
        "required_actions": decision.required_actions,
        "challenges": decision.challenges,
        "session_duration_minutes": decision.session_duration_minutes,
        "metadata": decision.metadata
    }

# ==================== Anomaly Detection Endpoints ====================

@router.get("/anomalies/recent")
async def get_recent_anomalies(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get recent detected anomalies for user"""
    from app.models import Anomaly
    
    anomalies = db.query(Anomaly).filter(
        Anomaly.user_id == current_user.id
    ).order_by(Anomaly.timestamp.desc()).limit(10).all()
    
    return {
        "anomalies": [
            {
                "id": a.id,
                "anomaly_type": a.anomaly_type,
                "severity": a.severity,
                "description": a.details.get("description", "") if a.details else "",
                "acknowledged": a.is_resolved,
                "detected_at": a.timestamp
            }
            for a in anomalies
        ]
    }

@router.post("/anomalies/{anomaly_id}/acknowledge")
async def acknowledge_anomaly(
    anomaly_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Acknowledge detected anomaly"""
    from app.models import Anomaly
    
    anomaly = db.query(Anomaly).filter(
        Anomaly.id == anomaly_id,
        Anomaly.user_id == current_user.id
    ).first()
    
    if not anomaly:
        raise HTTPException(status_code=404, detail="Anomaly not found")
    
    anomaly.is_acknowledged = True
    db.commit()
    
    return {"success": True, "message": "Anomaly acknowledged"}

# ==================== Behavior Profile Endpoints ====================

@router.get("/profile/behavior")
async def get_behavior_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user's behavior profile"""
    profile = ZeroTrustService.get_user_behavior_profile(current_user.id, db)
    
    if not profile:
        profile = {}
    
    return {
        "typical_hours": profile.get("typical_hours", []),
        "typical_days": profile.get("typical_days", []),
        "typical_locations": profile.get("typical_locations", []),
        "typical_devices": profile.get("typical_devices", []),
        "avg_session_duration": profile.get("avg_session_duration", 30)
    }

@router.post("/profile/behavior/reset")
async def reset_behavior_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Reset behavior profile to learn new patterns"""
    from app.models import BehaviorProfile
    
    profile = db.query(BehaviorProfile).filter(
        BehaviorProfile.user_id == current_user.id
    ).first()
    
    if profile:
        profile.behavior_data = {
            "typical_hours": list(range(9, 18)),
            "typical_days": [0, 1, 2, 3, 4],
            "typical_locations": [],
            "typical_devices": [],
            "avg_session_duration": 30
        }
        db.commit()
    
    return {"success": True, "message": "Behavior profile reset"}

# ==================== Risk History Endpoints ====================

@router.get("/risk/timeline")
async def get_risk_timeline(
    days: int = 7,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user's risk score timeline"""
    from app.models import AuditLog
    from datetime import timedelta
    
    start_date = datetime.utcnow() - timedelta(days=days)
    
    logs = db.query(AuditLog).filter(
        AuditLog.user_id == current_user.id,
        AuditLog.timestamp >= start_date
    ).order_by(AuditLog.timestamp).all()
    
    # Compile risk events
    risk_events = []
    avg_risk = 0.0
    
    for log in logs:
        device_info = log.device_info or {}
        risk_score = device_info.get("risk_score", 0.0)
        if risk_score > 0:
            risk_events.append({
                "timestamp": log.timestamp,
                "risk_score": risk_score,
                "action": log.action,
                "status": log.status
            })
            avg_risk += risk_score
    
    avg_risk = avg_risk / len(risk_events) if risk_events else 0
    
    return {
        "timeline": risk_events,
        "average_risk": avg_risk,
        "period_days": days,
        "total_events": len(risk_events)
    }

# ==================== Settings & Policies ====================

@router.get("/settings/trust-level")
async def get_trust_level_preference(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user's trust level preference"""
    return {
        "require_mfa": True,
        "allow_new_devices": True,
        "max_risk_tolerance": "high",  # low, medium, high
        "session_timeout_minutes": 480,
        "require_frequent_auth": False
    }

@router.post("/settings/trust-level")
async def update_trust_level_preference(
    settings: dict,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update user's trust level preference"""
    # In a real implementation, save to database
    logger.info(f"Updated trust settings for user {current_user.id}: {settings}")
    
    return {
        "success": True,
        "message": "Trust settings updated"
    }

# ==================== Access Policies Endpoints ====================

@router.get("/policies")
async def list_access_policies(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List access policies (placeholder for future implementation)"""
    # TODO: Implement actual policy storage and retrieval
    return {
        "policies": [
            {
                "id": 1,
                "name": "Standard Access Policy",
                "description": "Default policy for regular users",
                "risk_threshold": 0.7,
                "required_mfa": True,
                "session_timeout": 480,
                "created_at": datetime.utcnow(),
                "active": True
            },
            {
                "id": 2,
                "name": "Restricted Access Policy",
                "description": "Policy for sensitive operations",
                "risk_threshold": 0.3,
                "required_mfa": True,
                "session_timeout": 60,
                "created_at": datetime.utcnow(),
                "active": True
            }
        ]
    }

# ==================== Audit Logs Endpoints ====================

@router.get("/audit/logs")
async def list_audit_logs(
    current_user: User = Depends(get_current_user),
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """List audit logs for organization"""
    from app.models import AuditLog
    
    logs = db.query(AuditLog).order_by(
        AuditLog.timestamp.desc()
    ).limit(limit).all()
    
    return {
        "logs": [
            {
                "id": log.id,
                "user_id": log.user_id,
                "action": log.action,
                "status": log.status,
                "timestamp": log.timestamp,
                "ip_address": log.ip_address,
                "details": log.details if log.details else {}
            }
            for log in logs
        ],
        "total": len(logs)
    }

