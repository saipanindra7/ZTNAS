# ZTNAS Production Implementation Guide
## Enterprise-Ready Zero Trust Network Access System

**Document Version:** 2.0  
**Created:** 2024-03-28  
**Status:** Implementation Ready  
**Target Audience:** DevOps, Security Engineers, System Administrators

---

## 📋 Quick Start Checklist

- [ ] Install production dependencies
- [ ] Configure secrets management
- [ ] Enable rate limiting
- [ ] Setup structured logging
- [ ] Configure database backups
- [ ] Enable HTTPS/TLS
- [ ] Implement input validation
- [ ] Enable GDPR compliance features
- [ ] Configure email/SMS
- [ ] Setup monitoring & alerting
- [ ] Run security audit
- [ ] Load testing
- [ ] Deploy to production

---

## 1️⃣ Installation & Setup

### 1.1 Install Production Dependencies

```bash
cd backend
pip install -r requirements.txt
pip install -e .  # Install in development mode for local work
```

### 1.2 Environment Configuration

Create `.env.production` with secure credentials:

```bash
# Copy example and fill with real values
cp .env.example .env.production

# Set permissions (Linux/Mac)
chmod 600 .env.production
```

**Never commit `.env` files with real secrets!**

---

## 2️⃣ Production Features Implementation

### 2.1 Rate Limiting

**File:** `utils/rate_limiting.py`

**Integration in main.py:**

```python
from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from slowapi.errors import RateLimitExceeded
from utils.rate_limiting import limiter, rate_limit_exception_handler

app = FastAPI(title="ZTNAS API")

# Add rate limiter
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, rate_limit_exception_handler)

# Apply to routes
from app.routes import auth, mfa

@app.post("/api/v1/auth/login")
@limiter.limit("5/minute")
async def login(...):
    pass

@app.post("/api/v1/auth/register")
@limiter.limit("3/hour")
async def register(...):
    pass

@app.post("/api/v1/mfa/otp/verify")
@limiter.limit("5/minute")
async def verify_otp(...):
    pass
```

**Testing Rate Limits:**

```bash
# Should succeed first 5 times
for i in {1..5}; do curl -X POST http://localhost:8000/api/v1/auth/login; done

# Next requests should fail with 429
curl -X POST http://localhost:8000/api/v1/auth/login
# Response: {"error": "Too many requests", "retry_after": "60 seconds"}
```

### 2.2 Structured Logging with Correlation IDs

**File:** `utils/logging_config.py`

**Integration in main.py:**

```python
from utils.logging_config import setup_structured_logging, ProductionLogger
import logging

# Setup at app startup
logging.basicConfig(level=logging.INFO)
setup_structured_logging()

# Use in routes
logger = ProductionLogger("auth_routes")

@app.post("/api/v1/auth/login")
async def login(request: LoginRequest):
    logger.info(
        "Login attempt",
        extra={
            "username": request.username,
            "ip_address": request.client.host,
        }
    )
    
    try:
        # Login logic
        logger.info("Login successful", extra={"user_id": user.id})
    except Exception as e:
        logger.error("Login failed", exception=e, extra={"username": request.username})
        raise
```

**Log Output (JSON format):**

```json
{
  "timestamp": "2024-03-28T10:15:45.123456Z",
  "level": "INFO",
  "correlation_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
  "logger_name": "auth_routes",
  "message": "Login successful",
  "user_id": "usr_123456"
}
```

### 2.3 Secrets Management

**File:** `utils/secrets_management.py`

**Usage:**

```python
from utils.secrets_management import SecureSettings

# In your config
settings = SecureSettings()

# Automatically loads from AWS Secrets Manager in production
# Falls back to .env in development
database_url = settings.database_url
secret_key = settings.secret_key
smtp_creds = settings.smtp_credentials
```

**AWS Secrets Manager Setup:**

```bash
# Create secrets in AWS
aws secretsmanager create-secret \
  --name ztnas/postgres/connection-url \
  --secret-string "postgresql://user:password@host:5432/ztnas_db"

aws secretsmanager create-secret \
  --name ztnas/secrets/jwt-key \
  --secret-string "your-secret-key-minimum-32-characters"

# Rotate secrets
aws secretsmanager rotate-secret \
  --secret-id ztnas/postgres/connection-url \
  --rotation-rules AutomaticallyAfterDays=30
```

### 2.4 Database Backups

**File:** `utils/database_backup.py`

**Integration:**

