# ZTNAS - Production Deployment Guide for College Management System

## Overview

This guide explains how to deploy ZTNAS (Zero Trust Network Access System) as a production-ready college management system with proper security, reliability, and scalability.

## Current Status

✅ **System is Production-Ready**
- All critical errors fixed
- All functionalities verified working
- Security components (ZTNA, audit logging, policies) fully implemented
- Role-based access control (HOD, Faculty, Student, Admin) implemented
- Comprehensive error handling and logging in place

## Problem Solved: Directory Listing Issue

### The Issue
When accessing `localhost:5500`, Python's basic HTTP server showed a directory listing instead of serving the application.

### The Solution
Created a production-grade frontend server (`serve.py`) that:
- ✓ Automatically serves `index.html` as the default page
- ✓ Prevents directory listing (security)
- ✓ Adds security headers (X-Frame-Options, CSP, etc.)
- ✓ Supports CORS for backend API calls
- ✓ Implements gzip compression
- ✓ Provides proper logging
- ✓ Handles SPA routing correctly
- ✓ Prevents directory traversal attacks

## Deployment Options

### Option 1: Local Development (Windows)

#### Quick Start
```batch
cd d:\projects\ztnas\frontend
start-server.bat
```

Then open: **http://localhost:5500**

**Features:**
- Production-ready server
- Automatic index.html serving
- Security headers enabled
- CORS support for backend

---

### Option 2: Local Development (Linux/Mac)

```bash
cd frontend
bash ../scripts/step2b_start_frontend.sh
```

Or directly:
```bash
cd frontend
python serve.py
```

Then open: **http://localhost:5500**

---

### Option 3: Docker Production Deployment

#### Prerequisites
- Docker installed
- Docker Compose installed

#### Deploy Backend Only (Development)
```bash
docker-compose up -d postgres backend
```

Backend health check:
```bash
curl http://localhost:8000/health
```

#### Deploy Full Stack (Production)
```bash
docker-compose -f docker-compose.prod.yml up -d
```

**Architecture:**
```
┌─────────────────────────────────────────┐
│  Nginx Reverse Proxy (Port 443/SSL)     │
│  - Terminates TLS                       │
│  - Rate limiting                        │
│  - Security headers                     │
└──────────────┬──────────────────────────┘
               │
        ┌──────┴──────┐
        │             │
   ┌────▼─────┐  ┌────▼──────┐
   │ Frontend  │  │  Backend   │
   │(Port 80)  │  │(Port 8000) │
   └───┬───────┘  └────┬───────┘
       │               │
       └───────┬───────┘
               │
          ┌────▼──────┐
          │ PostgreSQL │
          │ (Port 5432)│
          └───────────┘
```

#### Deploy to College Infrastructure
```bash
# 1. Build production images
docker build -t ztnas-backend:1.0 -f backend/Dockerfile .
docker build -t ztnas-frontend:1.0 -f frontend/Dockerfile .

# 2. Push to registry (if using Kubernetes/Swarm)
docker tag ztnas-backend:1.0 registry.college.edu/ztnas-backend:1.0
docker push registry.college.edu/ztnas-backend:1.0

# 3. Deploy with Compose
docker-compose -f docker-compose.prod.yml up -d
```

---

### Option 4: Direct Server Deployment (Nginx)

#### Installation & Configuration

**1. Install Nginx**
```bash
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install nginx

# CentOS/RHEL
sudo yum install nginx
```

**2. Copy Configuration**
```bash
sudo cp nginx.conf /etc/nginx/nginx.conf
sudo mkdir -p /usr/share/nginx/html
sudo cp -r frontend/static/* /usr/share/nginx/html/
```

**3. Configure SSL Certificates**
```bash
# Copy your certificates
sudo cp /path/to/cert.crt /etc/ssl/certs/ztnas.crt
sudo cp /path/to/key.key /etc/ssl/private/ztnas.key

# Or generate self-signed (for testing only)
sudo openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout /etc/ssl/private/ztnas.key \
  -out /etc/ssl/certs/ztnas.crt
```

**4. Update Nginx Configuration**
Edit `/etc/nginx/nginx.conf`:
- Set `server_name` to your domain (e.g., `ztnas.college.edu`)
- Update certificate paths if needed
- Adjust upstream backend address

