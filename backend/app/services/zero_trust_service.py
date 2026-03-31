import hashlib
import json
import math
from datetime import datetime, timedelta
from typing import List, Dict, Tuple, Optional
from sqlalchemy.orm import Session
import logging

from app.models import User, DeviceRegistry, BehaviorProfile, Anomaly, AuditLog, Session as SessionModel
from app.schemas.zero_trust import (
    TrustLevel, RiskLevel, AnomalyType, DeviceInfo, NetworkContext, AuthenticationContext,
    DeviceTrustResponse, BehaviorAnalysisResponse, AdaptiveRiskScore, AccessDecision, RiskFactors
)
from config.settings import settings

logger = logging.getLogger(__name__)

class ZeroTrustService:
    """Service for Zero Trust access control and evaluation"""
    
    # ==================== Device Trust Scoring ====================
    
    @staticmethod
    def calculate_device_trust_score(
        user_id: int,
        device_id: str,
        device_info: DeviceInfo,
        db: Session
    ) -> Tuple[float, bool]:
        """
        Calculate device trust score (0-1)
        Returns: (trust_score, is_known_device)
        """
        try:
            # Check if device is registered
            registered_device = db.query(DeviceRegistry).filter(
                DeviceRegistry.user_id == user_id,
                DeviceRegistry.device_id == device_id
            ).first()
            
            trust_score = 0.0
            
            if not registered_device:
                # New/unknown device
                trust_score = 0.1  # Start with low trust
                return trust_score, False
            
            # Device is known
            days_since_use = (datetime.utcnow() - registered_device.last_used).days
            
            # Scoring logic
            base_score = registered_device.trust_score if registered_device.trust_score else 0.5
            
            # Increase trust if recently used
            if days_since_use == 0:
                trust_score = base_score + 0.15
            elif days_since_use <= 7:
                trust_score = base_score + 0.10
            elif days_since_use <= 30:
                trust_score = base_score + 0.05
            else:
                trust_score = base_score * 0.8  # Decay trust over time
            
            # OS/Browser consistency check
            if (device_info.os and registered_device.device_info.get("os") and 
                device_info.os != registered_device.device_info.get("os")):
                trust_score -= 0.1  # OS changed, reduce trust
            
            # Clamp to valid range
            trust_score = max(0.0, min(1.0, trust_score))
            
            # Update last_used
            registered_device.last_used = datetime.utcnow()
            db.commit()
            
            return trust_score, True
        except Exception as e:
            logger.error(f"Error calculating device trust: {str(e)}")
            return 0.1, False
    
    @staticmethod
    def register_trusted_device(
        user_id: int,
        device_id: str,
        device_name: str,
        device_info: DeviceInfo,
        db: Session
    ) -> bool:
        """Register a device as trusted"""
        try:
            # Check if already registered
            existing = db.query(DeviceRegistry).filter(
                DeviceRegistry.user_id == user_id,
                DeviceRegistry.device_id == device_id
            ).first()
            
            if existing:
                existing.device_name = device_name
                existing.trust_score = 0.9
                existing.last_used = datetime.utcnow()
            else:
                device = DeviceRegistry(
                    user_id=user_id,
                    device_id=device_id,
                    device_name=device_name,
                    device_info=device_info.dict(),
                    trust_score=0.8
                )
                db.add(device)
            
            db.commit()
            logger.info(f"Device {device_id} registered for user {user_id}")
            return True
        except Exception as e:
            db.rollback()
            logger.error(f"Error registering device: {str(e)}")
            return False
    
    # ==================== Behavioral Analysis ====================
    
    @staticmethod
    def get_user_behavior_profile(user_id: int, db: Session) -> Optional[Dict]:
        """Get or create user behavior profile"""
        try:
            profile = db.query(BehaviorProfile).filter(
                BehaviorProfile.user_id == user_id
            ).first()
            
            if not profile:
                # Create default profile
                profile = BehaviorProfile(
                    user_id=user_id,
                    behavior_data={
                        "typical_hours": list(range(9, 18)),  # 9 AM to 6 PM
                        "typical_days": [0, 1, 2, 3, 4],  # Mon-Fri
                        "typical_locations": [],
                        "typical_devices": [],
                        "avg_session_duration": 30
                    }
                )
                db.add(profile)
                db.commit()
            
            return profile.behavior_data if profile.behavior_data else {}
        except Exception as e:
            logger.error(f"Error getting behavior profile: {str(e)}")
            return None
    
    @staticmethod
    def analyze_behavior(
        user_id: int,
        device_info: DeviceInfo,
        network_context: NetworkContext,
        auth_context: AuthenticationContext,
        db: Session
    ) -> BehaviorAnalysisResponse:
        """Analyze current behavior against profile"""
        try:
            profile = ZeroTrustService.get_user_behavior_profile(user_id, db)
            now = datetime.utcnow()
            
            anomalies = []
            risk_score = 0.0
            
            # Check time anomaly
            current_hour = now.hour
            typical_hours = profile.get("typical_hours", list(range(9, 18)))
            if current_hour not in typical_hours:
                anomalies.append("unusual_login_time")
                risk_score += 0.15
            
            # Check day anomaly
            current_day = now.weekday()
            typical_days = profile.get("typical_days", [0, 1, 2, 3, 4])
            if current_day not in typical_days:
                anomalies.append("unusual_login_day")
                risk_score += 0.10
            
            # Check location anomaly
            user_locations = profile.get("typical_locations", [])
            if network_context.country not in user_locations and user_locations:
                anomalies.append("unusual_location")
                risk_score += 0.20
            
            # Check device anomaly
            typical_devices = profile.get("typical_devices", [])
            if device_info.device_id not in typical_devices and typical_devices:
                anomalies.append("new_device")
                risk_score += 0.15
            
            # MFA check
            if auth_context.mfa_used:
                risk_score *= 0.7  # MFA reduces risk
            
            behavior_score = max(0.0, min(1.0, 1.0 - risk_score))
            
            return BehaviorAnalysisResponse(
                behavior_score=behavior_score,
                is_anomalous=len(anomalies) > 0,
                detected_anomalies=anomalies,
                risk_factors=[f"Behavior: {a}" for a in anomalies],
                confidence=0.85
            )
        except Exception as e:
            logger.error(f"Error analyzing behavior: {str(e)}")
            return BehaviorAnalysisResponse(
                behavior_score=0.5,
                is_anomalous=False,
                detected_anomalies=[],
                risk_factors=[],
                confidence=0.0
            )
    
    # ==================== Anomaly Detection ====================
    
    @staticmethod
    def detect_anomalies(
        user_id: int,
        device_id: str,
        network_context: NetworkContext,
        db: Session
    ) -> List[Dict]:
        """Detect security anomalies"""
        anomalies = []
        
        try:
            # Get user's recent activity
            recent_sessions = db.query(SessionModel).filter(
                SessionModel.user_id == user_id
            ).order_by(SessionModel.created_at.desc()).limit(10).all()
            
            if not recent_sessions:
                return anomalies
            
            # Impossible travel detection
            last_session = recent_sessions[0]
            if len(recent_sessions) >= 2:
                prev_session = recent_sessions[1]
                time_diff_hours = (last_session.created_at - prev_session.created_at).total_seconds() / 3600
                
                # If less than 2 hours and different countries, flag impossible travel
                if time_diff_hours < 2 and network_context.country != last_session.ip_address:
                    anomalies.append({
                        "type": AnomalyType.IMPOSSIBLE_TRAVEL,
                        "severity": 0.8,
                        "description": "Geographically impossible travel detected"
                    })
            
            # VPN/Proxy anomaly
            if network_context.is_vpn or network_context.is_proxy:
                anomalies.append({
                    "type": AnomalyType.SUSPICIOUS_ACTIVITY,
                    "severity": 0.3,
                    "description": "VPN/Proxy detected"
                })
            
            # Datacenter IP anomaly
            if network_context.is_datacenter:
                anomalies.append({
                    "type": AnomalyType.SUSPICIOUS_ACTIVITY,
                    "severity": 0.6,
                    "description": "Login from datacenter IP address"
                })
            
            # Check for multiple failed attempts
            failed_attempts = db.query(User).filter(
                User.id == user_id,
                User.failed_login_attempts > 3
            ).first()
            
            if failed_attempts:
                anomalies.append({
                    "type": AnomalyType.MULTIPLE_FAILURES,
                    "severity": 0.7,
                    "description": f"{failed_attempts.failed_login_attempts} failed login attempts"
                })
            
            return anomalies
        except Exception as e:
            logger.error(f"Error detecting anomalies: {str(e)}")
            return anomalies
    
    # ==================== Risk Scoring ====================
    
    @staticmethod
    def calculate_adaptive_risk_score(
        user_id: int,
        device_id: str,
        device_info: DeviceInfo,
        network_context: NetworkContext,
        auth_context: AuthenticationContext,
        db: Session
    ) -> AdaptiveRiskScore:
        """Calculate comprehensive adaptive risk score"""
        try:
            # Component scores (0-1, higher = more risky)
            
            # 1. Device Risk
            device_trust, is_known = ZeroTrustService.calculate_device_trust_score(
                user_id, device_id, device_info, db
            )
            device_risk = 1.0 - device_trust
            
            # 2. Behavior Risk
            behavior_analysis = ZeroTrustService.analyze_behavior(
                user_id, device_info, network_context, auth_context, db
            )
            behavior_risk = 1.0 - behavior_analysis.behavior_score
            
            # 3. Network Risk
            network_risk = 0.0
            if network_context.is_vpn:
                network_risk += 0.15
            if network_context.is_proxy:
                network_risk += 0.15
            if network_context.is_datacenter:
                network_risk += 0.25
            if network_context.ip_reputation and network_context.ip_reputation < 0.5:
                network_risk += 0.20
            network_risk = min(1.0, network_risk)
            
            # 4. Time Risk
            time_risk = 0.0
            now_hour = datetime.utcnow().hour
            if now_hour < 6 or now_hour > 22:  # Unusual hours
                time_risk = 0.2
            
            # 5. Authentication Risk
            auth_risk = 0.3  # Base risk for password only
            if auth_context.mfa_used:
                auth_risk = 0.05  # Very low risk with MFA
            if auth_context.password_age_days and auth_context.password_age_days > 90:
                auth_risk += 0.1
            
            # Anomalies
            anomalies = ZeroTrustService.detect_anomalies(user_id, device_id, network_context, db)
            anomaly_risk = len(anomalies) * 0.15
            
            # Combine scores (weighted average)
            weights = {
                "device": 0.25,
                "behavior": 0.20,
                "network": 0.20,
                "time": 0.10,
                "auth": 0.20,
                "anomaly": 0.05
            }
            
            overall_risk = (
                device_risk * weights["device"] +
                behavior_risk * weights["behavior"] +
                network_risk * weights["network"] +
                time_risk * weights["time"] +
                auth_risk * weights["auth"] +
                min(1.0, anomaly_risk) * weights["anomaly"]
            )
            
            # Determine risk level
            if overall_risk < 0.2:
                risk_level = RiskLevel.MINIMAL
            elif overall_risk < 0.4:
                risk_level = RiskLevel.LOW
            elif overall_risk < 0.6:
                risk_level = RiskLevel.MEDIUM
            elif overall_risk < 0.8:
                risk_level = RiskLevel.HIGH
            else:
                risk_level = RiskLevel.CRITICAL
            
            # Access decision
            required_actions = []
            access_decision = "allow"
            
            if overall_risk >= 0.6:
                required_actions.append("require_mfa")
            if overall_risk >= 0.7:
                required_actions.append("step_up_auth")
            if overall_risk >= 0.85:
                access_decision = "block"
                required_actions.append("notify_security")
            
            return AdaptiveRiskScore(
                overall_risk_score=overall_risk,
                risk_level=risk_level,
                risk_factors=RiskFactors(
                    device_risk=device_risk,
                    behavior_risk=behavior_risk,
                    network_risk=network_risk,
                    time_risk=time_risk,
                    authentication_risk=auth_risk
                ),
                access_decision=access_decision,
                required_actions=required_actions,
                confidence=0.90
            )
        except Exception as e:
            logger.error(f"Error calculating risk score: {str(e)}")
            return AdaptiveRiskScore(
                overall_risk_score=0.5,
                risk_level=RiskLevel.MEDIUM,
                risk_factors=RiskFactors(
                    device_risk=0.1,
                    behavior_risk=0.1,
                    network_risk=0.1,
                    time_risk=0.1,
                    authentication_risk=0.3
                ),
                access_decision="challenge",
                required_actions=["require_mfa"],
                confidence=0.0
            )
    
    # ==================== Access Decision ====================
    
    @staticmethod
    def make_access_decision(
        user_id: int,
        risk_score: AdaptiveRiskScore,
        db: Session
    ) -> AccessDecision:
        """Make final access control decision"""
        try:
            user = db.query(User).filter(User.id == user_id).first()
            
            if not user:
                return AccessDecision(
                    user_id=user_id,
                    access_granted=False,
                    decision_reason="User not found",
                    required_actions=["notify_security"],
                    risk_score=1.0,
                    risk_level=RiskLevel.CRITICAL,
                    challenges=[],
                    metadata={}
                )
            
            # Check if account is locked
            if user.is_locked:
                return AccessDecision(
                    user_id=user_id,
                    access_granted=False,
                    decision_reason="Account locked due to failed attempts",
                    required_actions=["reset_password"],
                    risk_score=risk_score.overall_risk_score,
                    risk_level=risk_score.risk_level,
                    challenges=[],
                    metadata={"locked_until": (user.last_locked_time + timedelta(minutes=15)).isoformat()}
                )
            
            # Evaluate adaptive risk
            access_granted = risk_score.access_decision == "allow"
            challenges = []
            
            if risk_score.access_decision == "challenge":
                challenges.append("/mfa/verify")
            elif risk_score.access_decision == "block":
                access_granted = False
            
            return AccessDecision(
                user_id=user_id,
                access_granted=access_granted,
                decision_reason=f"Risk level: {risk_score.risk_level.value}",
                required_actions=risk_score.required_actions,
                risk_score=risk_score.overall_risk_score,
                risk_level=risk_score.risk_level,
                challenges=challenges,
                session_duration_minutes=30 if risk_score.risk_level == RiskLevel.CRITICAL else 480,
                metadata={
                    "risk_factors": risk_score.risk_factors.dict(),
                    "confidence": risk_score.confidence
                }
            )
        except Exception as e:
            logger.error(f"Error making access decision: {str(e)}")
            return AccessDecision(
                user_id=user_id,
                access_granted=False,
                decision_reason="Error evaluating access",
                required_actions=[],
                risk_score=0.5,
                risk_level=RiskLevel.MEDIUM,
                challenges=[],
                metadata={"error": str(e)}
            )
    
    # ==================== Monitoring & Updates ====================
    
    @staticmethod
    def update_behavior_profile(
        user_id: int,
        device_id: str,
        location: str,
        db: Session
    ) -> None:
        """Update user behavior profile with new data"""
        try:
            profile = db.query(BehaviorProfile).filter(
                BehaviorProfile.user_id == user_id
            ).first()
            
            if not profile:
                return
            
            data = profile.behavior_data or {}
            
            # Update typical hours
            current_hour = datetime.utcnow().hour
            typical_hours = data.get("typical_hours", [])
            if current_hour not in typical_hours:
                typical_hours.append(current_hour)
            data["typical_hours"] = sorted(list(set(typical_hours)))
            
            # Update typical devices
            typical_devices = data.get("typical_devices", [])
            if device_id not in typical_devices:
                typical_devices.append(device_id)
            data["typical_devices"] = typical_devices
            
            # Update typical locations
            typical_locations = data.get("typical_locations", [])
            if location not in typical_locations:
                typical_locations.append(location)
            data["typical_locations"] = typical_locations
            
            profile.behavior_data = data
            profile.updated_at = datetime.utcnow()
            db.commit()
            
            logger.info(f"Updated behavior profile for user {user_id}")
        except Exception as e:
            db.rollback()
            logger.error(f"Error updating behavior profile: {str(e)}")
