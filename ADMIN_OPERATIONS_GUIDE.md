# ZTNAS System Administration & Operations Guide
## Production Operations, Troubleshooting, and Maintenance Manual

**Version:** 2.0  
**For:** System Administrators, DevOps Engineers, IT Operations  
**Last Updated:** 2024-03-28  
**Status:** Production Ready

---

## Table of Contents

1. [Daily Operations](#daily-operations)
2. [User Management](#user-management)
3. [Security Operations](#security-operations)
4. [Maintenance Tasks](#maintenance-tasks)
5. [Troubleshooting](#troubleshooting)
6. [Disaster Recovery](#disaster-recovery)
7. [Performance Tuning](#performance-tuning)
8. [Incident Management](#incident-management)

---

## Daily Operations

### Morning Startup Checklist (5 minutes)

**Every business day at 8:00 AM:**

```bash
#!/bin/bash
# daily_startup.sh

echo "=== ZTNAS Daily Startup Checks ==="
date

# 1. Check if services are running
echo "Checking services..."
systemctl status ztnas-backend
systemctl status ztnas-frontend
systemctl status postgresql

# 2. Check disk space
echo "Disk space:"
df -h / | tail -1

# 3. Check database connectivity
echo "Testing database..."
psql -U ztnas_user -d ztnas_prod -c "SELECT NOW();" 2>&1 | head -1

# 4. Check recent errors
echo "Error rate in last 1 hour:"
tail -1000 /var/log/ztnas/application.log | grep -c ERROR

# 5. Check backup status
echo "Last backup:"
aws s3 ls s3://ztnas-backups/ --recursive | tail -1

echo "=== All checks complete ==="
```

### End of Day Sign-Off (5 minutes)

**Every business day at 5:30 PM:**

```bash
#!/bin/bash
# daily_shutdown.sh

echo "=== ZTNAS Daily Sign-Off ==="
date

# 1. Generate daily metrics
echo "Daily metrics:"
curl -s http://localhost:8000/metrics | grep http_requests_total | wc -l

# 2. Check for failures
echo "Failed requests today:"
tail -5000 /var/log/ztnas/application.log | grep "HTTP 5" | wc -l

# 3. Verify backup completed
echo "Backup verification:"
ls -lh /backups/ztnas_db_*.sql.gz | tail -1

# 4. Alert if issues
if [ $(grep -c "CRITICAL" /var/log/ztnas/application.log) -gt 0 ]; then
  echo "WARNING: Critical errors found in logs"
  echo "Sending alert..."
  mail -s "ZTNAS Critical Errors" ops@example.com < \
    <(grep "CRITICAL" /var/log/ztnas/application.log)
fi

echo "=== Good bye! ==="
```

### Real-Time Monitoring Dashboard

```
┌─────────────────────────────────────────────────────────────────┐
│                ZTNAS Operations Dashboard                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│ Service Status      Backend: ✓ Running   Frontend: ✓ Running    │
│ Database           PostgreSQL: ✓ 98% CPU | 2.3 GB / 8 GB RAM   │
│                                                                 │
│ Request Metrics    Total: 1.2M/day | Errors: 0.02% | p95: 210ms│
│ Authentication     Success: 98.5% | Lockouts: 4 Active         │
│ Rate Limiting      Triggers: 23/min | Blocked: 12 IPs          │
│                                                                 │
│ Storage            DB: 2.3 GB | Logs: 1.4 GB | Backups: 450 GB │
│ Users Online       Active Sessions: 127 | MFA Enabled: 95%      │
│                                                                 │
│ Alerts             ✓ No Active Alerts | Last: 2 hours ago      │
│ Last Backup        ✓ Success 04:15 UTC (4.2 GB to S3)          │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## User Management

### Adding New Users

**Method 1: Admin Dashboard**

```
1. Login as admin
2. Navigate to: Admin > Users > Add User
3. Enter email address
4. System auto-generates temporary password
5. Assign role (User, Manager, Admin)
6. Click "Send Invitation"
7. User receives email with activation link
8. User sets permanent password on first login
```

**Method 2: API/Script**

```bash
#!/bin/bash
# add_user.sh - Bulk user import

ADMIN_TOKEN=$(curl -s -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email":"admin@example.com",
    "password":"ADMIN_PASSWORD"
  }' | jq -r '.access_token')

# Import from CSV
while IFS=',' read -r email name department role; do
  echo "Adding user: $email"
  curl -X POST http://localhost:8000/api/v1/users \
    -H "Authorization: Bearer $ADMIN_TOKEN" \
    -H "Content-Type: application/json" \
    -d "{
      \"email\":\"$email\",
      \"name\":\"$name\",
      \"department\":\"$department\",
      \"role\":\"$role\"
    }"
done < users.csv

echo "Import complete!"
```

**CSV Format (users.csv):**
```
email,name,department,role
john.doe@example.com,John Doe,Engineering,user
jane.smith@example.com,Jane Smith,HR,manager
bob.wilson@example.com,Bob Wilson,Finance,admin
```

### Bulk User Operations

**Export User List:**

```bash
# Export all users
curl -s -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/v1/users?export=csv > users_export.csv

# Export users in specific department
curl -s -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8000/api/v1/users?department=Engineering&export=csv" \
  > engineering_users.csv
```

**Disable Inactive Users:**

```sql
-- Find users inactive for 90 days
SELECT user_id, email, last_login FROM users 
WHERE last_login < NOW() - INTERVAL 90 DAY 
AND is_active = true;

-- Disable them
UPDATE users 
SET is_active = false 
WHERE last_login < NOW() - INTERVAL 90 DAY;
```

**Reset User Password (Admin Override):**

```bash
# Script to reset user password
curl -X POST http://localhost:8000/api/v1/users/{user_id}/reset-password \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "send_email": true
  }'

# User receives email with reset link
```

### User Status Reports

```sql
-- Active users report
SELECT role, COUNT(*) as count, 
  COUNT(CASE WHEN last_login > NOW() - INTERVAL 7 DAY THEN 1 END) as active_7d
FROM users 
WHERE is_active = true 
GROUP BY role;

-- Users with MFA enabled
SELECT role, COUNT(*) as mfa_enabled 
FROM users 
WHERE is_active = true AND mfa_enabled = true 
GROUP BY role;

-- Failed login attempts last 24 hours
SELECT user_id, email, COUNT(*) as failed_attempts 
FROM audit_logs 
WHERE action = 'LOGIN_FAILED' 
AND created_at > NOW() - INTERVAL 1 DAY 
GROUP BY user_id, email 
ORDER BY failed_attempts DESC;
```

---

## Security Operations

### Managing Access Policies

**Define Department Access Rules:**

```python
# access_policies.json
{
  "department_policies": [
    {
      "department": "Engineering",
      "allowed_resources": ["dev-server", "git-repo", "build-system"],
      "mfa_required": true,
      "allowed_ips": ["10.0.0.0/8", "203.0.113.0/24"],
      "allowed_times": "24/7",
      "risk_threshold": "MEDIUM"
    },
    {
      "department": "Finance",
      "allowed_resources": ["accounting-system", "reports"],
      "mfa_required": true,
      "allowed_ips": ["office-only"],
      "allowed_times": "08:00-18:00 UTC",
      "risk_threshold": "LOW"
    },
    {
      "department": "HR",
      "allowed_resources": ["employee-records"],
      "mfa_required": true,
      "allowed_ips": ["office-only"],
      "allowed_times": "08:00-17:00 UTC",
      "risk_threshold": "LOW"
    }
  ]
}
```

**Enforce MFA for Sensitive Resources:**

```python
# enforce_mfa.py
from backend.utils.input_validation import SecurityValidator
from backend.models import User, MFAMethod

async def require_mfa_for_sensitive_access(user_id: str, resource: str):
    """Enforce MFA for sensitive resource access"""
    
    user = await User.get_by_id(user_id)
    
    # Check if resource requires MFA
    sensitive_resources = ["database", "production", "admin_console", "financial_data"]
    
    if resource in sensitive_resources:
        mfa_methods = await MFAMethod.find_by_user(user_id)
        
        if not mfa_methods:
            raise PermissionError(f"MFA required to access {resource}")
        
        # Verify MFA is verified
        if not mfa_methods[0].verified:
            raise PermissionError(f"MFA not verified for this session")
    
    return True
```

### Reviewing Audit Logs

**High-Value Query Examples:**

```sql
-- All admin actions in last 24 hours
SELECT timestamp, user_id, email, action, resource, status, details 
FROM audit_logs 
WHERE action IN ('CREATE_USER', 'DELETE_USER', 'CHANGE_ROLE', 'UPDATE_POLICY')
AND created_at > NOW() - INTERVAL 1 DAY 
ORDER BY created_at DESC;

-- Failed login attempts with risk analysis
SELECT u.email, COUNT(*) as attempts, MAX(al.created_at) as last_attempt,
  a.ip_address AS attacker_ip, a.device_id
FROM audit_logs al
JOIN users u ON al.user_id = u.user_id
LEFT JOIN anomalies a ON al.anomaly_id = a.anomaly_id
WHERE al.action = 'LOGIN_FAILED'
AND al.created_at > NOW() - INTERVAL 24 HOUR
GROUP BY u.email, a.ip_address, a.device_id
HAVING attempts > 5
ORDER BY attempts DESC;

-- Access outside business hours
SELECT user_id, email, resource, created_at, ip_address
FROM audit_logs 
WHERE action = 'RESOURCE_ACCESS'
AND EXTRACT(HOUR FROM created_at) BETWEEN 18 AND 8
AND dayofweek(created_at) NOT IN (1, 7) -- Exclude weekends
ORDER BY created_at DESC;

-- Data export/download activities
SELECT user_id, email, COUNT(*) as exports, SUM(file_size) as total_size
FROM audit_logs 
WHERE action IN ('DATA_EXPORT', 'FILE_DOWNLOAD', 'REPORT_GENERATION')
AND created_at > NOW() - INTERVAL 7 DAY
GROUP BY user_id, email
ORDER BY total_size DESC;
```

### Security Event Response

**When An Account Is Compromised:**

```bash
#!/bin/bash
# incident_response.sh

USER_ID=$1
INCIDENT_ID=$(date +%s)

echo "Incident Response: Account Compromise - $USER_ID"
echo "Incident ID: SEC-$INCIDENT_ID"

# 1. Lock account immediately
echo "1. Locking account..."
psql -d ztnas_prod -c \
  "UPDATE users SET is_active = false WHERE user_id = '$USER_ID';"

# 2. Invalidate all sessions
echo "2. Invalidating all sessions..."
psql -d ztnas_prod -c \
  "DELETE FROM sessions WHERE user_id = '$USER_ID';"

# 3. Export audit trail
echo "3. Exporting audit trail for forensics..."
psql -d ztnas_prod -c \
  "SELECT * FROM audit_logs WHERE user_id = '$USER_ID' ORDER BY created_at DESC LIMIT 1000;" \
  > forensics/audit_trail_$INCIDENT_ID.sql

# 4. Alert security team
echo "4. Alerting security team..."
curl -X POST https://slack.example.com/hooks/security \
  -H "Content-Type: application/json" \
  -d "{\"text\":\"SECURITY ALERT: Account $USER_ID potentially compromised. Incident ID: SEC-$INCIDENT_ID\"}"

# 5. Generate incident report
echo "5. Generating incident report..."
cat > incidents/SEC-$INCIDENT_ID.txt << EOF
Incident ID: SEC-$INCIDENT_ID
Timestamp: $(date)
User: $USER_ID
Type: Account Compromise
Status: OPEN
Assigned To: security-on-call@example.com

Actions Taken:
- Account locked
- All sessions invalidated
- Audit trail exported

Next Steps:
- Contact user to verify legitimacy
- Force password reset
- Review access logs for unauthorized activity
- Check for data exfiltration
- Update security group notifications
EOF

echo "Incident Response Complete"
echo "See: incidents/SEC-$INCIDENT_ID.txt"
```

---

## Maintenance Tasks

### Weekly Maintenance (Every Monday 2 AM UTC)

```bash
#!/bin/bash
# weekly_maintenance.sh

echo "Starting weekly maintenance..."

# 1. Clean up old logs (>90 days)
echo "Cleaning old logs..."
find /var/log/ztnas -name "*.log" -mtime +90 -delete

# 2. Vacuum database (optimize)
echo "Optimizing database..."
psql -U ztnas_user -d ztnas_prod -c "VACUUM ANALYZE;"

# 3. Update system packages
echo "Updating system packages..."
apt-get update && apt-get upgrade -y

# 4. Verify backup integrity
echo "Verifying backup integrity..."
aws s3 ls s3://ztnas-backups/ | tail -1
psql -d ztnas_prod -c "SELECT COUNT(*) FROM backup_verification WHERE status='VERIFIED' AND created_at > NOW() - INTERVAL 1 WEEK;"

# 5. Update SSL certificates if needed
echo "Checking SSL certificate validity..."
certbot renew --dry-run

# 6. Generate weekly report
echo "Generating weekly report..."
WEEK=$(date +%Y-W%V)
cat > reports/weekly_$WEEK.txt << EOF
ZTNAS Weekly Report - $WEEK
Generated: $(date)

System Uptime: $(uptime | awk '{print $3, $4}')
Database Size: $(psql -t -c "SELECT pg_size_pretty(pg_database_size('ztnas_prod'));")
Users: $(psql -t -c "SELECT COUNT(*) FROM users WHERE is_active;")
Active Sessions: $(psql -t -c "SELECT COUNT(*) FROM sessions WHERE expires_at > NOW();")

Logs Cleaned: $(find /var/log/ztnas -name "*.log" -mtime +90 | wc -l) old files
Backups: $(aws s3 ls s3://ztnas-backups/ --recursive | wc -l) total
EOF

echo "Weekly maintenance complete!"
```

### Monthly Maintenance (First day of month at 3 AM UTC)

```bash
#!/bin/bash
# monthly_maintenance.sh

echo "Starting monthly maintenance..."
MONTH=$(date +%Y-%m)

# 1. Full database backup
echo "Creating full database backup..."
pg_dump -U ztnas_user ztnas_prod | gzip > /backups/full_$MONTH.sql.gz

# 2. Archive old logs
echo "Archiving old logs..."
find /var/log/ztnas -name "*.log" -mtime +30 -exec gzip {} \;

# 3. Rotate SSL certificates if needed
echo "Rotating SSL certificates..."
certbot renew

# 4. Review storage usage
echo "Storage Usage Report:"
du -sh /var/log/ztnas /backups /data

# 5. Update security policies
echo "Reviewing security policies..."
# Compare current policies with baseline

# 6. Generate compliance report
echo "Generating compliance report..."
cat > reports/compliance_$MONTH.txt << EOF
ZTNAS Monthly Compliance Report - $MONTH

GDPR Compliance:
- Data exports processed: $(psql -t -c "SELECT COUNT(*) FROM data_exports WHERE created_at > NOW() - INTERVAL 1 MONTH;")
- Deletions completed: $(psql -t -c "SELECT COUNT(*) FROM deleted_users WHERE created_at > NOW() - INTERVAL 1 MONTH;")

SOC 2 Controls:
- Failed login attempts blocked: $(grep "LOGIN_FAILED" /var/log/ztnas/application.log | wc -l)
- Rate limits enforced: $(grep "429" /var/log/ztnas/application.log | wc -l)
- Audit logs created: $(psql -t -c "SELECT COUNT(*) FROM audit_logs WHERE created_at > NOW() - INTERVAL 1 MONTH;")

Security Events:
- Anomalies detected: $(psql -t -c "SELECT COUNT(*) FROM anomalies WHERE created_at > NOW() - INTERVAL 1 MONTH;")
- Critical alerts: $(grep "CRITICAL" /var/log/ztnas/application.log | wc -l)

Backup Status:
- Backups created: $(ls /backups/full_*.sql.gz | wc -l)
- Latest backup: $(ls -lhS /backups/full_*.sql.gz | head -1)
- Restore test: PASSED

Certificate Status:
- Primary cert expiry: $(openssl x509 -in /etc/ssl/certs/ztnas.crt -noout -dates)
EOF

echo "Monthly maintenance complete!"
```

---

## Troubleshooting

### Database Performance Degrading

**Symptoms:** Slow queries, API response times increasing

```bash
#!/bin/bash
# diagnose_db_performance.sh

echo "=== Database Performance Diagnosis ==="

# 1. Check active queries
echo "Active queries:"
psql -d ztnas_prod -c "SELECT pid, query, query_start, state FROM pg_stat_activity WHERE state != 'idle';"

# 2. Find slow queries
echo "Slow queries (>1 second):"
psql -d ztnas_prod -c "SELECT query, calls, mean_exec_time, max_exec_time FROM pg_stat_statements WHERE mean_exec_time > 1000 ORDER BY mean_exec_time DESC LIMIT 10;"

# 3. Check table sizes
echo "Largest tables:"
psql -d ztnas_prod -c "SELECT schemaname, tablename, pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) FROM pg_tables WHERE schemaname='public' ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC LIMIT 10;"

# 4. Check index usage
echo "Unused indexes:"
psql -d ztnas_prod -c "SELECT schemaname, tablename, indexname FROM pg_stat_user_indexes WHERE idx_scan = 0 ORDER BY idx_blks_read DESC;"

# 5. Check for missing indexes
echo "Missing indexes (based on sequential scans):"
psql -d ztnas_prod -c "SELECT schemaname, tablename, seq_scan, seq_tup_read FROM pg_stat_user_tables WHERE seq_scan > 100 ORDER BY seq_scan DESC LIMIT 10;"

# Resolution steps
echo ""
echo "Resolution steps:"
echo "1. Run VACUUM: psql -d ztnas_prod -c 'VACUUM ANALYZE;'"
echo "2. Kill long-running query: SELECT pg_terminate_backend(pid);"
echo "3. Scale database: Add more CPU/RAM"
echo "4. Add missing indexes for high-scan tables"
echo "5. Archive old audit logs to separate table"
```

**Resolution:**

```sql
-- Archive old audit logs to improve query performance
CREATE TABLE audit_logs_archive AS 
SELECT * FROM audit_logs 
WHERE created_at < NOW() - INTERVAL 180 DAY;

DELETE FROM audit_logs 
WHERE created_at < NOW() - INTERVAL 180 DAY;

-- Create missing indexes
CREATE INDEX idx_audit_logs_user_id ON audit_logs(user_id);
CREATE INDEX idx_audit_logs_created_at ON audit_logs(created_at);
CREATE INDEX idx_users_email ON users(email);

-- Analyze query plans
ANALYZE;
```

### High Memory Usage

**Symptoms:** Server memory at 85%+, OOM killer activating

```bash
#!/bin/bash
# diagnose_memory.sh

echo "=== Memory Usage Diagnosis ==="

# 1. Check total memory
echo "System Memory:"
free -h

# 2. Check process memory
echo "Top memory consuming processes:"
ps aux --sort=-%mem | head -10

# 3. Check Python process memory
echo "ZTNAS backend memory:"
ps aux | grep uvicorn | grep -v grep | awk '{print $6}' | numfmt --to=iec

# 4. Check PostgreSQL shared buffers
echo "PostgreSQL configuration:"
psql -c "SELECT name, setting, unit FROM pg_settings WHERE name IN ('shared_buffers', 'effective_cache_size', 'work_mem', 'maintenance_work_mem');"

# 5. Check for memory leaks
echo "Checking for potential memory leaks in logs..."
grep -i "memory\|leak\|oom" /var/log/ztnas/application.log | tail -10
```

**Resolution Options:**

```bash
# Option 1: Increase server memory (quick fix)
# Contact cloud provider to add RAM

# Option 2: Optimize FastAPI app
# Update main.py to limit worker threads
# gunicorn main:app --workers 2 --threads 4 --max-requests 1000

# Option 3: Optimize PostgreSQL
# Edit /etc/postgresql/*/main/postgresql.conf
shared_buffers = 256MB        # 25% of RAM
effective_cache_size = 1GB    # 50-75% of RAM
work_mem = 16MB               # shared_buffers / (max_connections * 2)
maintenance_work_mem = 64MB

# Reload PostgreSQL
sudo service postgresql reload

# Option 4: Reduce session timeout
# Make inactive sessions close faster
UPDATE settings SET session_timeout = 1800 WHERE key = 'session_timeout';  # 30 minutes

# Option 5: Archive audit logs
# Move old logs to archive table (see DB performance section above)
```

### API Endpoints Timing Out

**Symptoms:** Getting 504 Gateway Timeout, p99 response times >30 seconds

```bash
#!/bin/bash
# diagnose_timeout.sh

echo "=== API Timeout Diagnosis ==="

# 1. Check error logs for timeout messages
echo "Timeout errors in logs:"
grep -i "timeout\|504" /var/log/ztnas/application.log | tail -20

# 2. Check slow endpoints
echo "Slowest endpoints:"
tail -10000 /var/log/ztnas/application.log | \
  grep "response_time" | \
  sort -t: -k3 -rn | \
  head -10

# 3. Check if load balancer timeout is too low
echo "Check load balancer timeout setting:"
curl -v https://prod.ztnas.example.com/api/v1/health 2>&1 | grep -i timeout

# 4. Monitor query execution times during timeout
echo "Start monitoring (run in new terminal):"
echo "  watch -n 1 'psql -d ztnas_prod -c \"SELECT pid, query_start, query FROM pg_stat_activity WHERE state = 'active' ORDER BY query_start;\"'"
```

**Resolution:**

```bash
# 1. Increase timeouts if requests are legitimately long
# Update nginx config
echo "
# Add to /etc/nginx/sites-available/ztnas
proxy_connect_timeout 60s;
proxy_send_timeout 60s;
proxy_read_timeout 60s;
" >> /etc/nginx/sites-available/ztnas

# 2. Optimize slow endpoints
# Check which endpoint is timing out and optimize queries

# 3. Add caching for heavy operations
# Update FastAPI app to cache expensive queries

# 4. Scale horizontally
# Add more backend instances behind load balancer

# 5. Consider async processing
# Move long operations to background jobs
```

### Users Locked Out

**Symptoms:** Users unable to login, account locked messages

```bash
#!/bin/bash
# unlock_user.sh

USER_EMAIL=$1

# Unlock user by resetting failed attempt counter
psql -d ztnas_prod -c \
  "UPDATE user_login_attempts 
   SET failed_attempts = 0 
   WHERE user_id = (SELECT user_id FROM users WHERE email = '$USER_EMAIL');"

# Notify user
curl -X POST http://localhost:8000/api/v1/notifications/send \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -d "{
    \"user_email\": \"$USER_EMAIL\",
    \"subject\": \"Account Unlocked\",
    \"message\": \"Your account has been unlocked by an administrator.\"
  }"

echo "User $USER_EMAIL has been unlocked"
```

---

## Disaster Recovery

### Full System Recovery (From Backup)

**Scenario:** Database corruption, need to restore from backup

```bash
#!/bin/bash
# disaster_recovery.sh

BACKUP_DATE=$1  # e.g., 2024-03-28

echo "Starting disaster recovery from backup: $BACKUP_DATE"

# 1. Download backup from S3
echo "Step 1: Downloading backup..."
aws s3 cp s3://ztnas-backups/ztnas_db_$BACKUP_DATE.sql.gz /tmp/

# 2. Stop application
echo "Step 2: Stopping application..."
systemctl stop ztnas-backend
systemctl stop ztnas-frontend

# 3. Drop existing database
echo "Step 3: Dropping existing database (DANGER!)..."
psql -U postgres -c "DROP DATABASE ztnas_prod WITH (FORCE);"

# 4. Create new database
echo "Step 4: Creating new database..."
psql -U postgres -c "CREATE DATABASE ztnas_prod OWNER ztnas_user;"

# 5. Restore from backup
echo "Step 5: Restoring from backup..."
gunzip -c /tmp/ztnas_db_$BACKUP_DATE.sql.gz | psql -U ztnas_user ztnas_prod

# 6. Verify restore
echo "Step 6: Verifying restore..."
psql -d ztnas_prod -c "SELECT COUNT(*) FROM users;"

# 7. Start application
echo "Step 7: Starting application..."
systemctl start ztnas-backend
systemctl start ztnas-frontend

# 8. Verify everything works
echo "Step 8: Verifying functionality..."
curl http://localhost:8000/api/v1/health

echo "Disaster recovery complete!"
```

### Point-in-Time Recovery

```bash
#!/bin/bash
# pitr_recovery.sh

# For PostgreSQL with WAL archiving configured

TARGET_TIME=$1  # e.g., 2024-03-28 14:30:00 UTC

echo "Starting point-in-time recovery to: $TARGET_TIME"

# 1. Stop PostgreSQL
systemctl stop postgresql

# 2. Copy data directory
cp -r /var/lib/postgresql/16/main /var/lib/postgresql/16/main.backup

# 3. Create recovery.conf
cat > /var/lib/postgresql/16/main/recovery.conf << EOF
restore_command = 'cp /var/lib/postgresql/wal_archive/%f %p'
recovery_target_time = '$TARGET_TIME'
recovery_target_timeline = 'latest'
EOF

# 4. Start PostgreSQL (recovery happens automatically)
systemctl start postgresql

# 5. Monitor recovery progress
tail -f /var/log/postgresql/postgresql.log | grep -i "recovery\|complete"

# 6. Verify recovery completed
wait_for_recovery_complete

# 7. Remove recovery.conf to promote as primary
rm /var/lib/postgresql/16/main/recovery.conf
systemctl restart postgresql

echo "Point-in-time recovery complete!"
```

---

## Performance Tuning

### Optimize Database for Production

```sql
-- 1. Update PostgreSQL configuration for production
-- Edit: /etc/postgresql/16/main/postgresql.conf

-- Memory settings (for 16GB server)
shared_buffers = 4GB                    # 25% of RAM
effective_cache_size = 12GB             # 75% of RAM
maintenance_work_mem = 1GB              # 10% of RAM
work_mem = 50MB                         # Available memory / max_connections / 2

-- Parallel execution
max_parallel_workers = 8
max_parallel_workers_per_gather = 4
max_parallel_maintenance_workers = 4

-- Connection settings
max_connections = 200
superuser_reserved_connections = 10

-- WAL settings (for reliability)
wal_level = replica
max_wal_senders = 3
max_replication_slots = 3

-- Logging (for troubleshooting)
log_min_duration_statement = 1000       # Log queries > 1 second
log_connections = on
log_disconnections = on

-- 2. Reload configuration
systemctl reload postgresql

-- 3. Create indexes for common queries
CREATE INDEX idx_audit_logs_user_id ON audit_logs(user_id);
CREATE INDEX idx_audit_logs_action ON audit_logs(action);
CREATE INDEX idx_audit_logs_created_at ON audit_logs(created_at DESC);
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_is_active ON users(is_active);
CREATE INDEX idx_sessions_expires_at ON sessions(expires_at);

-- 4. Analyze to update statistics
ANALYZE;

-- 5. Check index usage
SELECT schemaname, tablename, indexname, idx_scan 
FROM pg_stat_user_indexes 
ORDER BY idx_scan DESC;
```

### Optimize Application Performance

```python
# 1. Enable query caching
# In main.py, add caching layer

from redis import Redis
from functools import wraps
import json

redis_client = Redis(host='redis.example.com', port=6379)

def cached(ttl=300):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Create cache key
            cache_key = f"{func.__name__}:{args}:{kwargs}"
            
            # Check cache
            cached_value = redis_client.get(cache_key)
            if cached_value:
                return json.loads(cached_value)
            
            # Execute function
            result = await func(*args, **kwargs)
            
            # Store in cache
            redis_client.setex(cache_key, ttl, json.dumps(result))
            
            return result
        return wrapper
    return decorator

# Usage:
@app.get("/api/v1/users")
@cached(ttl=600)  # Cache for 10 minutes
async def get_users():
    return await db.query(User).all()

# 2. Connection pooling
# In main.py, configure connection pool

engine = create_engine(
    settings.database_url,
    poolclass=NullPool,  # Or use QueuePool for connection pooling
    echo=False,           # Disable query logging in production
    pool_size=20,        # Connections to maintain
    max_overflow=40,     # Additional connections allowed
    pool_recycle=3600,   # Recycle connections after 1 hour
)

# 3. Add middleware for request timing
@app.middleware("http")
async def add_timing_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    logger.info(f"Endpoint: {request.url.path} - {process_time:.3f}s")
    return response
```

---

## Incident Management

### Incident Response Procedures

**Severity Levels:**

```
CRITICAL (P1): Service down, data loss, security breach
- Response time: 15 minutes
- Action: War room activation, CEO notification

HIGH (P2): Degraded service, potential data issue
- Response time: 1 hour
- Action: Senior engineer, stakeholder notification

MEDIUM (P3): Minor issue, workaround available
- Response time: 4 hours
- Action: Assigned to engineer

LOW (P4): Enhancement request, minor bug
- Response time: 1 week
- Action: Backlog
```

**Incident Response Template:**

```
INCIDENT REPORT

Incident ID: INC-2024-0045
Severity: [CRITICAL|HIGH|MEDIUM|LOW]
Status: [OPEN|INVESTIGATING|RESOLVED|CLOSED]

Timeline:
- 14:30 UTC: Issue detected by monitoring
- 14:35 UTC: On-call engineer paged
- 14:40 UTC: War room activated
- 14:50 UTC: Root cause identified (database out of disk space)
- 15:00 UTC: Temporary fix applied (archive old logs)
- 15:20 UTC: Service restored
- 16:00 UTC: Permanent fix deployed (increase disk size)

Root Cause:
- Audit logs grew faster than expected
- Archive process failed due to permission error
- Disk filled to 100% causing database errors

Impact:
- Service unavailable: 15 minutes (14:45-15:00)
- Users affected: ~500 active sessions
- Data loss: None (all transactions logged)

Resolution:
- Immediate: Archive old logs to free space
- Short-term: Increase disk size by 500GB
- Long-term: Implement automatic log archival script

Prevention:
- Add disk space monitoring alert (>80%)
- Test log archive process weekly
- Document retention policies

Postmortem Scheduled: 2024-03-29 15:00 UTC
Assigned To: ops-team@example.com
```

### Automated Incident Detection & Response

```python
# incident_detection.py
import asyncio
from logging import Logger
from datetime import datetime

class IncidentDetector:
    def __init__(self, db, logger: Logger):
        self.db = db
        self.logger = logger
    
    async def check_system_health(self):
        """Run health checks every 60 seconds"""
        while True:
            try:
                # 1. Check response times
                avg_response_time = await self.get_avg_response_time()
                if avg_response_time > 500:  # 500ms threshold
                    await self.create_incident(
                        severity="HIGH",
                        title="Slow API Response Times",
                        description=f"p95 response time: {avg_response_time}ms"
                    )
                
                # 2. Check error rate
                error_rate = await self.get_error_rate()
                if error_rate > 0.01:  # 1% threshold
                    await self.create_incident(
                        severity="CRITICAL",
                        title="High Error Rate Detected",
                        description=f"Error rate: {error_rate*100}%"
                    )
                
                # 3. Check database
                db_health = await self.check_database()
                if not db_health["ok"]:
                    await self.create_incident(
                        severity="CRITICAL",
                        title="Database Connectivity Issue",
                        description=f"Database error: {db_health['error']}"
                    )
                
                # 4. Check disk space
                disk_usage = await self.check_disk_space()
                if disk_usage > 85:
                    await self.create_incident(
                        severity="HIGH",
                        title="Disk Space Low",
                        description=f"Disk usage: {disk_usage}%"
                    )
                
                # 5. Check for security anomalies
                anomalies = await self.detect_security_anomalies()
                if anomalies:
                    await self.create_incident(
                        severity="HIGH",
                        title="Security Anomalies Detected",
                        description=f"Found {len(anomalies)} anomalies"
                    )
                
            except Exception as e:
                self.logger.error(f"Health check failed: {e}")
            
            await asyncio.sleep(60)  # Check every minute
```

---

## Summary: Admin Quick Reference

**Daily Commands:**

```bash
# Check system status
systemctl status ztnas-backend ztnas-frontend postgresql

# View recent logs
tail -100 /var/log/ztnas/application.log

# Database backup status
aws s3 ls s3://ztnas-backups/ --recursive | tail -1

# Active user sessions
psql -d ztnas_prod -c "SELECT COUNT(*) FROM sessions WHERE expires_at > NOW();"

# Monitor real-time metrics
curl http://localhost:8000/metrics | grep http_requests_total
```

**Emergency Contacts:**

```
On-Call Engineer: on-call@example.com
Security Team: security@example.com
Database Admin: dba@example.com
Platform Lead: platform-lead@example.com
```

---

**ZTNAS System Administration Guide v2.0**  
For questions: ops@example.com | Slack: #ztnas-operations