**5. Start Nginx**
```bash
sudo nginx -t  # Test configuration
sudo systemctl start nginx
sudo systemctl enable nginx  # Auto-start on boot
```

**6. Verify**
```bash
curl https://ztnas.college.edu  # Should serve index.html
```

---

## College System Integration

### Architecture for College Management

```
College Infrastructure
├── ZTNAS System (Deployed)
│   ├── Authentication Gateway
│   │   ├── SSO Integration (LDAP/Active Directory)
│   │   ├── MFA (6 methods available)
│   │   └── Device Trust Verification
│   │
│   ├── Dashboard (Role-Based)
│   │   ├── HOD Dashboard → Department policies, faculty access
│   │   ├── Faculty Dashboard → Device management, audit logs
│   │   ├── Student Dashboard → Device registration, policies
│   │   └── Admin Dashboard → Full system management
│   │
│   ├── Zero Trust Policies
│   │   ├── Risk Assessment (Behavioral, Device, Network)
│   │   ├── Adaptive Access Control
│   │   ├── Continuous Monitoring
│   │   └── Anomaly Detection
│   │
│   ├── Audit & Compliance
│   │   ├── Action Logging (Every API call)
│   │   ├── Policy Enforcement Logs
│   │   ├── Access Attempts (Success/Failure)
│   │   └── Device Trust Timeline
│   │
│   └── Integration Points
│       ├── LMS (Moodle, Canvas) via API
│       ├── Email System (Notifications)
│       ├── SIEM (Splunk/ELK) for log forwarding
│       └── Endpoint Management (Intune, Workspace ONE)
│
├── Existing College Systems
│   ├── Student Information System (SIS)
│   ├── Learning Management System (LMS)
│   ├── Email & Communication
│   ├── Network Infrastructure
│   └── IT Help Desk
```

### User Provisioning

#### Step 1: Import Student Accounts
```bash
python scripts/import_users.py \
  --source sis_export.csv \
  --role student \
  --department all \
  --send-invitation
```

#### Step 2: Bulk Create HOD Accounts
```bash
python scripts/create_hod_accounts.py \
  --departments CS,IT,Engineering
```

#### Step 3: Assign Policies
```bash
python scripts/assign_policies.py \
  --role faculty \
  --policy default_faculty_policy \
  --mfa_required true
```

#### Step 4: Configure College Policies
Update `/backend/config/policies.json`:
```json
{
  "college_policy": {
    "risk_thresholds": {
      "low": 0.3,
      "medium": 0.6,
      "high": 0.8
    },
    "device_trust_requirements": {
      "student": "medium",
      "faculty": "high",
      "admin": "critical"
    },
    "mfa_enforcement": {
      "admin": "required",
      "faculty": "recommended",
      "student": "optional"
    },
    "session_timeout": {
      "supervised_lab": 480,
      "library": 120,
      "off_campus": 60
    }
  }
}
```

---

## Security Features for Production

### 1. Authentication & Access Control
- ✓ JWT tokens with 24-hour expiration
- ✓ Argon2 + PBKDF2 password hashing
- ✓ 5-attempt account lockout
- ✓ MFA support (Email, SMS, TOTP, Backup codes, Picture password, Biometric)
- ✓ Session management

### 2. Zero Trust Security
- ✓ Continuous device verification
- ✓ Behavior-based risk scoring
- ✓ Real-time policy enforcement
- ✓ Anomaly detection
- ✓ Device trust tracking

### 3. Network Security
- ✓ TLS 1.2+ encryption
- ✓ CORS restrictions
- ✓ Rate limiting (login: 5/min, API: 100/min)
- ✓ SQL injection prevention via ORM
- ✓ CSRF token validation

### 4. Monitoring & Audit
- ✓ Comprehensive audit logs
- ✓ API call tracking
- ✓ Failed login tracking
- ✓ Policy violation alerts
- ✓ Real-time dashboards

---

## Performance Tuning

### Backend (FastAPI)
```python
# In main.py - Production settings
app.add_middleware(
    GZipMiddleware,
    minimum_size=1000
)

# Database connection pooling
SQLALCHEMY_POOL_SIZE = 20
SQLALCHEMY_MAX_OVERFLOW = 40
```

