# ZTNAS Quick Start for University IT Administrators
## Setup & Management Guide for University Deployment

**For:** University IT Staff | **Audience:** Non-technical to technical  
**Duration:** 15-30 minutes to get started | **Version:** 2.0

---

## What You Need to Know (5 minutes)

### What is ZTNAS?
ZTNAS is a **secure access control system** for your entire university. It:
- ✅ Protects student and staff data
- ✅ Integrates with your university directory (Active Directory/LDAP)
- ✅ Automatically grants appropriate access based on role
- ✅ Logs all access for compliance
- ✅ Supports multi-factor authentication (MFA)

### Key Features Available Now
1. **Authentication:** Students/staff login with university credentials
2. **MFA:** Optional two-factor authentication via email or authenticator app
3. **Audit Logging:** Every action is tracked and stored
4. **Role-Based Access:** Different access for students, faculty, staff
5. **GDPR Compliance:** Students can request their data or delete accounts
6. **Security:** Protected against common attacks

---

## Immediate Setup (First 30 Minutes)

### Step 1: Get Access Information

**Ask your IT Director or Database Administrator for:**

```
□ PostgreSQL server hostname (e.g., db.university.edu or localhost:5432)
□ Database name (usually: ztnas_prod)
□ Database username (usually: ztnas_user)
□ Database password (keep this SECRET!)
□ LDAP/Active Directory server hostname
□ LDAP service account credentials
□ LDAP student group DN (distinguish name)
□ LDAP faculty group DN
□ LDAP staff group DN
```

### Step 2: Create Initial Admin Account

**Run this command on the server:**

```bash
# SSH into the server
ssh admin@ztnas.university.edu

# Create first admin user
cd /opt/ztnas
python -c "
from backend.models import User
from sqlalchemy.orm import Session
from backend.database import engine

db = Session(bind=engine)
admin = User(
    email='your.email@university.edu',
    name='Your Name',
    is_admin=True,
    is_active=True
)
db.add(admin)
db.commit()
print('✓ Admin account created')
"
```

### Step 3: First Login

**Access:** https://ztnas.university.edu/html/login.html

```
Email: your.email@university.edu
Password: (will be sent via email or provided separately)
```

**First Time:** You'll be prompted to set a new password

---

## Daily Operations

### Adding a New Student

**Option 1: Manual (for testing)**
```bash
# Login as admin → Admin Panel → Users → Add User
1. Click "Add User"
2. Enter student email (e.g., student123@university.edu)
3. Select role: "Student"
4. Click "Send Invitation"
5. Student receives email with setup link
```

**Option 2: Bulk Import (recommended)**
```bash
# Upload CSV file with student list

# CSV Format: users_import.csv
email,name,role,department
student001@university.edu,John Smith,student,Engineering
student002@university.edu,Jane Doe,student,Engineering
faculty001@university.edu,Dr. Smith,faculty,Engineering
```

**Then:**
```bash
# Login as admin → Admin Panel → Users → Bulk Import
# Upload CSV file
# System automatically sends invitations
```

### Removing Access for a User

```bash
# Option 1: Disable within 24 hours (reversible)
Admin Panel → Users → Search for user → Status → Inactive

# Option 2: Permanent deletion (after 30 days)
Admin Panel → Users → Search for user → Delete Account
# User gets 30-day notice before permanent deletion
```

### Checking Login History

```bash
# Admin Panel → Audit Logs → Search
Filter by: Date, User, Action

# View:
- Login attempts (successful and failed)
- Failed attempts from IPs
- MFA usage
- Password changes
```

---

## Troubleshooting

### "I forgot my password"

**For admins:**
```bash
# Backup LDAP entry in database
psql -U ztnas_user -d ztnas_prod -c \
  "UPDATE users SET password_reset_required=true WHERE email='admin@university.edu';"

# Or send reset link via email
# Admin Panel → Users → Send Password Reset
```

### "Student can't login"

**Check:**
1. Verify LDAP connection
   ```bash
   ldapwhoami -H ldap://ldap.university.edu -D "cn=student,ou=students,dc=university,dc=edu" -W
   ```

2. Check audit logs for errors
   ```bash
   Admin Panel → Audit Logs → Filter by username
   ```

3. Verify student account is active
   ```bash
   Admin Panel → Users → Search → Check status
   ```

### "MFA not working"

**Student should:**
1. Try email OTP (faster to set up)
2. Check spam folder for verification email
3. Use backup codes if device is lost

**Admin can help:**
```bash
Admin Panel → Users → Find user → Reset MFA
# User will need to re-setup their MFA next login
```

### "Something looks wrong - I need to check logs"

```bash
# Access server logs
ssh admin@ztnas.university.edu
tail -f /var/log/ztnas/application.log | grep ERROR

# Check database connectivity
psql -U ztnas_user -d ztnas_prod -c "SELECT NOW();"

# Check backup status
ls -lh /backups/ztnas_db_*.sql.gz | tail -5
```

