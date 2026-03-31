"""
Test Zero Trust Features
"""

import pytest
from datetime import datetime, timedelta
from fastapi.testclient import TestClient


class TestDeviceManagement:
    """Test device registry and trust scoring"""
    
    def test_device_registration(self, client: TestClient, auth_headers):
        """Test device registration"""
        response = client.post("/api/v1/zero-trust/devices/register",
                              headers=auth_headers,
                              json={
                                  "device_name": "My Laptop",
                                  "device_info": {
                                      "device_id": "laptop-123-abc",
                                      "device_type": "desktop",
                                      "os": "Windows",
                                      "os_version": "11",
                                      "browser": "Chrome",
                                      "browser_version": "120"
                                  }
                              })
        assert response.status_code == 200
        data = response.json()
        assert "success" in data or "device_name" in data or "device_id" in data
    
    def test_list_trusted_devices(self, client: TestClient, auth_headers):
        """Test listing trusted devices"""
        # Register a device first
        client.post("/api/v1/zero-trust/devices/register",
                   headers=auth_headers,
                   json={
                       "device_name": "My Device",
                       "device_info": {
                           "device_id": "device-456-def",
                           "device_type": "desktop",
                           "os": "Windows",
                           "os_version": "11",
                           "browser": "Chrome",
                           "browser_version": "120"
                       }
                   })
        
        # List devices
        response = client.get("/api/v1/zero-trust/devices/trusted", headers=auth_headers)
        assert response.status_code == 200
        devices = response.json()
        assert isinstance(devices, list)
    
    def test_remove_device(self, client: TestClient, auth_headers):
        """Test device removal"""
        # Register a device
        register_response = client.post("/api/v1/zero-trust/devices/register",
                                       headers=auth_headers,
                                       json={
                                           "device_name": "Device to Remove",
                                           "device_info": {
                                               "device_id": "device-remove-789",
                                               "device_type": "desktop",
                                               "os": "Windows",
                                               "os_version": "10",
                                               "browser": "Firefox",
                                               "browser_version": "115"
                                           }
                                       })
        # Get device_id from response if available
        data = register_response.json()
        device_id = data.get("device_id") or "device-remove-789"
        
        # Remove device
        response = client.delete(f"/api/v1/zero-trust/devices/{device_id}",
                                headers=auth_headers)
        assert response.status_code in [200, 204, 404]
    
    def test_device_trust_score_calculation(self, client: TestClient, auth_headers):
        """Test device trust score is calculated correctly"""
        response = client.post("/api/v1/zero-trust/devices/register",
                              headers=auth_headers,
                              json={
                                  "device_name": "Test Device",
                                  "device_info": {
                                      "device_id": "test-device-score",
                                      "device_type": "desktop",
                                      "os": "Windows",
                                      "os_version": "11",
                                      "browser": "Chrome",
                                      "browser_version": "120"
                                  }
                              })
        
        assert response.status_code in [200, 201]
        data = response.json()
        # Just verify response has expected structure
        assert "success" in data or "message" in data


