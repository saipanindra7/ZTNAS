# ZTNAS Production Integration Quick Start
## How to Integrate Enterprise Features into Your App

**Document Version:** 1.0  
**Target:** Developers integrating production utilities  
**Time Required:** 2-3 hours for full integration  
**Difficulty:** Intermediate

---

## Overview

This guide shows how to integrate the 7 production utility modules into your FastAPI `main.py` to achieve full enterprise readiness.

**7 Modules to Integrate:**
1. ✅ Rate Limiting (slowapi)
2. ✅ Structured Logging (correlation IDs)
3. ✅ Secrets Management (AWS)
4. ✅ Database Backups (automated)
5. ✅ GDPR Compliance (data export/delete)
6. ✅ Input Validation (security)
7. ✅ Monitoring/Metrics (Prometheus)

**Current State:** Utilities created and ready | **Target State:** Integrated and tested

---

## Step 1: Enable Rate Limiting (15 minutes)

### Step 1a: Update main.py

```python
# backend/main.py

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi_limiter import FastAPILimiter
from fastapi_limiter.util import get_remote_address
from redis import asyncio as aioredis
from slowapi import Limiter
from slowapi.util import get_remote_address as get_limiter_address

# Import rate limiting module
from utils.rate_limiting import limiter, RATE_LIMITS

app = FastAPI(
    title="ZTNAS API",
    version="2.0",
    description="Zero Trust Network Access System"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize rate limiter on startup
@app.on_event("startup")
async def startup():
    # Connect to Redis for rate limiting
    redis = aioredis.from_url("redis://localhost:6379")
    await FastAPILimiter.init(redis)
    
    print("✓ Rate limiter initialized")

@app.on_event("shutdown")
async def shutdown():
    pass

app.state.limiter = limiter  # Make limiter available globally
```

### Step 1b: Apply Rate Limits to Routes

```python
# backend/routes/auth.py

from fastapi import APIRouter, Depends
from slowapi import Limiter
from slowapi.util import get_remote_address

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])
limiter = Limiter(key_func=get_remote_address)

# Apply rate limit decorator
@router.post("/login")
@limiter.limit("5/minute")  # 5 attempts per minute per IP
async def login(request: Request, credentials: LoginRequest):
    """
    Login endpoint with rate limiting.
    Limit: 5 requests per minute per IP address
    """
    # ... login logic ...
    pass

@router.post("/register")
@limiter.limit("3/hour")  # 3 registrations per hour per IP
async def register(request: Request, user_data: UserCreate):
    """
    Registration endpoint with rate limiting.
    Limit: 3 requests per hour per IP address
    """
    # ... registration logic ...
    pass

@router.post("/mfa/verify")
@limiter.limit("5/minute")  # 5 MFA attempts per minute
async def verify_mfa(request: Request, mfa_data: MFAVerify):
    """
    MFA verification with rate limiting.
    Limit: 5 attempts per minute per user
    """
    # ... MFA verification logic ...
    pass
```

### Step 1c: Test Rate Limiting

```bash
#!/bin/bash
# test_rate_limiting.sh

echo "Testing login rate limiting (5/minute)..."

for i in {1..10}; do
  echo "Request $i:"
  curl -X POST http://localhost:8000/api/v1/auth/login \
    -H "Content-Type: application/json" \
    -d '{"email":"test@example.com","password":"test"}' \
    -s | jq '.status' || echo "Rate limited"
done

# Expected: Requests 1-5 return 200/401, Requests 6-10 return 429
```

---

## Step 2: Enable Structured Logging (20 minutes)

### Step 2a: Update main.py

```python
# backend/main.py

import structlog
from utils.logging_config import ProductionLogger, setup_structured_logging

# Initialize structured logging
setup_structured_logging(log_level="INFO")

# Create logger
logger = ProductionLogger("main")

@app.on_event("startup")
async def startup():
    # ... existing startup code ...
    
    logger.info("Application starting", extra={
        "version": "2.0",
        "environment": os.getenv("ENVIRONMENT", "development"),
        "database": "connected"
    })

@app.on_event("shutdown")
async def shutdown():
    logger.info("Application shutdown", extra={"timestamp": datetime.utcnow()})
```

### Step 2b: Add Correlation ID Middleware

