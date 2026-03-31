# ZTNAS Production Deployment Readiness Checklist
## Enterprise Deployment Pre-Flight Verification

**Document Version:** 2.0  
**Created:** 2024-03-28  
**Status:** Ready for Production Use  
**Org Types:** Enterprise | Higher Education | Healthcare | Government

---

## ✅ Pre-Deployment Verification

### Level 1: Critical Infrastructure (MUST PASS)

- [ ] **Database Connectivity**
  - [ ] PostgreSQL 16+ running and accessible
  - [ ] Database credentials configured in `.env`
  - [ ] Connection pooling tested (10+ concurrent connections)
  - [ ] Backup and recovery tested

```bash
# Test database connectivity
python -c "from sqlalchemy import create_engine; engine = create_engine(os.getenv('DATABASE_URL')); conn = engine.connect(); print('✓ DB connected')"
```

- [ ] **Backend API Running**
  - [ ] FastAPI server starts without errors
  - [ ] All routes accessible: `curl http://localhost:8000/api/v1/health`
  - [ ] WebSocket connections work
  - [ ] CORS policies configured correctly

```bash
# Terminal 1: Start backend
cd backend
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload

# Terminal 2: Test health
curl http://localhost:8000/api/v1/health
# Expected: {"status":"healthy","timestamp":"..."}
```

- [ ] **Frontend Server Running**
  - [ ] HTTP server running on port 5500
  - [ ] Static files loading
  - [ ] Dashboard loads without errors
  - [ ] No console errors in browser DevTools

```bash
# Terminal 1: Start frontend
cd frontend
python -m http.server 5500 --directory static

# Terminal 2: Test
curl http://localhost:5500/html/dashboard.html | head -20
```

- [ ] **Authentication Working**
  - [ ] Login endpoint responds
  - [ ] Password validation enforced
  - [ ] MFA options available
  - [ ] Session tokens generated

```bash
# Test login
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@example.com","password":"Password123!"}'
# Expected: success with access_token
```

---

### Level 2: Security Essentials (MUST PASS)

- [ ] **Secrets Configured**
  - [ ] All `.env` variables set (not example values)
  - [ ] Database URL with strong password
  - [ ] JWT secret (min 32 chars, random)
  - [ ] SMTP credentials for email
  - [ ] AWS credentials for backups (if using)

**Critical Environment Variables:**
```bash
DATABASE_URL=postgresql://user:STRONG_PASSWORD@localhost:5432/ztnas_prod
JWT_SECRET=your_very_secret_key_min_32_chars_random_string
ADMIN_EMAIL=admin@yourorg.com
ADMIN_PASSWORD=InitialAdminPassword123!
ENVIRONMENT=production
SENTRY_DSN=https://... (optional)
```

- [ ] **SSL/TLS Certificate**
  - [ ] Valid certificate for domain
  - [ ] Certificate not expired
  - [ ] Certificate chain complete
  - [ ] Private key secure and backed up

```bash
# Check certificate
ssh user@prod-server
openssl x509 -in /etc/ssl/certs/ztnas.crt -text -noout | grep -A2 "Validity"
# Expected: "Not Before" and "Not After" show valid dates
```

- [ ] **Database Backups Working**
  - [ ] Nightly backup scheduled
  - [ ] Backup stored off-site (S3, Azure, GCS)
  - [ ] Restore tested from backup
  - [ ] Retention policy enforced (30+ days)

```python
# Test backup manually
from backend.utils.database_backup import DatabaseBackup
backup = DatabaseBackup(settings.database_url, s3_bucket="ztnas-backups")
backup.create_backup()  # Should create backup file
# Verify file exists in S3: aws s3 ls s3://ztnas-backups/
```

- [ ] **Rate Limiting Active**
  - [ ] Endpoint rate limits configured
  - [ ] Login limited to 5/minute per IP
  - [ ] Registration limited to 3/hour per IP
  - [ ] API rate limits per key
  - [ ] Test produces 429 responses