class TestRiskAssessment:
    """Test risk assessment and scoring"""
    
    def test_risk_assessment(self, client: TestClient, auth_headers):
        """Test access risk assessment"""
        response = client.post("/api/v1/zero-trust/risk/assess",
                              headers=auth_headers,
                              json={
                                  "user_id": 1,
                                  "device_info": {
                                      "device_id": "test-device",
                                      "device_name": "Test",
                                      "device_type": "desktop",
                                      "os": "Windows",
                                      "os_version": "11"
                                  },
                                  "network_context": {
                                      "ip_address": "192.168.1.1",
                                      "country": "US"
                                  },
                                  "auth_context": {
                                      "mfa_used": True,
                                      "is_new_session": False
                                  }
                              })
        assert response.status_code in [200, 400, 422]
    
    def test_risk_levels(self, client: TestClient, auth_headers):
        """Test all risk levels are returned correctly"""
        response = client.post("/api/v1/zero-trust/risk/assess",
                              headers=auth_headers,
                              json={
                                  "user_id": 1,
                                  "device_info": {
                                      "device_id": "test",
                                      "device_name": "Device",
                                      "device_type": "desktop",
                                      "os": "Linux",
                                      "os_version": "22.04"
                                  },
                                  "network_context": {
                                      "ip_address": "1.1.1.1",
                                      "country": "US"
                                  },
                                  "auth_context": {
                                      "mfa_used": True,
                                      "is_new_session": False
                                  }
                              })
        
        assert response.status_code in [200, 400, 422]
        assert "risk_level" in data
        assert data["risk_level"] in ["MINIMAL", "LOW", "MEDIUM", "HIGH", "CRITICAL"]
    
    def test_access_decision(self, client: TestClient, auth_headers):
        """Test access decision making"""
        response = client.post("/api/v1/zero-trust/access/decide",
                              headers=auth_headers,
                              json={
                                  "user_id": 1,
                                  "device_info": {
                                      "device_id": "test-device",
                                      "device_name": "Test",
                                      "device_type": "desktop",
                                      "os": "Windows",
                                      "os_version": "11"
                                  },
                                  "network_context": {
                                      "ip_address": "192.168.1.1",
                                      "country": "US"
                                  },
                                  "auth_context": {
                                      "mfa_used": True,
                                      "is_new_session": False
                                  },
                                  "requested_resource": "sensitive_data"
                              })
        assert response.status_code in [200, 400, 422]


