# ZTNAS Quick Start & Testing Guide

## ⚡ Quick Start (Next 2 Minutes)

### Step 1: Verify Servers Are Running
```bash
# Check frontend on port 5500
http://localhost:5500

# Check backend on port 8000
http://localhost:8000/docs
```

Both should show activity. If not:
```bash
# Terminal 1 - Backend
cd d:\projects\ztnas\backend
python -m uvicorn app.main:app --reload --port 8000

# Terminal 2 - Frontend
cd d:\projects\ztnas\frontend
python -m http.server 5500
```

---

## 🎯 Quick Test (5 Minutes)

### Test 1: Login with Fresh Device
```
1. Open PRIVATE WINDOW (Ctrl+Shift+P in Chrome/Edge)
   - Private window = clean device, no localStorage

2. Visit: http://localhost:5500/static/html/login.html

3. Enter test credentials:
   Username: testcollege
   Password: TestCollege123

4. EXPECTED: Device verification → MFA challenge → Dashboard
```

### Test 2: Same Device Second Login
```
1. STILL IN SAME PRIVATE WINDOW (don't close)

2. Logout (button in dashboard)

3. Login again with same credentials

4. EXPECTED: Faster login, device might be recognized
```

### Test 3: Different Device (New Window)
```
1. Open NORMAL WINDOW (not private)

2. Visit: http://localhost:5500/static/html/login.html

3. Login with same credentials

4. EXPECTED: Different device detected, may ask MFA
```

---

## ✅ What to Check

### In Browser

**Check 1: Device Card on Dashboard**
```
After logging in, look for:
┌────────────────────────────┐
│ 🔐 Device Verification     │
│ Browser: Chrome 146.0      │ ✅ Shows correct browser
│ OS: Windows 11             │ ✅ Shows correct OS  
│ Device ID: ztnas_device... │ ✅ Unique ID shown
│ Trust Score: 80%           │ ✅ Score displayed
│ MFA: Not required          │ ✅ Status shown
└────────────────────────────┘
```

**Check 2: Browser Console (F12)**
```
Look for these logs:
✓ Auth service initialized
✓ Device verification: {...}
✓ Trust score calculated: 70-100
✓ Device verified, displaying UI
✓ Dashboard data loaded
```

**Check 3: Dashboard Data Showing**
```
Verify you can see:
✅ Active Users count
✅ MFA Enrolled count
✅ Risk Events count
✅ Anomalies count
✅ Charts loading
✅ Recent logs table
✅ Buttons clickable
```

### In Browser Console (F12 → Console Tab)

Run these commands to verify:

```javascript
// Check device verification module
typeof deviceVerification !== 'undefined'  // Should print: true

// Check MFA module  
typeof mfaHandler !== 'undefined'  // Should print: true

// Check device ID
localStorage.getItem('ztnas_device_id')  // Should show UUID

// Check auth
auth.isAuthenticated()  // Should print: true

// Check device info
deviceVerification.verify().then(d => console.log(d))  
// Should show browser, OS, trust_score, requires_mfa
```

---

## 🔍 Common Issues & Fixes

### Issue: "Dashboard just shows loading"

**Check:**
```
F12 → Network tab
- Look for failed requests (red)
- Check backend logs
```

**Fix:**
```
1. Restart backend server
   cd d:\projects\ztnas\backend
   python -m uvicorn app.main:app --reload --port 8000

2. Restart frontend server
   cd d:\projects\ztnas\frontend
   python -m http.server 5500

3. Hard refresh browser: Ctrl+Shift+R

4. Check console for errors: F12 → Console
```

### Issue: "MFA not showing"

**Check:**
```
- Private window? (ensures fresh device)
- Console showing device detection?
- Trust score < 70?
```

**Fix:**
```
1. Clear localStorage: 
   F12 → Console → localStorage.clear()

2. Close all tabs

3. Open fresh private window

4. Login again
```

### Issue: "Backend 404 or connection error"

**Fix:**
```
1. Check backend is running:
   http://localhost:8000/docs

2. Should see Swagger docs

3. If not, start backend:
   cd d:\projects\ztnas\backend
   python -m uvicorn app.main:app --reload --port 8000
```

### Issue: "Device ID changing every time"

**This is normal if:**
- Using private/incognito window → localStorage cleared
- Browser cookies disabled
- Clearing cache each time

**This is a problem if:**
- Normal window but ID changing
- Fix: Check if localStorage is available
  ```javascript
  F12 → Console:
  localStorage.setItem('test', '1')
  localStorage.getItem('test')  // Should print: 1
  ```

---

## 📋 Feature Verification Checklist

Print this and check off each item:

```
DEVICE DETECTION
□ Browser detected (Chrome, Edge, Safari, Firefox)
□ OS detected (Windows, macOS, Linux)
□ Device ID generated (unique per browser)
□ Device ID persists after logout

TRUST SCORE
□ Score calculated (0-100)
□ New device score ≤ 70 (triggers MFA)
□ Same device score > 70 (skips MFA)
□ Score displayed on dashboard

MFA FLOW
□ MFA selection appears on new device
□ Can select Email OTP method
□ Can select Authenticator App method
□ Code entry field appears (6 digits)
□ Can verify with any 6-digit code
□ Invalid code shows error
□ Resend code button works
□ Can switch methods without error
□ Successful code redirects to dashboard

DASHBOARD
□ Device card displays at top
□ Shows browser version
□ Shows OS name
□ Shows trust score %
□ Shows device ID
□ Shows MFA requirement status
□ Dashboard data loads (no more "loading...")
□ Buttons clickable
□ All navigation works
□ Profile page shows info
□ Logout button works

SECURITY
□ Tokens issued after login
□ Tokens clear after logout
□ Session data stored correctly
□ MFA completion tracked
□ Device ID persisted in index
```

---

## 🎬 Screen Recording Verification

For documentation, record this sequence:

```
1. Open private browser window (0:00)
   - Shows fresh device state

2. Navigate to login page (0:05)
   - Type credentials
   - Show login form

3. Click Sign In (0:10)
   - Device verification running (in console)
   - Loading message "Verifying device..."

4. MFA selection appears (0:15)
   - Show Email and Authenticator options
   - Click Email OTP

5. Code entry screen (0:20)
   - Enter 6-digit code
   - Click Verify

6. Dashboard loads (0:25)
   - Scroll to see device verification card
   - Highlight browser, OS, trust score
   - Scroll to show all dashboard data

7. Show Console logs (0:30)
   - F12 → Console
   - Show device verification logs

8. Run verification commands (0:40)
   - deviceVerification.verify()
   - Show device info
   - Show trust score

9. Logout and login again (0:50)
   - Same device recognized
   - Faster login process
   - May skip MFA

10. Open different browser (1:00)
    - Show different browser detected
    - May trigger MFA again
    - Shows different browser/OS
```

**Total Time:** ~1 minute showing full flow

---

## 🚀 Production Deployment Checklist

Before going live:

```
FRONTEND
□ All scripts included in HTML
□ CSS fully loaded (no layout issues)
□ No console errors
□ Responsive on mobile
□ Works in all browsers (Chrome, Firefox, Safari, Edge)
□ HTTPS enabled (if required)
□ Assets cached properly

BACKEND
□ Database migrations applied
□ All endpoints return 200/203/404 (not 500)
□ Authentication working
□ Rate limiting enforced
□ Audit logs being written
□ CORS configured for frontend domain

INTEGRATION
□ Frontend → Backend communication works
□ Device info sent with requests
□ MFA codes validated server-side
□ Trust scores verified server-side
□ No sensitive data exposed in logs

SECURITY
□ Passwords hashed (not in logs)
□ Tokens secure (can't be forged)
□ Device IDs random (can't be guessed)
□ MFA codes rotate (can't be reused)
□ Rate limiting prevents brute force
□ HTTPS redirects HTTP traffic

OPERATIONS
□ Error messages don't expose internals
□ Graceful handling of backend down
□ Automatic fallbacks
□ Health check endpoints working
□ Monitoring/alerts configured
□ Backup strategy in place
```

---

## 📞 Support & Debugging

### Get Help

**Backend Issues:**
```bash
# Check backend is running
curl http://localhost:8000/docs

# View backend logs
# Watch terminal where backend started

# Test backend directly
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"testcollege","password":"TestCollege123"}'
```

**Frontend Issues:**
```bash
# Check frontend is running  
curl http://localhost:5500/static/html/login.html

# Check browser console (F12 → Console tab)
# Check network tab for failed requests

# Test device verification in console
deviceVerification.verify().then(console.log)
```

**Database Issues:**
```bash
# Connect to PostgreSQL
psql -U ztnas_user -d ztnas_db

# Check users table
SELECT id, username, email, is_active FROM users;

# Check audit logs
SELECT * FROM audit_logs ORDER BY created_at DESC LIMIT 10;
```

---

## 📚 Additional Resources

- **Testing Guide:** See `TESTING_GUIDE.md`
- **Implementation Details:** See `IMPLEMENTATION_SUMMARY.md`
- **Backend API Docs:** `http://localhost:8000/docs`
- **Database Schema:** `backend/app/models/__init__.py`
- **Frontend Code:** `frontend/static/js/`

---

## ✨ Success Indicators

You'll know everything is working when:

1. ✅ Private window login → Device card appears → Trust score shown
2. ✅ Logout and login → Same device → May skip MFA
3. ✅ Different browser → Different device detected → May ask MFA
4. ✅ Dashboard shows users, logs, policies (no more "loading...")
5. ✅ All buttons clickable and responsive
6. ✅ Console shows device verification logs (no errors)
7. ✅ Browser, OS, Device ID, Trust Score all displaying
8. ✅ MFA methods available and working

When all 8 are ✅, **you're production-ready!**

---

**Status:** Ready to Test! 🚀  
**Expected Duration:** 5-10 minutes  
**Difficulty:** Easy (just navigate & observe)

Good luck! 🎉