```python
# backend/middleware/correlation_id.py

import uuid
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from utils.logging_config import CorrelationIdFilter

class CorrelationIdMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Get or generate correlation ID
        correlation_id = request.headers.get("X-Correlation-ID")
        if not correlation_id:
            correlation_id = str(uuid.uuid4())
        
        # Add to request state
        request.state.correlation_id = correlation_id
        
        # Add to response headers
        response = await call_next(request)
        response.headers["X-Correlation-ID"] = correlation_id
        
        return response

# Add to main.py
from middleware.correlation_id import CorrelationIdMiddleware

app.add_middleware(CorrelationIdMiddleware)
```

### Step 2c: Use Logger in Routes

```python
# backend/routes/auth.py

from utils.logging_config import ProductionLogger

logger = ProductionLogger("auth_routes")

@router.post("/login")
async def login(credentials: LoginRequest):
    logger.info("Login attempt", extra={
        "email": credentials.email,
        "timestamp": datetime.utcnow()
    })
    
    try:
        user = await authenticate_user(credentials.email, credentials.password)
        logger.info("Login successful", extra={"user_id": user.id})
        return {"access_token": token}
    except Exception as e:
        logger.error("Login failed", extra={"error": str(e)})
        raise

# All logs now include:
# - timestamp
# - correlation_id (auto-injected)
# - level (info, error, debug)
# - custom fields (email, user_id, error)
```

### Step 2d: Test Logging

```bash
# Start application and check logs
tail -f /var/log/ztnas/application.log | jq '.'

# Expected JSON output:
# {
#   "timestamp": "2024-03-28T10:15:45.123Z",
#   "correlation_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
#   "level": "info",
#   "logger": "auth_routes",
#   "message": "Login attempt",
#   "email": "user@example.com"
# }
```

---

## Step 3: Enable Secrets Management (15 minutes)

### Step 3a: Update main.py

```python
# backend/main.py

from utils.secrets_management import SecretsManager

# Initialize secrets manager
secrets_manager = SecretsManager(
    environment=os.getenv("ENVIRONMENT", "development"),
    aws_region=os.getenv("AWS_REGION", "us-east-1")
)

@app.on_event("startup")
async def startup():
    # Load secrets from AWS Secrets Manager (or environment fallback)
    database_url = secrets_manager.get_secret("database_url")
    jwt_secret = secrets_manager.get_secret("jwt_secret")
    smtp_password = secrets_manager.get_secret("smtp_password")
    
    # Use secrets in application
    engine = create_engine(database_url)
    settings.JWT_SECRET = jwt_secret
    
    logger.info("Secrets loaded successfully")
```

### Step 3b: Configure AWS Secrets Manager

```bash
#!/bin/bash
# setup_secrets.sh

# Create secrets in AWS Secrets Manager
aws secretsmanager create-secret \
  --name ztnas/database_url \
  --secret-string "postgresql://user:password@localhost:5432/ztnas_prod"

aws secretsmanager create-secret \
  --name ztnas/jwt_secret \
  --secret-string "your-super-secret-key-min-32-chars"

aws secretsmanager create-secret \
  --name ztnas/smtp_password \
  --secret-string "your-email-password"

aws secretsmanager create-secret \
  --name ztnas/api_keys \
  --secret-string '{"twilio_key":"xxx","sendgrid_key":"yyy"}'

echo "✓ All secrets configured in AWS"
```

### Step 3c: Test Secrets

```python
# Test script
from utils.secrets_management import SecretsManager

secrets = SecretsManager(environment="production")

# Get single secret
db_url = secrets.get_secret("database_url")
print(f"Database URL loaded: {db_url[:20]}...")  # Don't print full URL

# Get nested secret
api_keys = secrets.get_secret("api_keys")
print(f"Twilio key loaded: {api_keys['twilio_key'][:10]}...")

print("✓ Secrets management working")
```

---

## Step 4: Enable Database Backups (15 minutes)

### Step 4a: Update main.py

```python
# backend/main.py

from utils.database_backup import DatabaseBackup
import asyncio

# Initialize backup system
database_url = os.getenv("DATABASE_URL")
s3_bucket = os.getenv("BACKUP_S3_BUCKET", "ztnas-backups")

backup_system = DatabaseBackup(
    database_url=database_url,
    s3_bucket=s3_bucket,
    retention_days=30
)

@app.on_event("startup")
async def startup():
    # Start automatic backups every night at 3 AM UTC
    # Schedule the backup task
    
    async def backup_scheduler():
        while True:
            # Run backup every 24 hours
            await asyncio.sleep(86400)  # 24 hours
            try:
                backup_system.create_backup()
                logger.info("Automated backup completed")
            except Exception as e:
                logger.error("Backup failed", extra={"error": str(e)})
    
    # Start backup scheduler in background
    asyncio.create_task(backup_scheduler())
    
    # Or use APScheduler for more control
    from apscheduler.schedulers.background import BackgroundScheduler
    from apscheduler.triggers.cron import CronTrigger
    
    scheduler = BackgroundScheduler()
    scheduler.add_job(
        backup_system.create_backup,
        trigger=CronTrigger(hour=3, minute=0),  # 3 AM UTC
        id="nightly_backup"
    )
    scheduler.start()
    
    logger.info("Backup scheduler started")
```