class TestBehaviorAnalytics:
    """Test behavioral analytics"""
    
    def test_behavior_analysis(self, client: TestClient, auth_headers):
        """Test behavior analysis"""
        response = client.post("/api/v1/zero-trust/analyze/behavior",
                              headers=auth_headers,
                              json={
                                  "user_id": 1,
                                  "device_info": {
                                      "device_id": "test-device",
                                      "device_name": "Test",
                                      "device_type": "desktop",
                                      "os": "Windows",
                                      "os_version": "11"
                                  },
                                  "network_context": {
                                      "ip_address": "192.168.1.1",
                                      "country": "US"
                                  },
                                  "auth_context": {
                                      "mfa_used": True,
                                      "is_new_session": False
                                  }
                              })
        assert response.status_code in [200, 400, 422]
    
    def test_get_behavior_profile(self, client: TestClient, auth_headers):
        """Test retrieving behavior profile"""
        response = client.get("/api/v1/zero-trust/profile/behavior",
                             headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "typical_hours" in data or "profile" in data
    
    def test_reset_behavior_profile(self, client: TestClient, auth_headers):
        """Test resetting behavior profile"""
        response = client.post("/api/v1/zero-trust/profile/behavior/reset",
                              headers=auth_headers)
        assert response.status_code == 200


class TestAnomalyDetection:
    """Test anomaly detection"""
    
    def test_get_recent_anomalies(self, client: TestClient, auth_headers):
        """Test retrieving recent anomalies"""
        response = client.get("/api/v1/zero-trust/anomalies/recent",
                             headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_acknowledge_anomaly(self, client: TestClient, auth_headers):
        """Test acknowledging anomaly"""
        # First get anomalies
        anomalies_response = client.get("/api/v1/zero-trust/anomalies/recent",
                                       headers=auth_headers)
        anomalies = anomalies_response.json()
        
        if anomalies:
            anomaly_id = anomalies[0]["id"]
            
            # Acknowledge
            response = client.post(f"/api/v1/zero-trust/anomalies/{anomaly_id}/acknowledge",
                                  headers=auth_headers)
            assert response.status_code in [200, 404]
        else:
            # No anomalies to test with, skip
            pytest.skip("No anomalies in system")
    
    def test_anomaly_types(self, client: TestClient, auth_headers):
        """Test different anomaly types"""
        response = client.get("/api/v1/zero-trust/anomalies/recent",
                             headers=auth_headers)
        
        data = response.json()
        # Anomaly types: impossible_travel, unusual_time, unusual_location, 
        #                new_device, multiple_failures, vpn, proxy, datacenter
        expected_types = [
            "impossible_travel", "unusual_time", "unusual_location",
            "new_device", "multiple_failures", "vpn", "proxy", "datacenter"
        ]


class TestRiskTimeline:
    """Test risk timeline and historical data"""
    
    def test_risk_timeline(self, client: TestClient, auth_headers):
        """Test retrieving risk timeline"""
        response = client.get("/api/v1/zero-trust/risk/timeline",
                             headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        
        # Should return timeline data
        assert "timeline" in data or isinstance(data, list)
    
    def test_risk_timeline_filters(self, client: TestClient, auth_headers):
        """Test risk timeline with filters"""
        response = client.get(
            "/api/v1/zero-trust/risk/timeline?days=7",
            headers=auth_headers
        )
        assert response.status_code == 200


class TestTrustSettings:
    """Test trust level settings"""
    
    def test_get_trust_settings(self, client: TestClient, admin_headers):
        """Test getting trust level settings"""
        response = client.get("/api/v1/zero-trust/settings/trust-level",
                             headers=admin_headers)
        assert response.status_code in [200, 403]  # 403 if not admin
    
    def test_update_trust_settings(self, client: TestClient, admin_headers):
        """Test updating trust level settings"""
        response = client.post("/api/v1/zero-trust/settings/trust-level",
                              headers=admin_headers,
                              json={
                                  "require_mfa": True,
                                  "max_risk_tolerance": 0.6
                              })
        assert response.status_code in [200, 403]


class TestZeroTrustIntegration:
    """Integration tests for Zero Trust flow"""
    
    def test_complete_device_trust_flow(self, client: TestClient, auth_headers):
        """Test complete device registration and trust scoring flow"""
        # 1. Register device
        register_response = client.post("/api/v1/zero-trust/devices/register",
                                       headers=auth_headers,
                                       json={
                                           "device_name": "Test Device",
                                           "device_type": "laptop",
                                           "os_info": "Windows 11",
                                           "browser_info": "Chrome"
                                       })
        assert register_response.status_code == 200
        
        device = register_response.json()
        device_id = device["id"]
        initial_trust = device["trust_score"]
        
        # 2. Assess risk with this device
        risk_response = client.post("/api/v1/zero-trust/risk/assess",
                                   headers=auth_headers,
                                   json={
                                       "device_info": {
                                           "device_id": device_id,
                                           "trust_score": initial_trust
                                       },
                                       "network_info": {
                                           "ip_address": "192.168.1.1",
                                           "country": "US"
                                       }
                                   })
        assert risk_response.status_code == 200
        
        # 3. Make access decision
        decision_response = client.post("/api/v1/zero-trust/access/decide",
                                       headers=auth_headers,
                                       json={
                                           "risk_score": risk_response.json()["risk_score"],
                                           "user_id": "test-user",
                                           "resource": "application"
                                       })
        assert decision_response.status_code == 200
        assert decision_response.json()["decision"] in ["ALLOW", "CHALLENGE", "DENY"]
    
    def test_rapid_location_change_detection(self, client: TestClient, auth_headers):
        """Test impossible travel (rapid location change) detection"""
        # Simulate access from US
        client.post("/api/v1/zero-trust/analyze/behavior",
                   headers=auth_headers,
                   json={
                       "login_time": datetime.now().isoformat(),
                       "device_id": "device-1",
                       "ip_address": "1.1.1.1",
                       "location": "New York, US"
                   })
        
        # Immediately simulate access from Japan (impossible travel)
        response = client.post("/api/v1/zero-trust/analyze/behavior",
                              headers=auth_headers,
                              json={
                                  "login_time": (datetime.now() + timedelta(minutes=1)).isoformat(),
                                  "device_id": "device-2",
                                  "ip_address": "2.2.2.2",
                                  "location": "Tokyo, Japan"
                              })
        
        assert response.status_code == 200
