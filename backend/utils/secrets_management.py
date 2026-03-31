# Secrets Management Configuration
# Production-safe handling of credentials using AWS Secrets Manager
# Local development uses .env with warnings

import os
import json
import logging
from typing import Optional, Dict, Any
from functools import lru_cache
import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)

class SecretsManager:
    """
    Unified secrets management interface:
    - AWS Secrets Manager in production
    - Environment variables locally with security warnings
    - Supports secret rotation
    """
    
    def __init__(self, use_aws: bool = False, region: str = "us-east-1"):
        self.use_aws = use_aws and os.getenv("ENVIRONMENT") == "production"
        self.region = region
        self.client = None
        
        if self.use_aws:
            self.client = boto3.client("secretsmanager", region_name=region)
            logger.info("Initialized AWS Secrets Manager for production")
        else:
            logger.warning(
                "Using environment variables for secrets. "
                "This is ONLY acceptable for development. "
                "Use AWS Secrets Manager or similar in production!"
            )
    
    def get_secret(self, secret_name: str, default: Optional[str] = None) -> str:
        """
        Retrieve a secret from Secrets Manager or environment
        
        Args:
            secret_name: Name of the secret (e.g., "ztnas/db/password")
            default: Default value if secret not found
        
        Returns:
            Secret value
        """
        
        if self.use_aws:
            return self._get_aws_secret(secret_name, default)
        else:
            return self._get_env_secret(secret_name, default)
    
    def _get_aws_secret(self, secret_name: str, default: Optional[str] = None) -> str:
        """Retrieve secret from AWS Secrets Manager"""
        
        try:
            response = self.client.get_secret_value(SecretId=secret_name)
            
            if "SecretString" in response:
                secret = response["SecretString"]
                
                # Try to parse as JSON for complex secrets
                try:
                    return json.loads(secret)
                except json.JSONDecodeError:
                    return secret
            
            return response.get("SecretBinary", default)
        
        except ClientError as e:
            logger.error(f"Failed to retrieve secret '{secret_name}': {e}")
            
            if default is not None:
                logger.warning(f"Using default value for secret '{secret_name}'")
                return default
            
            raise ValueError(f"Secret '{secret_name}' not found and no default provided")
    
    def _get_env_secret(self, secret_name: str, default: Optional[str] = None) -> str:
        """
        Retrieve secret from environment variables
        Convert secret_name: ztnas/db/password -> ZTNAS_DB_PASSWORD
        """
        
        env_var = secret_name.upper().replace("/", "_")
        value = os.getenv(env_var, default)
        
        if value is None:
            raise ValueError(f"Secret '{env_var}' not found in environment")
        
        return value
    
    @lru_cache(maxsize=128)
    def get_json_secret(self, secret_name: str) -> Dict[str, Any]:
        """Get a JSON-formatted secret"""
        
        secret_str = self.get_secret(secret_name)
        
        try:
            return json.loads(secret_str)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse secret '{secret_name}' as JSON: {e}")
            raise

class SecureSettings:
    """Settings that are loaded securely from Secrets Manager"""
    
    def __init__(self):
        self.secrets = SecretsManager(
            use_aws=os.getenv("ENVIRONMENT") == "production"
        )
    
    @property
    def database_url(self) -> str:
        """Database connection URL"""
        return self.secrets.get_secret(
            "ztnas/postgres/connection-url",
            os.getenv("DATABASE_URL")
        )
    
    @property
    def secret_key(self) -> str:
        """JWT secret key for token signing"""
        return self.secrets.get_secret(
            "ztnas/secrets/jwt-key",
            os.getenv("SECRET_KEY")
        )
    
    @property
    def smtp_credentials(self) -> Dict[str, str]:
        """Email SMTP credentials"""
        return self.secrets.get_json_secret(
            "ztnas/email/smtp"
        )
    
    @property
    def twilio_credentials(self) -> Dict[str, str]:
        """Twilio SMS credentials"""
        return self.secrets.get_json_secret(
            "ztnas/sms/twilio"
        )
    
    @property
    def aws_credentials(self) -> Dict[str, str]:
        """AWS credentials for S3/SES/etc"""
        return self.secrets.get_json_secret(
            "ztnas/aws/credentials"
        )

# Recommended .env setup for development (COMMIT AN EXAMPLE ONLY):
"""
# .env.example - NEVER commit actual .env with secrets
ENVIRONMENT=development
DATABASE_URL=postgresql://user:password@localhost:5432/ztnas_db
SECRET_KEY=your-secret-key-minimum-32-characters-long
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
TWILIO_ACCOUNT_SID=your_twilio_sid
TWILIO_AUTH_TOKEN=your_twilio_token
TWILIO_FROM_NUMBER=+1234567890
AWS_REGION=us-east-1
LOG_LEVEL=INFO
"""