```python
from utils.database_backup import DatabaseBackup, BackupHealthCheck

# Initialize backup system
backup_system = DatabaseBackup(
    database_url=settings.database_url,
    backup_dir="./backups",
    s3_bucket="my-company-backups",  # Optional S3 upload
    retention_days=30
)

# Start automatic nightly backups
@app.on_event("startup")
async def startup():
    backup_system.start_automatic_backups(hours=24)

@app.on_event("shutdown")
async def shutdown():
    backup_system.stop_automatic_backups()

# Manual backup endpoint (admin only)
@app.post("/api/v1/admin/backups/create")
@require_admin
async def create_backup():
    backup_file = backup_system.create_backup()
    
    # Verify backup
    health = BackupHealthCheck()
    verification = health.verify_backup(backup_file)
    
    return {
        "backup_file": backup_file,
        "verification": verification,
    }

# List backups
@app.get("/api/v1/admin/backups/list")
@require_admin
async def list_backups():
    return backup_system.get_backup_list()

# Restore backup
@app.post("/api/v1/admin/backups/restore")
@require_admin
async def restore_backup(backup_file: str):
    backup_system.restore_backup(backup_file)
    return {"status": "restored", "file": backup_file}
```

### 2.5 Input Validation & Security

**File:** `utils/input_validation.py`

**Usage:**

```python
from utils.input_validation import SecurityValidator, ValidationError

# Validate email
try:
    email = SecurityValidator.validate_email(request.email)
except ValidationError as e:
    raise HTTPException(status_code=400, detail=str(e))

# Validate password
strength, issues = SecurityValidator.validate_password(request.password)
if strength == PasswordStrength.WEAK:
    return {
        "error": "Password too weak",
        "issues": issues,
    }

# Validate username
try:
    username = SecurityValidator.validate_username(request.username)
except ValidationError as e:
    raise HTTPException(status_code=400, detail=str(e))

# Check SQL injection
try:
    SecurityValidator.prevent_sql_injection(user_input)
except ValidationError:
    # Potential attack logged and blocked
    raise HTTPException(status_code=400, detail="Invalid input")

# Sanitize all input
clean_data = SecurityValidator.sanitize_input(request.dict())
```

### 2.6 GDPR Compliance

**File:** `utils/gdpr_compliance.py`

**Integration:**

```python
from utils.gdpr_compliance import GDPRCompliance, DataExportFormat

@app.get("/api/v1/users/data-export")
@require_authentication
async def export_user_data(user_id: str, format: str = "json", db: Session = Depends()):
    """
    GDPR Right to Data Portability
    Exports user data in portable format
    """
    
    gdpr = GDPRCompliance(db)
    
    try:
        export_format = DataExportFormat(format)
        data_file = gdpr.export_user_data(user_id, export_format)
        
        return {
            "status": "success",
            "format": format,
            "download_url": f"/api/v1/users/download/{user_id}",
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/v1/users/delete-account")
@require_authentication
async def delete_user_account(user_id: str, reason: str = "user_request", db: Session = Depends()):
    """
    GDPR Right to be Forgotten
    Permanently deletes or anonymizes user data
    """
    
    # Verify user is deleting their own account
    if user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Cannot delete other users")
    
    gdpr = GDPRCompliance(db)
    
    # Send confirmation email first
    # ... email logic ...
    
    # 7-day grace period before permanent deletion
    counts = gdpr.delete_user_data(
        user_id=user_id,
        reason="user_requested_deletion",
        anonymize_only=True  # First anonymize, optional 7-day grace
    )
    
    return {
        "status": "deletion_initiated",
        "grace_period_days": 7,
        "grace_period_until": (datetime.utcnow() + timedelta(days=7)).isoformat(),
        "deleted_records": counts,
    }

@app.get("/api/v1/users/{user_id}/deletion-status")
@require_authentication
async def check_deletion_status(user_id: str, db: Session = Depends()):
    """Check if user account is pending deletion"""
    
    gdpr = GDPRCompliance(db)
    status = gdpr.get_deletion_status(user_id)
    
    return status
```

### 2.7 Email Configuration

**File:** `utils/email_service.py` (Create new)

```python
import aiosmtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

class EmailService:
    def __init__(self, smtp_host: str, smtp_port: int, username: str, password: str):
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port
        self.username = username
        self.password = password
    
    async def send_email(
        self,
        to_email: str,
        subject: str,
        body_html: str,
        body_text: str = None
    ):
        """Send email using SMTP"""
        
        message = MIMEMultipart("alternative")
        message["From"] = self.username
        message["To"] = to_email
        message["Subject"] = subject
        
        if body_text:
            message.attach(MIMEText(body_text, "plain"))
        
        message.attach(MIMEText(body_html, "html"))
        
        async with aiosmtplib.SMTP(hostname=self.smtp_host, port=self.smtp_port) as smtp:
            await smtp.login(self.username, self.password)
            await smtp.send_message(message)
```

---

## 3️⃣ Deployment Configuration

### 3.1 Docker Production Setup

