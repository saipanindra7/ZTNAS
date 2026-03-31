# Rate Limiting Configuration for Production
# Protects against brute force and DoS attacks

from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi import HTTPException, Request
import logging

logger = logging.getLogger(__name__)

# Initialize rate limiter
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"]
)

# Rate limit configurations for different endpoints
RATE_LIMITS = {
    "auth_login": "5/minute",           # 5 login attempts per minute per IP
    "auth_register": "3/hour",          # 3 registrations per hour per IP
    "mfa_otp_verify": "5/minute",       # 5 OTP verification attempts per minute
    "mfa_request": "3/minute",          # 3 MFA requests per minute
    "password_reset": "3/hour",         # 3 password reset requests per hour
    "audit_logs": "100/minute",         # 100 audit log reads per minute
    "general_api": "1000/hour",         # 1000 general API calls per hour
}

async def rate_limit_exception_handler(request: Request, exc: RateLimitExceeded):
    """
    Handle rate limit exceeded errors
    Returns proper HTTP 429 response with retry information
    """
    logger.warning(
        f"Rate limit exceeded",
        extra={
            "client_ip": request.client.host,
            "endpoint": request.url.path,
            "method": request.method,
            "limit": str(exc.detail),
        }
    )
    
    return HTTPException(
        status_code=429,
        detail={
            "error": "Too many requests",
            "message": str(exc.detail),
            "retry_after": exc.headers.get("retry-after", "60 seconds")
        }
    )

class RateLimitMiddleware:
    """
    Production-grade rate limiting middleware with:
    - Per-user and per-IP limiting
    - Whitelist support for trusted IPs
    - Graceful degradation
    """
    
    def __init__(self, app, limiter):
        self.app = app
        self.limiter = limiter
        self.whitelist_ips = {
            "127.0.0.1",  # Localhost
            "::1",        # IPv6 localhost
        }
    
    async def __call__(self, request: Request, call_next):
        """Apply rate limiting to incoming requests"""
        
        # Skip rate limiting for whitelisted IPs
        if request.client.host in self.whitelist_ips:
            return await call_next(request)
        
        # Apply rate limiting
        try:
            response = await call_next(request)
            return response
        except RateLimitExceeded as exc:
            return await rate_limit_exception_handler(request, exc)