### Step 4b: Manually Create & Restore Backup

```python
# Create backup
from utils.database_backup import DatabaseBackup

backup = DatabaseBackup(
    database_url="postgresql://user:pass@localhost:5432/ztnas_prod",
    s3_bucket="ztnas-backups"
)

# Create backup manually
backup_file = backup.create_backup()
print(f"✓ Backup created: {backup_file}")

# List backups
backups = backup.list_backups()
for b in backups:
    print(f"  - {b['filename']}: {b['size']}")

# Restore from backup
backup.restore_backup(backup_file="/backups/ztnas_db_2024-03-28.sql.gz")
print("✓ Database restored")
```

### Step 4c: Test Backup Integration

```bash
# Monitor backup in logs
tail -f /var/log/ztnas/application.log | grep -i backup

# Manual backup for testing
curl -X POST http://localhost:8000/admin/backup/create \
  -H "Authorization: Bearer $ADMIN_TOKEN"

# List backups
curl http://localhost:8000/admin/backup/list \
  -H "Authorization: Bearer $ADMIN_TOKEN" | jq '.backups'
```

---

## Step 5: Enable GDPR Compliance (15 minutes)

### Step 5a: Create GDPR Endpoints

```python
# backend/routes/gdpr.py

from fastapi import APIRouter, Depends, HTTPException
from utils.gdpr_compliance import GDPRCompliance
from utils.logging_config import ProductionLogger

router = APIRouter(prefix="/api/v1/users", tags=["gdpr"])
logger = ProductionLogger("gdpr_routes")

gdpr_service = GDPRCompliance(db=None)  # Inject DB in StartUp

@router.post("/{user_id}/export")
async def export_user_data(user_id: str, current_user = Depends(get_current_user)):
    """
    GDPR Right to Data Portability.
    User can export all their personal data in JSON/CSV/NDJSON format.
    """
    
    # Verify user is exporting their own data
    if current_user.id != user_id and not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Unauthorized")
    
    logger.info("Data export requested", extra={"user_id": user_id})
    
    try:
        # Export in JSON format
        export_file = gdpr_service.export_user_data(
            user_id=user_id,
            format="json"
        )
        
        logger.info("Data export completed", extra={
            "user_id": user_id,
            "file": export_file
        })
        
        return {
            "status": "success",
            "download_url": f"/download/{export_file}",
            "expires_in_hours": 24
        }
    
    except Exception as e:
        logger.error("Data export failed", extra={"error": str(e)})
        raise HTTPException(status_code=500, detail="Export failed")

@router.post("/{user_id}/delete")
async def request_account_deletion(user_id: str, current_user = Depends(get_current_user)):
    """
    GDPR Right to be Forgotten.
    User requests complete account deletion with 7-day grace period.
    """
    
    if current_user.id != user_id and not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Unauthorized")
    
    logger.info("Account deletion requested", extra={"user_id": user_id})
    
    try:
        deletion_id = gdpr_service.schedule_user_deletion(
            user_id=user_id,
            grace_period_days=7
        )
        
        logger.info("Account deletion scheduled", extra={
            "user_id": user_id,
            "deletion_id": deletion_id,
            "grace_period": 7
        })
        
        # Send confirmation email to user
        # (implement email sending)
        
        return {
            "status": "scheduled",
            "deletion_id": deletion_id,
            "will_delete_at": "2024-04-04T10:30:00Z",
            "can_cancel_until": "2024-04-03T23:59:59Z"
        }
    
    except Exception as e:
        logger.error("Deletion request failed", extra={"error": str(e)})
        raise HTTPException(status_code=500, detail="Deletion request failed")

# Add to main.py
from routes.gdpr import router as gdpr_router
app.include_router(gdpr_router)
```

### Step 5b: Test GDPR Endpoints