**Dockerfile:**

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install PostgreSQL client for backups
RUN apt-get update && apt-get install -y postgresql-client && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Run with gunicorn for production
CMD ["gunicorn", "--workers", "4", "--worker-class", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8000", "main:app"]
```

**docker-compose.yml:**

```yaml
version: '3.8'

services:
  postgres:
    image: postgres:16
    environment:
      POSTGRES_PASSWORD: ${DB_PASSWORD}
      POSTGRES_USER: ${DB_USER}
      POSTGRES_DB: ztnas_db
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${DB_USER}"]
      interval: 10s
      timeout: 5s
      retries: 5

  backend:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      DATABASE_URL: postgresql://${DB_USER}:${DB_PASSWORD}@postgres:5432/ztnas_db
      SECRET_KEY: ${SECRET_KEY}
      ENVIRONMENT: production
    depends_on:
      postgres:
        condition: service_healthy
    volumes:
      - ./backups:/app/backups
    restart: always

  frontend:
    build: ./frontend
    ports:
      - "5500:5500"
    restart: always

volumes:
  postgres_data:
```

### 3.2 HTTPS/TLS Configuration

**Nginx reverse proxy with SSL:**

```nginx
server {
    listen 443 ssl http2;
    server_name ztnas.example.com;

    ssl_certificate /etc/letsencrypt/live/ztnas.example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/ztnas.example.com/privkey.pem;

    # Security headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;

    location /api/ {
        proxy_pass http://backend:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location / {
        proxy_pass http://frontend:5500;
        proxy_set_header Host $host;
    }
}

# Redirect HTTP to HTTPS
server {
    listen 80;
    server_name ztnas.example.com;
    return 301 https://$server_name$request_uri;
}
```

---

## 4️⃣ Monitoring & Alerting

### 4.1 Prometheus Metrics

```python
from prometheus_client import Counter, Histogram, Gauge, generate_latest

# Define metrics
request_count = Counter(
    'ztnas_requests_total',
    'Total requests',
    ['method', 'endpoint', 'status']
)

request_duration = Histogram(
    'ztnas_request_duration_seconds',
    'Request duration',
    ['endpoint']
)

login_attempts = Counter(
    'ztnas_login_attempts_total',
    'Login attempts',
    ['status']
)

# Expose metrics endpoint
@app.get("/metrics")
async def metrics():
    return generate_latest()
```

### 4.2 Alerting Rules

**alert rules.yml:**

```yaml
groups:
  - name: ztnas
    rules:
      - alert: HighErrorRate
        expr: rate(ztnas_requests_total{status="500"}[5m]) > 0.05
        for: 5m
        annotations:
          summary: "High error rate detected"

      - alert: LoginFailureSpike
        expr: rate(ztnas_login_attempts_total{status="failed"}[5m]) > 10
        for: 5m
        annotations:
          summary: "Potential brute force attack"

      - alert: DatabaseConnectionError
        expr: ztnas_db_connection_errors_total > 0
        for: 1m
        annotations:
          summary: "Database connection error"
```

---

## 5️⃣ Security Audit Checklist

**Before Production Deployment:**

- [ ] All environment secrets in Secrets Manager
- [ ] Rate limiting enabled on all auth endpoints
- [ ] HTTPS/TLS configured with valid certificate
- [ ] Input validation on all endpoints
- [ ] SQL injection prevention testing passed
- [ ] XSS prevention testing passed
- [ ] CORS properly configured
- [ ] Authentication token rotation working
- [ ] MFA methods tested  (email, SMS, TOTP, WebAuthn)
- [ ] Backup system tested and verified
- [ ] GDPR compliance features tested
- [ ] Monitoring and alerting configured
- [ ] Database backups tested (restore validated)
- [ ] Security headers configured
- [ ] Rate limiting alerts configured
- [ ] Brute force protection active
- [ ] Account lockout functioning
- [ ] Audit logging working
- [ ] Load testing completed
- [ ] Penetration testing completed

---

## 6️⃣ Maintenance & Operations

### 6.1 Daily Tasks

- [ ] Monitor error logs
- [ ] Check backup completion
- [ ] Verify no rate limit issues
- [ ] Monitor database performance

### 6.2 Weekly Tasks

- [ ] Review security alerts
- [ ] Check authentication logs
- [ ] Verify backup restoration
- [ ] Review user activity

### 6.3 Monthly Tasks

- [ ] Rotate secrets
- [ ] Update dependencies
- [ ] Security audit
- [ ] Performance review
- [ ] Disaster recovery test

---

## 7️⃣ Troubleshooting

### Problem: Rate limiting too strict

**Solution:** Adjust limits in `app/routes/auth.py`:

```python
@router.post("/login")
@limiter.limit("10/minute")  # Increase from 5/minute
def login(...):
    pass
```

### Problem: Backups not running

**Solution:** Check logs and database connectivity:

```bash
docker logs ztnas_backend
# Check database backup scheduler
curl http://localhost:8000/api/v1/admin/backups/list
```

### Problem: High memory usage

**Solution:** Optimize database queries and enable connection pooling:

```python
engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=20,
    max_overflow=0,
    pool_pre_ping=True,
)
```

---

## 📞 Support & Resources

- **Documentation:** `docs/API.md`
- **Issues:** GitHub Issues
- **Security:** security@example.com
- **On-call:** [Your on-call system]

---

**Last Updated:** 2024-03-28  
**Status:** Production Ready  
**Version:** 2.0