---

## Monitoring (Daily 5-Minute Check)

### Health Check Command

```bash
#!/bin/bash
# Save as: health_check.sh
# Run daily

echo "ZTNAS Health Check - $(date)"
echo ""

# 1. Backend status
echo "1. Backend API:"
curl -s http://localhost:8000/api/v1/health | jq '.status'

# 2. Database
echo "2. Database:"
psql -U ztnas_user -d ztnas_prod -c "SELECT COUNT(*) as users FROM users;"

# 3. Disk space
echo "3. Disk usage:"
df -h / | tail -1

# 4. Recent errors
echo "4. Errors in last hour:"
grep ERROR /var/log/ztnas/application.log | wc -l

# 5. Backups
echo "5. Latest backup:"
ls -lh /backups/ztnas_db_*.sql.gz | tail -1 | awk '{print $9, $5, $6, $7, $8}'

echo ""
echo "Done!"
```

**Run:** `bash health_check.sh`

---

## Important Security Notes

### DO:
- ✅ Keep database password secure (use environment variables, not in files)
- ✅ Regularly backup database
- ✅ Review audit logs monthly
- ✅ Enable MFA for all admin accounts
- ✅ Update SSL certificates before expiry
- ✅ Create backup admin accounts (for emergencies)

### DON'T:
- ❌ Share database passwords in email or chat
- ❌ Store passwords in version control (git)
- ❌ Leave database publicly accessible
- ❌ Delete audit logs (keep 90+ days)
- ❌ Use the same password for multiple systems
- ❌ Ignore security alerts

---

## Useful Commands Cheat Sheet

```bash
# Start/stop services
sudo systemctl start ztnas-backend
sudo systemctl stop ztnas-backend
sudo systemctl status ztnas-backend

# Check if backend is running
curl http://localhost:8000/api/v1/health

# View recent errors
tail -50 /var/log/ztnas/application.log | grep ERROR

# Backup database manually
pg_dump -U ztnas_user ztnas_prod | gzip > /backups/ztnas_db_manual.sql.gz

# Restore database (DANGER - loses current data!)
gunzip -c /backups/ztnas_db_*.sql.gz | psql -U ztnas_user ztnas_prod

# Reset a user's password
psql -U ztnas_user -d ztnas_prod -c \
  "UPDATE users SET password_reset_required=true WHERE email='user@university.edu';"

# Count active users
psql -U ztnas_user -d ztnas_prod -c "SELECT COUNT(*) FROM users WHERE is_active=true;"

# View failed logins last 24 hours
psql -U ztnas_user -d ztnas_prod -c \
  "SELECT user_id, COUNT(*) as attempts FROM audit_logs WHERE action='LOGIN_FAILED' AND created_at > NOW() - INTERVAL 24 HOUR GROUP BY user_id ORDER BY attempts DESC;"
```

---

## Support Contacts

**Issues:** Document the problem and check these first:
1. Logs: `/var/log/ztnas/application.log`
2. Audit: `Admin Panel → Audit Logs`
3. Health: `http://ztnas.university.edu/api/v1/health`

**Escalation:**
```
Level 1 - Your IT Team Lead
Level 2 - University IT Director
Level 3 - ZTNAS Support (if applicable)
```

---

## Monthly Maintenance Tasks

**First Monday of each month:**
- [ ] Review audit logs for anomalies
- [ ] Check database size growth
- [ ] Verify backups completed successfully
- [ ] Update SSL certificates if needed (check expiry)
- [ ] Review user access - remove inactive users
- [ ] Security: Check for any failed login patterns

**Quarterly (every 3 months):**
- [ ] Full security audit
- [ ] Performance baseline check
- [ ] Disaster recovery test (restore from backup)
- [ ] LDAP synchronization verification

---

## FAQ

**Q: Can students reset their own passwords?**  
A: Yes! Login page → "Forgot Password?" → Verify via email → Set new password

**Q: What if a student loses their MFA device?**  
A: They can use backup codes (saved during setup) or contact support to reset MFA

**Q: How long are logs kept?**  
A: Audit logs kept for 90+ days minimum. Older logs archived annually.

**Q: Can students see each other's data?**  
A: No. Each student only sees their own profile and allowed resources.

**Q: What happens when a student graduates?**  
A: Admin sets status to "inactive". Account kept for 1 year then archived.

**Q: Is there an API for integrations?**  
A: Yes! 40+ endpoints available. See API documentation at: `/docs`

---

## Success Indicators

✓ System is working well when:
- All 50,000+ students can login
- Average login time <1 second
- Backup completes nightly without errors
- Zero audit log anomalies
- Admin reports are current and accurate
- Support tickets <5 per week

---

**ZTNAS University Administrator Quick Start**  
Version: 2.0 | Updated: 2024-03-28 | Status: Ready for Use

**Next:** Ask your IT team to start with Step 1 of HIGHER_ED_IMPLEMENTATION_ROADMAP.md
