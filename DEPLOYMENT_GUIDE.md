# ZTNAS Phase 6: Testing & Deployment Guide

## Overview
Phase 6 focuses on comprehensive testing, security validation, and production deployment of the ZTNAS system.

## Table of Contents
1. [Unit Testing](#unit-testing)
2. [Integration Testing](#integration-testing)
3. [Performance Testing](#performance-testing)
4. [Security Testing](#security-testing)
5. [Docker Deployment](#docker-deployment)
6. [Production Checklist](#production-checklist)

---

## Unit Testing

### Setup

1. **Install development dependencies:**
```bash
cd backend
pip install -r requirements-dev.txt
```

2. **Run all unit tests:**
```bash
pytest -v
```

3. **Run specific test module:**
```bash
pytest tests/test_auth.py -v
```

4. **Run with coverage report:**
```bash
pytest --cov=app --cov-report=html
```

### Test Modules

#### Authentication Tests (`test_auth.py`)
- User registration validation
- Password hash verification
- Login success/failure scenarios
- Account lockout mechanism
- Password change flow
- Token refresh
- Logout functionality
- Audit logging

**Run:** `pytest tests/test_auth.py`

#### MFA Tests (`test_mfa.py`)
- TOTP setup and verification
- SMS/Email OTP setup
- Picture password registration
- Backup code generation
- MFA method management
- Rate limiting
- Code validity windows
- Single-use code enforcement

**Run:** `pytest tests/test_mfa.py`

#### Zero Trust Tests (`test_zero_trust.py`)
- Device registration
- Trust score calculation
- Risk assessment
- Behavior analysis
- Anomaly detection
- Access decisions
- Risk timeline
- Settings management

**Run:** `pytest tests/test_zero_trust.py`

### Continuous Integration

Create `.github/workflows/tests.yml`:
```yaml
name: Run Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    services:
      postgres:
        image: postgres:18
        env:
          POSTGRES_PASSWORD: postgres
    
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.14'
      
      - name: Install dependencies
        run: |
          pip install -r backend/requirements-dev.txt
      
      - name: Run tests
        run: |
          cd backend
          pytest --cov=app --cov-report=xml
      
      - name: Upload coverage
        uses: codecov/codecov-action@v3
```

---

## Integration Testing

### Database Integration

```python
# Test database operations
def test_user_persistence(db_session):
    """Test data persists correctly"""
    from app.models import User
    
    user = User(email="test@example.com", username="testuser")
    db_session.add(user)
    db_session.commit()
    
    retrieved = db_session.query(User).filter_by(email="test@example.com").first()
    assert retrieved is not None
    assert retrieved.username == "testuser"
```

### API Integration

```bash
# Test API endpoints end-to-end
pytest tests/test_* -m integration --tb=short

# With real database
export DATABASE_URL=postgresql://postgres:password@localhost/test_ztnas_db
pytest -v
```

### Authentication Flow

```bash
# Test complete login flow
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "username": "testuser",
    "password": "TestPass@123"
  }'

# Login
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "TestPass@123"
  }'
```

---

## Performance Testing

### Load Testing with Locust

1. **Create `backend/locustfile.py`:**
```python
from locust import HttpUser, task, between
import json

class UserBehavior(HttpUser):
    wait_time = between(1, 3)
    
    def on_start(self):
        self.token = self.login()
    
    def login(self):
        response = self.client.post("/api/v1/auth/login", json={
            "email": "test@example.com",
            "password": "TestPass@123"
        })
        if response.status_code == 200:
            return response.json()["access_token"]
        return None
    
    @task(1)
    def get_current_user(self):
        self.client.get("/api/v1/auth/me", 
                       headers={"Authorization": f"Bearer {self.token}"})
    
    @task(1)
    def get_devices(self):
        self.client.get("/api/v1/zero-trust/devices/trusted",
                       headers={"Authorization": f"Bearer {self.token}"})
    
    @task(1)
    def get_anomalies(self):
        self.client.get("/api/v1/zero-trust/anomalies/recent",
                       headers={"Authorization": f"Bearer {self.token}"})
```

2. **Run load test:**
```bash
locust -f backend/locustfile.py -H http://localhost:8000 --users 100 --spawn-rate 10
```

### Performance Benchmarks

- **Target response time:** <200ms (95th percentile)
- **Database queries:** <100ms average
- **MFA verification:** <500ms
- **Dashboard load:** <2s
- **Concurrent users:** 1000+

---

## Security Testing

### OWASP Top 10 Validation

#### 1. SQL Injection
```bash
# Test parameterized queries
curl "http://localhost:8000/api/v1/auth/login" \
  -d "email=test@example.com' OR '1'='1';--&password=anything"
# Should NOT authenticate
```

#### 2. Authentication Issues
```bash
# Test without token
curl http://localhost:8000/api/v1/auth/me
# Should return 401

# Test with invalid token
curl http://localhost:8000/api/v1/auth/me \
  -H "Authorization: Bearer invalid"
# Should return 401
```

#### 3. Cross-Site Scripting (XSS)
```bash
# Test user input sanitization
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "username": "<script>alert(1)</script>",
    "password": "TestPass@123"
  }'
# Username should be sanitized
```

#### 4. CSRF Protection
- Verify CSRF tokens in state-changing requests
- Check SameSite cookie attributes

#### 5. Broken Object Level Authorization
```bash
# Test BOLA vulnerability
# Try accessing other user's data
curl http://localhost:8000/api/v1/mfa/methods/999 \
  -H "Authorization: Bearer user1_token"
# Should return 403, not reveal other user data
```

### Password Security

```bash
# Verify bcrypt usage
pytest tests/test_auth.py::TestPasswordSecurity -v

# Check password strength requirements
- Minimum 8 characters
- At least one uppercase letter
- At least one lowercase letter
- At least one number
- At least one special character
```

### Rate Limiting

```bash
# Test rate limiting on login endpoint
for i in {1..10}; do
  curl -X POST http://localhost:8000/api/v1/auth/login \
    -H "Content-Type: application/json" \
    -d '{"email":"test@example.com","password":"wrong"}'
done
# Should return 429 after threshold
```

### Dependency Vulnerability Scanning

```bash
# Check for known vulnerabilities
pip install safety
safety check -r backend/requirements.txt

# Alternative with pip-audit
pip install pip-audit
pip-audit -r backend/requirements.txt
```

---

## Docker Deployment

### Build and Deploy

1. **Build Docker images:**
```bash
docker-compose build
```

2. **Start services:**
```bash
docker-compose up -d
```

3. **Verify containers running:**
```bash
docker-compose ps
```

4. **View logs:**
```bash
docker-compose logs -f backend
docker-compose logs -f postgres
docker-compose logs -f frontend
```

### Environment Configuration

Create `.env` file in project root:
```env
# Database
DB_PASSWORD=YourSecurePassword123!

# Security
SECRET_KEY=your-very-long-secure-key-at-least-32-chars-for-production

# Environment
ENVIRONMENT=production
DEBUG=False

# CORS
CORS_ORIGINS=https://yourdomain.com

# SMTP (for email OTP)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
```

### Health Checks

```bash
# Check backend health
curl http://localhost:8000/health

# Check database connection
docker-compose exec backend python -c "from config.database import engine; engine.connect()"

# Check API documentation
curl http://localhost:8000/docs
```

### Data Backup

```bash
# Backup PostgreSQL database
docker-compose exec postgres pg_dump -U postgres ztnas_db > backup.sql

# Restore from backup
docker-compose exec -T postgres psql -U postgres ztnas_db < backup.sql
```

---

## Production Checklist

### Security
- [ ] Set `DEBUG=False` in production
- [ ] Use strong `SECRET_KEY` (minimum 64 characters)
- [ ] Configure HTTPS/TLS certificates
- [ ] Enable CORS only for trusted origins
- [ ] Set secure cookie flags (Secure, HttpOnly, SameSite)
- [ ] Implement rate limiting
- [ ] Enable password reset mechanism
- [ ] Configure JWT token expiration
- [ ] Enable audit logging
- [ ] Set up intrusion detection

### Performance
- [ ] Enable database query caching
- [ ] Configure CDN for static assets
- [ ] Set up database indexes
- [ ] Enable compression (gzip)
- [ ] Configure connection pooling
- [ ] Set up load balancing
- [ ] Monitor response times
- [ ] Configure auto-scaling

### Reliability
- [ ] Set up database backups (daily)
- [ ] Configure automated failover
- [ ] Set up monitoring and alerting
- [ ] Implement health checks
- [ ] Configure log rotation
- [ ] Set up disaster recovery plan
- [ ] Document runbooks
- [ ] Configure uptime monitoring

### Compliance
- [ ] Implement audit logging (DONE)
- [ ] Set up data retention policies
- [ ] Document security policies
- [ ] Conduct security audit
- [ ] Obtain necessary certifications
- [ ] Document API contracts
- [ ] Set up incident response process
- [ ] Document compliance requirements

### Operations
- [ ] Set up monitoring dashboard
- [ ] Configure alerting
- [ ] Document deployment process
- [ ] Create rollback procedures
- [ ] Set up CI/CD pipeline
- [ ] Document API endpoints
- [ ] Create user documentation
- [ ] Set up support system

### Testing Coverage

**Target Coverage:** 80%+ code coverage

```bash
# Generate coverage report
pytest --cov=app --cov-report=html
# View report: htmlcov/index.html

# Target by module:
# - app/routes: 90%+
# - app/services: 85%+
# - app/models: 75%+
```

---

## Deployment Steps

### Step 1: Pre-Deployment
```bash
# Run all tests
pytest --cov=app

# Run security checks
bandit -r app/

# Check code quality
pylint app/

# Verify Docker build
docker-compose build
```

### Step 2: Staging Deployment
```bash
# Deploy to staging
docker-compose up -d

# Run smoke tests
pytest tests/ -m integration

# Load test
locust -f locustfile.py -u 100
```

### Step 3: Production Deployment
```bash
# Update .env with production values
nano .env

# Pull latest code
git pull origin main

# Build production image
docker-compose build --no-cache

# Stop current containers
docker-compose down

# Start new containers
docker-compose up -d

# Verify health
curl https://yourdomain.com/health
```

### Step 4: Post-Deployment
```bash
# Verify all services running
docker-compose ps

# Check logs for errors
docker-compose logs

# Run health checks
pytest tests/test_health.py -v

# Monitor performance
# Check monitoring dashboard
```

---

## Troubleshooting

### Database Connection Issues
```bash
# Check if postgres container is running
docker ps | grep postgres

# Check database logs
docker-compose logs postgres

# Test connection
docker-compose exec postgres psql -U postgres -c "SELECT version();"
```

### Backend Not Starting
```bash
# View detailed logs
docker-compose logs backend

# Rebuild and restart
docker-compose build --no-cache backend
docker-compose up backend
```

### Frontend Not Loading
```bash
# Check nginx logs
docker-compose logs frontend

# Test frontend container
docker-compose exec frontend curl localhost

# Verify static files
docker-compose exec frontend ls -la /usr/share/nginx/html
```

---

## Rollback Procedure

If deployment fails:

```bash
# 1. Stop current containers
docker-compose down

# 2. Restore database from backup
docker-compose up -d postgres
docker-compose exec -T postgres psql -U postgres ztnas_db < backup.sql

# 3. Checkout previous version
git checkout HEAD~1

# 4. Rebuild and start
docker-compose up -d

# 5. Verify
curl http://localhost:8000/health
```

---

## Monitoring & Maintenance

### Key Metrics to Monitor
- API response times (target: <200ms)
- Error rate (target: <0.1%)
- Database query time (target: <100ms)
- CPU usage (target: <70%)
- Memory usage (target: <80%)
- Disk space (alert at 80%)
- Active sessions
- Failed login attempts

### Daily Tasks
- Monitor error logs
- Check backup completion
- Verify all services running
- Check disk space

### Weekly Tasks
- Review performance metrics
- Check security logs
- Review failed logins
- Verify backups

### Monthly Tasks
- Security audit
- Performance review
- Dependency updates
- Documentation review

---

## Support & Escalation

**For issues:**
1. Check logs: `docker-compose logs [service]`
2. Verify service health: `curl http://localhost:8000/health`
3. Review recent changes and git history
4. Consult runbooks and documentation
5. Contact team lead if issue persists

---

**Last Updated:** March 26, 2026
**Version:** 1.0.0
**Status:** Production Ready