```bash
#!/bin/bash
# test_gdpr.sh

USER_ID="user_123"
TOKEN="your_jwt_token"

# Test data export
echo "Testing data export..."
curl -X POST http://localhost:8000/api/v1/users/$USER_ID/export \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json"

# Expected response:
# {
#   "status": "success",
#   "download_url": "/download/export_2024_03_28_123456.json",
#   "expires_in_hours": 24
# }

# Test account deletion request
echo "Testing deletion request..."
curl -X POST http://localhost:8000/api/v1/users/$USER_ID/delete \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json"

# Expected response:
# {
#   "status": "scheduled",
#   "deletion_id": "del_abc123",
#   "will_delete_at": "2024-04-04T10:30:00Z",
#   "can_cancel_until": "2024-04-03T23:59:59Z"
# }
```

---

## Step 6: Enable Input Validation (15 minutes)

### Step 6a: Use Security Validator in Routes

```python
# backend/routes/auth.py

from utils.input_validation import SecurityValidator, StringValidator
from utils.logging_config import ProductionLogger

logger = ProductionLogger("auth_validation")
validator = SecurityValidator()

@router.post("/register")
async def register(user_data: UserCreate):
    """Register with comprehensive input validation"""
    
    # Validate email
    email_errors = validator.validate_email(user_data.email)
    if email_errors:
        logger.warning("Invalid email", extra={"errors": email_errors})
        raise HTTPException(status_code=400, detail=f"Invalid email: {email_errors}")
    
    # Validate username
    username_errors = validator.validate_username(user_data.username)
    if username_errors:
        logger.warning("Invalid username", extra={"errors": username_errors})
        raise HTTPException(status_code=400, detail=f"Invalid username: {username_errors}")
    
    # Validate password strength
    password_errors = validator.validate_password(user_data.password)
    if password_errors:
        logger.warning("Weak password", extra={"errors": password_errors})
        raise HTTPException(status_code=400, detail=f"Password too weak: {password_errors}")
    
    # Sanitize input strings
    name_sanitized = StringValidator.sanitize_string(user_data.name)
    
    # Create user with validated data
    user = await create_user(
        email=user_data.email,
        username=user_data.username,
        password=user_data.password,  # Already hashed by create_user
        name=name_sanitized
    )
    
    logger.info("User registered", extra={"user_id": user.id, "email": user.email})
    
    return {"user_id": user.id, "message": "Registration successful"}

@router.post("/login")
async def login(credentials: LoginRequest):
    """Login with validation"""
    
    # Validate email format
    if not validator.validate_email(credentials.email):
        raise HTTPException(status_code=400, detail="Invalid email format")
    
    # Prevent SQL injection through email field
    email_clean = StringValidator.sanitize_string(credentials.email)
    
    # Authenticate
    user = await authenticate_user(email_clean, credentials.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    return {"access_token": token}
```

### Step 6b: Test Input Validation

```bash
#!/bin/bash
# test_input_validation.sh

echo "=== Testing Input Validation ==="

# Test 1: Invalid email
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email":"not-an-email",
    "password":"Test123!",
    "username":"testuser"
  }'
# Expected: 400 - Invalid email

# Test 2: Weak password
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email":"user@example.com",
    "password":"123456",
    "username":"testuser"
  }'
# Expected: 400 - Password too weak

# Test 3: SQL injection attempt
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email":"admin'\'' OR 1=1--",
    "password":"test"
  }'
# Expected: 400 or 401 (sanitized)

# Test 4: Valid input
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email":"newuser@example.com",
    "password":"SecurePass123!",
    "username":"newuser"
  }'
# Expected: 201 or 200 - Success
```

---

## Step 7: Enable Prometheus Metrics (15 minutes)

### Step 7a: Add Metrics Endpoint

```python
# backend/main.py

from prometheus_client import Counter, Histogram, Gauge
from prometheus_client import generate_latest, REGISTRY, CONTENT_TYPE_LATEST

# Define metrics
request_count = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)

request_duration = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration',
    ['method', 'endpoint']
)

active_connections = Gauge(
    'active_connections',
    'Active WebSocket connections'
)

login_attempts = Counter(
    'auth_login_attempts_total',
    'Total login attempts',
    ['status']
)

rate_limit_triggers = Counter(
    'rate_limit_triggers_total',
    'Rate limit triggers',
    ['endpoint']
)

# Metrics endpoint
@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint"""
    return Response(
        generate_latest(REGISTRY),
        media_type=CONTENT_TYPE_LATEST
    )

# Middleware to track metrics
@app.middleware("http")
async def track_metrics(request: Request, call_next):
    start_time = time.time()
    
    response = await call_next(request)
    
    duration = time.time() - start_time
    
    # Record metrics
    request_count.labels(
        method=request.method,
        endpoint=request.url.path,
        status=response.status_code
    ).inc()
    
    request_duration.labels(
        method=request.method,
        endpoint=request.url.path
    ).observe(duration)
    
    return response
```