```bash
# Test rate limiting
for i in {1..10}; do
  curl -X POST http://localhost:8000/api/v1/auth/login -d '{"email":"test@example.com"}' -H "Content-Type: application/json"
done
# Expected: First 5 succeed, next 5 return 429 (Too Many Requests)
```

---

### Level 3: Monitoring & Observability (SHOULD PASS)

- [ ] **Logging Configured**
  - [ ] Structured JSON logging enabled
  - [ ] Correlation IDs in all logs
  - [ ] Log level set to INFO (not DEBUG)
  - [ ] Logs exported to SIEM or file
  - [ ] Log rotation enabled (don't fill disk)

```bash
# Check logs format
tail -50 /var/log/ztnas/application.log | grep "correlation_id"
# Expected: JSON format with correlation_id fields
```

- [ ] **Monitoring Metrics Active**
  - [ ] Prometheus endpoint responding
  - [ ] Request latency metrics collected
  - [ ] Database connection pool metrics
  - [ ] Error rate tracking
  - [ ] Custom business metrics

```bash
# Check Prometheus metrics
curl http://localhost:8000/metrics
# Expected: prometheus format metrics (http_requests_total, etc.)
```

- [ ] **Alerting Configured**
  - [ ] Alert for high error rate (>1%)
  - [ ] Alert for slow responses (p95 > 500ms)
  - [ ] Alert for database disconnects
  - [ ] Alert for authentication failures (>10/min per IP)
  - [ ] Alert recipients configured

```yaml
# Example AlertManager config
alerts:
  - name: "High Error Rate"
    condition: "error_rate > 0.01"
    recipients: ["ops@example.com"]
  - name: "Slow API Responses"
    condition: "response_time_p95 > 500"
    recipients: ["ops@example.com"]
```

---

### Level 4: Compliance & Audit (SHOULD PASS)

- [ ] **Audit Logging Complete**
  - [ ] All authentication events logged
  - [ ] All authorization decisions logged
  - [ ] All data access logged
  - [ ] Audit logs tamper-proof
  - [ ] Retention policy enforced

```sql
-- Verify audit logs exist
SELECT COUNT(*) FROM audit_logs WHERE created_at > NOW() - INTERVAL 1 DAY;
-- Expected: >100 entries for active system
```

- [ ] **GDPR Compliance Ready**
  - [ ] Data export endpoint working
  - [ ] Data deletion endpoint working
  - [ ] Privacy policy published
  - [ ] Data retention policies documented
  - [ ] Data processing agreement signed

```bash
# Test GDPR endpoints
curl -X POST http://localhost:8000/api/v1/users/{user_id}/export \
  -H "Authorization: Bearer $TOKEN"
# Expected: Export file generated

curl -X POST http://localhost:8000/api/v1/users/{user_id}/delete \
  -H "Authorization: Bearer $TOKEN"
# Expected: Deletion scheduled with confirmation email
```

- [ ] **Security Documentation**
  - [ ] Security policy documented
  - [ ] Incident response plan written
  - [ ] Password policy defined
  - [ ] MFA requirements documented
  - [ ] Access control policies defined

---

## 🔧 Post-Deployment Verification

### Day 1: Immediately After Deployment

```bash
# 1. Backend Health Check
curl http://prod.ztnas.example.com/api/v1/health

# 2. Frontend Load Test  
for i in {1..100}; do
  curl -s http://prod.ztnas.example.com/ > /dev/null &
done
wait

# 3. Authentication Test
curl -X POST http://prod.ztnas.example.com/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"TestPass123!"}'

# 4. Database Query
psql -h prod-db.example.com -U ztnas_user -d ztnas_prod \
  -c "SELECT COUNT(*) FROM users;"

# 5. Check Logs
tail -100 /var/log/ztnas/application.log | grep -i error

# 6. Monitor CPU/Memory
top -b -n 1 | head -20
ps aux | grep "uvicorn\|gunicorn"
```

### Week 1: Initial Monitoring

**Daily Checks:**

```bash
# Check error rate
curl -s http://localhost:8000/metrics | grep http_requests_total | grep 5xx

# Check response times
curl -s http://localhost:8000/metrics | grep http_request_duration_seconds

# Check database connections
psql -U postgres -d ztnas_prod \
  -c "SELECT count(*) FROM pg_stat_activity WHERE datname = 'ztnas_prod';"

# Check backup status
aws s3 ls s3://ztnas-backups/ --recursive | tail -5

# Check SSL certificate validity
echo | openssl s_client -connect prod.ztnas.example.com:443 2>/dev/null | \
  openssl x509 -noout -dates
```

**Weekly Report Template:**

```markdown
# ZTNAS Production - Weekly Status Report
Date: 2024-04-04

## Uptime
- Availability: 99.98% (Target: 99.95%)
- Downtime: 2.88 minutes
- Incidents: 1 (resolved in 15 min)

## Performance
- Average response time: 145ms
- P95 response time: 298ms
- Error rate: 0.02%
- Requests processed: 2.1M

## Security
- Failed login attempts: 523
- Rate-limited requests: 18
- Security alerts: 0
- Audit logs created: 45,231

## Infrastructure
- Database size: 2.3 GB
- Backup status: ✓ Last backup 2024-04-04 03:15 UTC
- Certificate expiry: 365 days
- Disk usage: 42%

## Issues & Resolutions
- (None this week)

## Next Steps
- Monitor database growth
- Plan SSL certificate renewal (in 11 months)
```

---

## 🔐 Security Post-Deployment Checks

### Verify No Exposed Secrets

```bash
# Check git history for secrets
git log -p | grep -i "password\|secret\|key" | head -20

# Check environment files
grep -r "password" .env .env.local docker-compose.yml 2>/dev/null | grep -v "password_" | grep -v "# "

# Check if using example credentials
grep -r "example.com\|test@test\|Password123" backend/config.py backend/main.py frontend/
```

### Verify HTTPS is Enforced

```bash
# Test HTTP redirect to HTTPS
curl -v http://prod.ztnas.example.com/ 2>&1 | grep "301\|302\|Location"
# Expected: Redirect to https://

# Check HSTS header
curl -I https://prod.ztnas.example.com/ | grep -i "strict-transport-security"
# Expected: max-age=31536000

# Check CSP header
curl -I https://prod.ztnas.example.com/ | grep -i "content-security-policy"
```

### Verify Authentication is Working

```bash
# Test login without MFA
curl -X POST http://prod.ztnas.example.com/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@example.com","password":"Password123!"}'
# If MFA required: Expected 401 or 403
# If allows: Expected 200 with token

# Test invalid password
curl -X POST http://prod.ztnas.example.com/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@example.com","password":"WrongPassword"}'
# Expected: 401 Unauthorized

# Test account lockout
for i in {1..6}; do
  curl -X POST http://prod.ztnas.example.com/api/v1/auth/login \
    -d '{"email":"testuser@example.com","password":"wrong"}'
done
# Requests 1-5: 401
# Request 6: Should get locked or delayed (rate limited)
```

---

## 📊 Performance Baseline

These are expected performance targets for a properly configured ZTNAS system:

```
Metric                      Target          Acceptable        Warning
─────────────────────────────────────────────────────────────────
Response Time (p50)        <50ms           <100ms            >150ms
Response Time (p95)        <200ms          <300ms            >500ms
Response Time (p99)        <500ms          <1000ms           >2000ms

Request Success Rate       >99.9%          >99%              <98%
Error Rate (5xx)          <0.1%           <0.5%             >1%
Rate Limit Triggers       <5/min/IP       <10/min/IP        >20/min/IP

Database Query Time       <50ms           <100ms            >500ms
Authentication Success    >95%            >90%              <80%

Login Endpoint (POST)     <100ms          <200ms            >500ms
Dashboard Load (GET)      <150ms          <300ms            >500ms
API Requests (avg)        <100ms          <200ms            >500ms

Uptime                    99.99%          99.95%            <99%
Backup Success Rate       100%            >99%              <95%

CPU Usage                 <40%            <60%              >80%
Memory Usage              <50%            <70%              >85%
Disk I/O                  <40%            <60%              >80%
```

---

## 🚨 Critical Issues Resolution

### Issue: Login Page Not Loading

```
Symptoms: Blank page, no error in console
Resolution:
1. Check frontend server: curl http://localhost:5500/html/login.html
2. Check browser console: F12 > Console tab
3. Check Chart.js CDN: Look for failed requests
4. Restart frontend server
5. Clear browser cache: Ctrl+Shift+Delete
```

### Issue: "Database Connection Refused"

```
Symptoms: API returns 500 errors
Resolution:
1. Check PostgreSQL running: psql -U postgres -d postgres
2. Check DATABASE_URL in .env
3. Check network connectivity: ping <db-host>
4. Check firewall rules
5. Verify credentials: psql -h <host> -U <user> -d <db>
6. Check max_connections limit
```

### Issue: "Rate Limit: Too Many Requests"

```
Symptoms: Getting 429 errors
Resolution:
1. Wait 60 seconds for rate limit to reset
2. Check if automated traffic hitting endpoint
3. Check for bot attacks (look in logs)
4. Verify rate limits are appropriate
5. Add IP to whitelist if trusted
```

### Issue: MFA Not Working

```
Symptoms: MFA code not accepted, TOTP app out of sync
Resolution:
1. Verify system time is correct: date
2. Check TOTP secret in database
3. Test with Google Authenticator app
4. Regenerate backup codes if lost
5. Use recovery key from account
```

---

## ✅ Go-Live Checklist

**Final 24-Hour Before Production:**

- [ ] All code deployed and tested
- [ ] Database backups verified
- [ ] SSL certificate valid
- [ ] Monitoring and alerting active
- [ ] All team members notified of deployment
- [ ] Incident response team on standby
- [ ] Emergency contact numbers documented
- [ ] Rollback procedure tested
- [ ] All stakeholders notified

**During Go-Live (1-2 hours):**

- [ ] Monitor active: Watch metrics dashboard
- [ ] Logs monitored: Check for errors
- [ ] Sample users: Test login, basic workflows
- [ ] Performance: Verify response times
- [ ] Errors: Alert on any 5xx responses
- [ ] Support ready: Team available for issues

**After Go-Live Success (Day 1):**

- [ ] Post-deployment review
- [ ] Document any issues encountered
- [ ] Evaluate performance against baseline
- [ ] Collect user feedback
- [ ] Plan any optimizations needed
- [ ] Schedule next review (1 week)

---

## 📞 Support & Escalation

### During Production Issues

**Level 1 - Support Team (0-30 minutes):**
- Check documentation
- Restart application
- Check system resources
- Verify configuration

**Level 2 - Engineering Team (30 minutes - 2 hours):**
- Analyze logs
- Check database
- Review recent changes
- Debug performance issues

**Level 3 - Emergency Response (2+ hours):**
- Enterprise support
- Professional services
- Architecture review
- Major incident mitigation

**Escalation Matrix:**
```
Severity        Response Time    Escalation Time    Action
─────────────────────────────────────────────────────────────
Critical        15 min           1 hour             War room
High            1 hour           4 hours            Senior engineer
Medium          4 hours          8 hours            Team review
Low             1 day            3 days             Backlog
```

---

## 📝 Deployment Sign-Off

```
Production Deployment: ZTNAS v2.0
Date: 2024-03-28
Environment: prod.ztnas.example.com

Verifications:
☑ All security checks passed
☑ Performance baseline established
☑ Monitoring active
☑ Backups verified
☑ Team trained
☑ Support procedure documented

Deployment Authority: _____________________ Date: __________
Operations Lead:      _____________________ Date: __________
Security Officer:     _____________________ Date: __________
Application Owner:    _____________________ Date: __________

Authorized for production deployment.
```

---

**ZTNAS Production Deployment Readiness Checklist v2.0**  
Last Updated: 2024-03-28 | Status: Ready for Use
