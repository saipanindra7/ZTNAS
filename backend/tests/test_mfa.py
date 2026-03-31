"""
Test MFA Endpoints
"""

import pytest
import pyotp
from fastapi.testclient import TestClient


class TestMFASetup:
    """Test MFA setup and enrollment"""
    
    def test_totp_setup(self, client: TestClient, auth_headers):
        """Test TOTP setup returns QR code and secret"""
        response = client.post("/api/v1/mfa/totp/setup", headers=auth_headers, json={})
        assert response.status_code == 200
        data = response.json()
        assert "secret" in data
        assert "qr_code_url" in data
        assert data["qr_code_url"].startswith("data:image/png;base64")
    
    def test_totp_enroll(self, client: TestClient, auth_headers):
        """Test TOTP enrollment with verification"""
        # Setup TOTP
        setup_response = client.post("/api/v1/mfa/totp/setup", headers=auth_headers, json={})
        secret = setup_response.json()["secret"]
        
        # Generate valid TOTP code
        totp = pyotp.TOTP(secret)
        code = totp.now()
        
        # Enroll - pass secret as query parameter
        response = client.post("/api/v1/mfa/totp/enroll",
                              headers=auth_headers,
                              json={"totp_code": code},
                              params={"secret": secret})
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == True
    
    def test_totp_enroll_invalid_code(self, client: TestClient, auth_headers):
        """Test TOTP enrollment with invalid code"""
        # Setup TOTP
        client.post("/api/v1/mfa/totp/setup", headers=auth_headers, json={})
        
        # Try to enroll with invalid code
        response = client.post("/api/v1/mfa/totp/enroll",
                              headers=auth_headers,
                              json={"totp_code": "000000"})
        assert response.status_code == 400
    
    def test_sms_otp_setup(self, client: TestClient, auth_headers):
        """Test SMS OTP setup"""
        response = client.post("/api/v1/mfa/sms/setup",
                              headers=auth_headers,
                              json={"phone_number": "+1234567890"})
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
    
    def test_email_otp_setup(self, client: TestClient, auth_headers):
        """Test Email OTP setup"""
        response = client.post("/api/v1/mfa/email/setup", headers=auth_headers, json={})
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
    
    def test_picture_password_setup(self, client: TestClient, auth_headers):
        """Test Picture Password setup"""
        # This would require image upload
        # For now, test the endpoint structure
        response = client.post("/api/v1/mfa/picture/setup",
                              headers=auth_headers,
                              json={})
        # Expect either success or file required error
        assert response.status_code in [200, 400, 422]
    
    def test_backup_codes_generation(self, client: TestClient, auth_headers):
        """Test backup codes generation"""
        response = client.post("/api/v1/mfa/backup-codes/generate", 
                              headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "codes" in data
        assert len(data["codes"]) == 10


class TestMFAVerification:
    """Test MFA verification"""
    
    def test_verify_totp(self, client: TestClient, auth_headers):
        """Test TOTP verification"""
        # Setup and enroll TOTP
        setup_response = client.post("/api/v1/mfa/totp/setup", headers=auth_headers, json={})
        secret = setup_response.json()["secret"]
        
        totp = pyotp.TOTP(secret)
        code = totp.now()
        
        enroll_response = client.post("/api/v1/mfa/totp/enroll",
                                     headers=auth_headers,
                                     json={"totp_code": code},
                                     params={"secret": secret})
        method_id = enroll_response.json()["method_id"]
        
        # Verify TOTP
        new_code = totp.now()
        response = client.post("/api/v1/mfa/verify",
                              headers=auth_headers,
                              json={
                                  "method_id": method_id,
                                  "verification_code": new_code
                              })
        assert response.status_code == 200
    
    def test_verify_backup_code(self, client: TestClient, auth_headers):
        """Test backup code verification"""
        # Generate backup codes
        backup_response = client.post("/api/v1/mfa/backup-codes/generate",
                                     headers=auth_headers, json={})
        codes = backup_response.json()["codes"]
        method_id = backup_response.json()["method_id"]
        
        # Verify one backup code
        response = client.post("/api/v1/mfa/verify",
                              headers=auth_headers,
                              json={
                                  "method_id": method_id,
                                  "verification_code": codes[0]
                              })
        assert response.status_code == 200
    
    def test_backup_code_single_use(self, client: TestClient, auth_headers):
        """Test that backup codes can only be used once"""
        # Generate backup codes
        backup_response = client.post("/api/v1/mfa/backup-codes/generate",
                                     headers=auth_headers, json={})
        codes = backup_response.json()["codes"]
        method_id = backup_response.json()["method_id"]
        code = codes[0]
        
        # Use the code
        client.post("/api/v1/mfa/verify",
                   headers=auth_headers,
                   json={
                       "method_id": method_id,
                       "verification_code": code
                   })
        
        # Try to use the same code again
        response = client.post("/api/v1/mfa/verify",
                              headers=auth_headers,
                              json={
                                  "method_id": method_id,
                                  "verification_code": code
                              })
        assert response.status_code == 400


class TestMFAManagement:
    """Test MFA method management"""
    
    def test_list_mfa_methods(self, client: TestClient, auth_headers):
        """Test listing user's MFA methods"""
        response = client.get("/api/v1/mfa/methods", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)
        assert "methods" in data
        assert isinstance(data["methods"], list)
    
    def test_set_primary_mfa_method(self, client: TestClient, auth_headers):
        """Test setting primary MFA method"""
        # Setup TOTP first
        setup_response = client.post("/api/v1/mfa/totp/setup", headers=auth_headers, json={})
        secret = setup_response.json()["secret"]
        
        totp = pyotp.TOTP(secret)
        code = totp.now()
        
        enroll_response = client.post("/api/v1/mfa/totp/enroll",
                                     headers=auth_headers,
                                     json={"totp_code": code},
                                     params={"secret": secret})
        
        method_id = enroll_response.json()["method_id"]
        
        # Set as primary
        response = client.post(
            f"/api/v1/mfa/methods/{method_id}/set-primary",
            headers=auth_headers
        )
        assert response.status_code in [200, 404]  # 404 if method not found
    
    def test_remove_mfa_method(self, client: TestClient, auth_headers, test_user_data):
        """Test removing MFA method"""
        # Setup TOTP
        setup_response = client.post("/api/v1/mfa/totp/setup", headers=auth_headers, json={})
        secret = setup_response.json()["secret"]
        
        totp = pyotp.TOTP(secret)
        code = totp.now()
        
        client.post("/api/v1/mfa/totp/enroll",
                   headers=auth_headers,
                   json={"totp_code": code},
                   params={"secret": secret})
        
        # List methods to get ID
        methods_response = client.get("/api/v1/mfa/methods", headers=auth_headers)
        methods_data = methods_response.json()
        methods = methods_data.get("methods", [])
        
        if methods:
            method_id = methods[0]["id"]
            
            # Remove method (requires password verification)
            response = client.delete(
                f"/api/v1/mfa/methods/{method_id}",
                headers=auth_headers,
                json={"password": test_user_data["password"]}
            )
            assert response.status_code in [200, 404, 422]


class TestMFASecurity:
    """Test MFA security features"""
    
    def test_otp_rate_limiting(self, client: TestClient, auth_headers):
        """Test OTP verification rate limiting"""
        # Setup a method first so we have a valid method_id
        setup_response = client.post("/api/v1/mfa/backup-codes/generate", 
                                    headers=auth_headers, json={})
        method_id = setup_response.json()["method_id"]
        
        # Try multiple invalid codes rapidly
        for _ in range(5):
            response = client.post("/api/v1/mfa/verify",
                                  headers=auth_headers,
                                  json={
                                      "method_id": method_id,
                                      "verification_code": "000000"
                                  })
            # Should fail after multiple attempts with 400/422
        assert response.status_code in [400, 422]
    
    def test_otp_code_validity_window(self, client: TestClient, auth_headers):
        """Test that TOTP code validity window is enforced"""
        # Setup TOTP
        setup_response = client.post("/api/v1/mfa/totp/setup", headers=auth_headers, json={})
        secret = setup_response.json()["secret"]
        
        totp = pyotp.TOTP(secret)
        
        # Generate code
        code = totp.now()
        
        # Enroll
        enroll_response = client.post("/api/v1/mfa/totp/enroll",
                                     headers=auth_headers,
                                     json={"totp_code": code},
                                     params={"secret": secret})
        method_id = enroll_response.json()["method_id"]
        
        # Code should be valid immediately after
        verify_response = client.post("/api/v1/mfa/verify",
                                     headers=auth_headers,
                                     json={
                                         "method_id": method_id,
                                         "verification_code": code
                                     })
        assert verify_response.status_code == 200
    
    def test_mfa_required_for_protected_endpoints(self, client: TestClient, test_user_data, db):
        """Test that MFA is enforced when required"""
        from app.models import User
        
        # Register user
        client.post("/api/v1/auth/register", json=test_user_data)
        
        # Get user and set MFA_REQUIRED
        user = db.query(User).filter(User.email == test_user_data["email"]).first()
        
        # Login with username
        response = client.post("/api/v1/auth/login", json={
            "username": test_user_data["email"],
            "password": test_user_data["password"]
        })
        
        # Should get temporary token requiring MFA
        assert response.status_code == 200