### Step 7b: Export Metrics to Prometheus

```yaml
# prometheus.yml

global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'ztnas'
    static_configs:
      - targets: ['localhost:8000']
    metrics_path: '/metrics'
```

### Step 7c: Visualize with Grafana

```bash
# Start Prometheus
prometheus --config.file=prometheus.yml

# Start Grafana
docker run -d -p 3000:3000 grafana/grafana

# Add Prometheus datasource in Grafana UI (http://localhost:3000)
# Dashboard > New > Add panel > Select Prometheus
# Example queries:
## Request rate: rate(http_requests_total[5m])
## Error rate: rate(http_requests_total{status=~"5.."}[5m])
## Response time: histogram_quantile(0.95, http_request_duration_seconds)
```

---

## Complete Integration Checklist

```
RATE LIMITING
☑ Import slowapi in main.py
☑ Initialize limiter on startup
☑ Add decorators to auth routes
☑ Test rate limiting works
☑ Configure limits in production-safe values

STRUCTURED LOGGING
☑ Setup structured logging in main.py
☑ Add correlation ID middleware
☑ Replace print() with logger calls
☑ Verify JSON format in logs
☑ Configure log level for production (INFO)

SECRETS MANAGEMENT
☑ Create secrets in AWS Secrets Manager
☑ Initialize SecretsManager in main.py
☑ Load secrets on startup
☑ Remove hardcoded secrets from code
☑ Test secret rotation

DATABASE BACKUPS
☑ Initialize DatabaseBackup in main.py
☑ Schedule nightly backups with APScheduler
☑ Configure S3 bucket for off-site storage
☑ Test backup creation
☑ Test backup restoration

GDPR COMPLIANCE
☑ Create GDPR routes (export, delete)
☑ Add to main.py router
☑ Test data export endpoint
☑ Test deletion request endpoint
☑ Document GDPR policies

INPUT VALIDATION
☑ Import validators in routes
☑ Add validation to registration endpoint
☑ Add validation to login endpoint
☑ Test SQL injection prevention
☑ Test XSS prevention

PROMETHEUS METRICS
☑ Add metrics to main.py
☑ Create /metrics endpoint
☑ Configure Prometheus scraping
☑ Setup Grafana dashboards
☑ Create alerting rules

TESTING
☑ Unit tests for each module
☑ Integration tests for full flow
☑ Load testing (1000+ concurrent users)
☑ Security audit
☑ Production deployment checklist review
```

---

## Expected Results After Integration

**Status After Full Integration:**

```
✓ Rate limiting active on all auth endpoints
✓ All logs in structured JSON format with correlation IDs
✓ All secrets stored in AWS (no hardcoded values)
✓ Automated nightly database backups to S3
✓ GDPR export/delete endpoints available
✓ All user input validated and sanitized
✓ Prometheus metrics collection active
✓ Grafana dashboards created
✓ Performance baseline established
✓ System ready for production deployment
```

**Example Production Deployment Command:**

```bash
# With all integrations active
docker run -e ENVIRONMENT=production \
  -e DATABASE_URL="$(aws secretsmanager get-secret-value --secret-id ztnas/database_url --query SecretString --output text)" \
  -e JWT_SECRET="$(aws secretsmanager get-secret-value --secret-id ztnas/jwt_secret --query SecretString --output text)" \
  -p 8000:8000 \
  -v /var/log/ztnas:/app/logs \
  ztnas:2.0

# System will:
# 1. Check secrets in AWS
# 2. Initialize rate limiting
# 3. Setup structured logging
# 4. Start backup scheduler
# 5. Expose Prometheus metrics
# 6. Ready for GDPR data requests
```

---

## Next Steps

1. **Complete Integration** - Follow steps 1-7 above
2. **Run Tests** - Execute integration tests for all modules
3. **Load Testing** - Use Apache JMeter to test with 1000+ users
4. **Security Audit** - Review for remaining vulnerabilities
5. **Deploy to Staging** - Test in staging environment first
6. **Production Deployment** - Deploy with monitoring active

---

**ZTNAS Production Integration Quick Start v1.0**  
Questions? See PRODUCTION_IMPLEMENTATION_GUIDE.md or AdminGuide
