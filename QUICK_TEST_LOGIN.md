# Quick Start - Test the Fixed Login Flow

## Prerequisites

✅ Backend running on `http://localhost:8000`  
✅ Frontend server running on `http://localhost:5500`  
✅ Database seeded with test users  

---

## 🚀 30-Second Quick Test

### 1. Open Login Page
```
http://localhost:5500/login.html
```

### 2. Click "Demo Login" Button
- Form auto-fills with: `testcollege` / `TestCollege123`
- Clicks login automatically

### 3. Verify Dashboard Loads
- Should see "Welcome back" message
- Role-based dashboard appears
- No error pages

**Status:** ✅ PASS if you reach dashboard

---

## 📝 Complete Test Walkthrough (5 Minutes)

### Test #1: New Registration

```
URL: http://localhost:5500/register.html

Fields:
  Full Name:       Alice Smith
  Email:           alice@college.edu
  Username:        alice_smith
  Password:        SecurePass123!
  Confirm Password: SecurePass123!
  ✓ Terms of Service

Click: "Create Account"

✅ Expected: Success message → Redirects to login
```

### Test #2: First-Time Login

```
URL: http://localhost:5500/login.html

Fields:
  Username: alice_smith
  Password: SecurePass123!

Click: "Sign In"

✅ Expected: Logs in → See Alice's dashboard
```

### Test #3: Verify Authentication Persists

```
In browser, press: F5 (Refresh)

✅ Expected: Dashboard still visible (not redirected to login)
            Same user, same data
```

### Test #4: Logout

```
Click: "Logout" button (top-right of dashboard)

Confirm: "Yes" in dialog

✅ Expected: Redirect to login.html
            Dashboard is gone
```

### Test #5: Try Accessing Dashboard While Logged Out

```
URL: http://localhost:5500/dashboard.html

✅ Expected: Redirects to login.html immediately
            Cannot bypass authentication
```

### Test #6: Demo Account

```
URL: http://localhost:5500/login.html

Click: "Demo Login"

✅ Expected: Automatically fills testcollege / TestCollege123
            Logs in successfully
            Shows testcollege's dashboard
```

### Test #7: Wrong Password

```
URL: http://localhost:5500/login.html

Fields:
  Username: testcollege
  Password: WrongPassword123!

Click: "Sign In"

✅ Expected: Error message shows
            Stays on login page
            Can retry
```

### Test #8: Console Verification

```
Open: Browser Console (F12 → Console)

Should see logs like:
  "✓ Login page initialized"
  "Auth token found: true"
  "Current user: {id: ..., username: ...}"

No red errors ✅
```

---

## 🔍 Troubleshooting

### "404 Not Found" on login.html

**Problem:** File not found  
**Solution:** 
- Check URL: `http://localhost:5500/login.html` (not `/frontend/...`)
- Verify frontend server is running
- Check server routing points to `/html/` subdirectory

### "Network error" when trying to login

**Problem:** Cannot connect to backend  
**Solution:**
- Is backend on `http://localhost:8000`?
- Run: `python -m app.main` from backend directory
- Check for CORS errors in browser console

### "Account created successfully" but then "103 times out"

**Problem:** Page stuck after registration  
**Solution:**
- Close and reopen register tab
- Manually go to login.html: `http://localhost:5500/login.html`
- Try logging in with new credentials

### "Welcome back!" but dashboard shows "Loading..."

**Problem:** Data not loading  
**Solution:**
- Open browser console (F12)
- Check network tab for failed requests
- Verify user has roles assigned in backend database
- Check backend `/api/v1/dashboard` endpoint exists

---

## ✅ Checklist Before Full Deployment

- [ ] New user registration works
- [ ] Login works with new user
- [ ] Demo login works  
- [ ] Dashboard loads after login
- [ ] Refresh page keeps user logged in
- [ ] Logout works and clears data
- [ ] Cannot access dashboard while logged out
- [ ] Wrong password shows error
- [ ] Browser console has no red errors
- [ ] All role dashboards (admin, hod, faculty, student) work
- [ ] API calls from dashboard work (no 401 errors)

---

## 📊 File Structure Verification

```
frontend/
├── static/
│   ├── html/
│   │   ├── login.html          ✅ Updated ✅
│   │   ├── register.html       ✅ Updated ✅
│   │   ├── dashboard.html      ✅ Updated ✅
│   │   ├── mfa.html            ✅ Updated ✅
│   │   └── index.html          ✅ OK
│   └── js/
│       ├── auth.js             ✅ NEW (240 lines)
│       ├── login.js            ✅ Rewritten
│       ├── register.js         ✅ Rewritten
│       ├── dashboard.js        ✅ Updated
│       └── mfa.js              ✅ Updated
```

---

## 🧪 API Endpoints Used

| Endpoint | Method | Used By | Status |
|----------|--------|---------|--------|
| `/auth/login` | POST | login.js | ✅ Working |
| `/auth/register` | POST | register.js | ✅ Working |
| `/auth/me` | GET | auth.js | ✅ Working |
| `/auth/refresh` | POST | auth.js | ✅ Working |
| `/dashboard` | GET | dashboard.js | ✅ Working |

---

## 💡 Key Improvements

✅ **Single Auth Service**: All auth in one place (auth.js)  
✅ **Better Error Messages**: User-friendly, not technical  
✅ **Token Refresh**: Automatic token renewal  
✅ **Persistent Login**: Survives page refresh  
✅ **Role-Based Views**: Different dashboards per role  
✅ **401 Handling**: Auto-logout on invalid token  
✅ **Password Strength**: Visual indicator during registration  
✅ **Form Validation**: Client + server validation  
✅ **No Token Leakage**: Secure localStorage keys  

---

## 🎓 Test Scenarios

Choose your comfort level:

### Level 1️⃣ - Basic (5 min)
- Click demo login
- See dashboard
- Logout

### Level 2️⃣ - Intermediate (10 min)
- Register new account
- Login with new account
- Refresh page
- Logout

### Level 3️⃣ - Advanced (20 min)
- Register multiple users (admin, student, etc.)
- Test each role's dashboard
- Test wrong passwords
- Test account lockout (3 failures)
- Check browser console for errors
- Test API calls from dashboard

### Level 4️⃣ - Expert (30 min)
- Test token expiry (wait 15 minutes)
- Test refresh token usage
- Manually clear tokens, try accessing dashboard
- Check all network requests
- Verify CORS headers
- Test with DevTools network throttling

---

## 📞 Quick Help

| Issue | Command |
|-------|---------|
| Check if backend is running | `curl http://localhost:8000/api/v1/health` |
| Clear all auth data | Open console: `localStorage.clear()` |
| Check stored token | `localStorage.getItem('ztnas_token')` |
| Check current user | `localStorage.getItem('ztnas_user')` |
| Restart frontend server | Stop (Ctrl+C) and: `python serve_simple.py` |
| View backend logs | Check terminal where backend started |

---

**Last Updated:** March 29, 2026  
**Version:** 2.0 - Quick Test Guide  
**Status:** Ready to Test ✅
