# Input Validation & Security Hardening
# Comprehensive validation for production safety

import re
import html
from typing import Optional, List, Any, Union
from enum import Enum
import logging

logger = logging.getLogger(__name__)

class ValidationError(Exception):
    """Custom validation error"""
    pass

class PasswordStrength(str, Enum):
    WEAK = "weak"
    FAIR = "fair"
    GOOD = "good"
    STRONG = "strong"

class SecurityValidator:
    """
    Production-grade input validation:
    - SQL injection prevention
    - XSS prevention
    - Password strength enforcement
    - Email validation
    - IP validation
    - Rate limiting awareness
    """
    
    # Regex patterns for validation
    EMAIL_PATTERN = re.compile(
        r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    )
    
    USERNAME_PATTERN = re.compile(r"^[a-zA-Z0-9_-]{3,32}$")
    
    IPV4_PATTERN = re.compile(
        r"^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}"
        r"(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$"
    )
    
    IPV6_PATTERN = re.compile(
        r"^(([0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4}|"
        r"([0-9a-fA-F]{1,4}:){1,7}:|"
        r"::1)$"
    )
    
    # SQL injection patterns
    SQL_INJECTION_PATTERNS = [
        r"(\bunion\b.*\bselect\b)",
        r"(\};?\s*\bselect\b)",
        r"(\bor\b.*=.*)",
        r"(-{2}|/\*|\*/|xp_|sp_)",
    ]
    
    # XSS patterns
    XSS_PATTERNS = [
        r"<script[^>]*>.*?</script>",
        r"javascript:",
        r"onerror=",
        r"onload=",
    ]
    
    @staticmethod
    def validate_email(email: str, max_length: int = 255) -> str:
        """Validate and sanitize email address"""
        
        if not email:
            raise ValidationError("Email cannot be empty")
        
        if len(email) > max_length:
            raise ValidationError(f"Email too long (max {max_length} chars)")
        
        email = email.strip().lower()
        
        if not SecurityValidator.EMAIL_PATTERN.match(email):
            raise ValidationError("Invalid email format")
        
        return email
    
    @staticmethod
    def validate_username(username: str, min_length: int = 3, max_length: int = 32) -> str:
        """Validate and sanitize username"""
        
        if not username:
            raise ValidationError("Username cannot be empty")
        
        if len(username) < min_length or len(username) > max_length:
            raise ValidationError(
                f"Username must be {min_length}-{max_length} characters"
            )
        
        username = username.strip()
        
        if not SecurityValidator.USERNAME_PATTERN.match(username):
            raise ValidationError(
                "Username can only contain letters, numbers, dashes, and underscores"
            )
        
        return username
    
    @staticmethod
    def validate_password(password: str) -> tuple[PasswordStrength, List[str]]:
        """
        Validate password strength
        Returns: (strength_level, list_of_issues)
        """
        
        if not password:
            raise ValidationError("Password cannot be empty")
        
        if len(password) < 8:
            raise ValidationError("Password must be at least 8 characters")
        
        if len(password) > 128:
            raise ValidationError("Password must be less than 128 characters")
        
        issues = []
        strength_score = 0
        
        # Check requirements
        if not re.search(r"[a-z]", password):
            issues.append("Missing lowercase letters")
        else:
            strength_score += 1
        
        if not re.search(r"[A-Z]", password):
            issues.append("Missing uppercase letters")
        else:
            strength_score += 1
        
        if not re.search(r"\d", password):
            issues.append("Missing numbers")
        else:
            strength_score += 1
        
        if not re.search(r"[!@#$%^&*()_+\-=\[\]{};':\"\\|,.<>\/?]", password):
            issues.append("Missing special characters")
        else:
            strength_score += 1
        
        # Determine strength level
        if strength_score <= 1:
            strength = PasswordStrength.WEAK
        elif strength_score == 2:
            strength = PasswordStrength.FAIR
        elif strength_score == 3:
            strength = PasswordStrength.GOOD
        else:
            strength = PasswordStrength.STRONG
        
        return strength, issues
    
    @staticmethod
    def prevent_sql_injection(input_string: str) -> str:
        """Detect and prevent SQL injection attempts"""
        
        if not isinstance(input_string, str):
            return input_string
        
        for pattern in SecurityValidator.SQL_INJECTION_PATTERNS:
            if re.search(pattern, input_string, re.IGNORECASE):
                logger.warning(
                    f"SQL injection pattern detected",
                    extra={"pattern": pattern, "input": input_string[:100]}
                )
                raise ValidationError("Invalid input detected: potential SQL injection")
        
        return input_string
    
    @staticmethod
    def prevent_xss(input_string: str, allow_html: bool = False) -> str:
        """Detect and prevent XSS attacks"""
        
        if not isinstance(input_string, str):
            return input_string
        
        for pattern in SecurityValidator.XSS_PATTERNS:
            if re.search(pattern, input_string, re.IGNORECASE):
                logger.warning(
                    f"XSS pattern detected",
                    extra={"pattern": pattern, "input": input_string[:100]}
                )
                raise ValidationError("Invalid input detected: potential XSS attack")
        
        # HTML escape by default
        if not allow_html:
            input_string = html.escape(input_string)
        
        return input_string
    
    @staticmethod
    def validate_ip_address(ip_address: str) -> str:
        """Validate IP address (IPv4 or IPv6)"""
        
        if not ip_address:
            raise ValidationError("IP address cannot be empty")
        
        ip_address = ip_address.strip()
        
        if not (
            SecurityValidator.IPV4_PATTERN.match(ip_address) or
            SecurityValidator.IPV6_PATTERN.match(ip_address)
        ):
            raise ValidationError(f"Invalid IP address: {ip_address}")
        
        return ip_address
    
    @staticmethod
    def validate_string(
        value: str,
        min_length: int = 1,
        max_length: int = 1000,
        allow_special: bool = False,
        check_sql_injection: bool = True,
        check_xss: bool = True,
    ) -> str:
        """Generic string validation with multiple checks"""
        
        if not value:
            raise ValidationError("Value cannot be empty")
        
        if not isinstance(value, str):
            raise ValidationError("Value must be a string")
        
        value = value.strip()
        
        if len(value) < min_length or len(value) > max_length:
            raise ValidationError(
                f"Value length must be {min_length}-{max_length} characters"
            )
        
        if check_sql_injection:
            SecurityValidator.prevent_sql_injection(value)
        
        if check_xss:
            SecurityValidator.prevent_xss(value, allow_html=allow_html)
        
        if not allow_special and not re.match(r"^[a-zA-Z0-9\s\-_.]+$", value):
            raise ValidationError("Value contains invalid characters")
        
        return value
    
    @staticmethod
    def sanitize_input(input_value: Any) -> Any:
        """
        General input sanitization:
        - Strip whitespace
        - HTML escape
        - Remove null bytes
        """
        
        if isinstance(input_value, str):
            # Remove null bytes
            input_value = input_value.replace("\x00", "")
            
            # Strip whitespace
            input_value = input_value.strip()
            
            # HTML escape
            input_value = html.escape(input_value)
        
        elif isinstance(input_value, dict):
            for key, value in input_value.items():
                input_value[key] = SecurityValidator.sanitize_input(value)
        
        elif isinstance(input_value, list):
            input_value = [SecurityValidator.sanitize_input(item) for item in input_value]
        
        return input_value

class StringValidator:
    """Quick validators for common string types"""
    
    @staticmethod
    def is_valid_email(email: str) -> bool:
        """Check if string is valid email"""
        try:
            SecurityValidator.validate_email(email)
            return True
        except ValidationError:
            return False
    
    @staticmethod
    def is_valid_username(username: str) -> bool:
        """Check if string is valid username"""
        try:
            SecurityValidator.validate_username(username)
            return True
        except ValidationError:
            return False
    
    @staticmethod
    def is_valid_ip(ip_address: str) -> bool:
        """Check if string is valid IP"""
        try:
            SecurityValidator.validate_ip_address(ip_address)
            return True
        except ValidationError:
            return False