### Database (PostgreSQL)
```sql
-- Connection pooling with PgBouncer
-- In postgresql.conf
max_connections = 200
shared_buffers = 256MB
effective_cache_size = 1GB
work_mem = 16MB
maintenance_work_mem = 64MB

-- Create indexes
CREATE INDEX idx_audit_logs_timestamp ON audit_logs(timestamp DESC);
CREATE INDEX idx_devices_user_id ON devices(user_id);
CREATE INDEX idx_policies_role ON policies(role);
```

### Frontend
- ✓ Gzip compression enabled
- ✓ Static asset caching (1-hour TTL)
- ✓ Lazy loading for charts
- ✓ Minified JavaScript/CSS

---

## Monitoring & Operations

### Health Checks
```bash
# Backend health
curl http://backend:8000/health

# Database connectivity
curl http://backend:8000/health/db

# Frontend availability
curl http://frontend:5500/

# Full system check
curl https://ztnas.college.edu/api/v1/health
```

### Log Files
```
Backend:  /logs/backend.log
Frontend: /logs/frontend.log
Nginx:    /var/log/nginx/access.log, /var/log/nginx/error.log
Database: /var/log/postgresql/postgresql.log
```

### Metrics (Prometheus)
```bash
# Access metrics endpoint
curl http://backend:8000/metrics

# Key metrics to monitor
- http_requests_total
- login_attempts_total
- device_trust_score (avg)
- policy_violations_total
- database_query_duration
```

---

## Troubleshooting

### Issue: Directory Listing on localhost:5500
**Solution:** Use the new `serve.py` script
```bash
cd frontend && python serve.py
```

### Issue: 401 Unauthorized on Dashboard
**Solution:** Login first, JWT token is required
```bash
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin123"}'
```

### Issue: CORS Errors
**Solution:** Check `.env` file CORS_ORIGINS setting
```bash
CORS_ORIGINS=["http://localhost:5500", "https://ztnas.college.edu"]
```

### Issue: 404 on API Endpoints
**Solution:** Check backend is running
```bash
ps aux | grep "uvicorn\|python"
curl http://localhost:8000/health
```

---

## Backup & Recovery

### Database Backup
```bash
# Daily backup
pg_dump -U ztnas_user -h localhost ztnas_db > /backups/ztnas_$(date +%Y%m%d).sql

# Or with Docker
docker exec ztnas-postgres pg_dump -U ztnas_user ztnas_db > backup.sql
```

### Automated Backups with Cron
```bash
# Edit crontab
crontab -e

# Add:
0 2 * * * pg_dump -U ztnas_user -h localhost ztnas_db > /backups/ztnas_$(date +\%Y\%m\%d).sql

# Cleanup old backups
0 3 * * * find /backups -name "ztnas_*.sql" -mtime +30 -delete
```

### Recovery
```bash
psql -U ztnas_user -h localhost ztnas_db < /backups/ztnas_20260328.sql
```

---

## Next Steps for Production Deployment

1. **Week 1: Setup**
   - [ ] Provision production servers
   - [ ] Configure SSL certificates
   - [ ] Setup PostgreSQL with backups
   - [ ] Configure Nginx reverse proxy

2. **Week 2: Deployment**
   - [ ] Deploy backend using Docker or direct install
   - [ ] Deploy frontend (Nginx or Docker)
   - [ ] Configure database connection
   - [ ] Run smoke tests

3. **Week 3: Integration**
   - [ ] Import student data from SIS
   - [ ] Create HOD accounts
   - [ ] Configure college policies
   - [ ] Setup SSO integration

4. **Week 4: Monitoring**
   - [ ] Setup log aggregation (ELK/Splunk)
   - [ ] Configure Prometheus metrics
   - [ ] Create monitoring dashboards
   - [ ] Setup alerts for critical events

5. **Week 5: Training & Go-Live**
   - [ ] Train IT staff on administration
   - [ ] Train HODs on dashboard
   - [ ] Communication to users
   - [ ] Go-live and monitoring

---

## Support & Documentation

- **Admin Documentation:** See `ADMIN_QUICK_START.md`
- **API Documentation:** Swagger UI at `http://backend:8000/docs`
- **Architecture Overview:** See `PROJECT_ANALYSIS_OVERVIEW.md`

---

**Status:** ✅ PRODUCTION READY

The ZTNAS system is fully tested and ready for college deployment. Follow this guide for a secure, reliable implementation.

