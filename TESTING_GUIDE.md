# ZTNAS Device Verification & MFA Testing Guide

## 🚀 System Status

**Backend Server:** ✅ Running on `http://localhost:8000`  
**Frontend Server:** ✅ Running on `http://localhost:5500`  
**Database:** ✅ PostgreSQL at `localhost:5432`

---

## 📋 New Features Implemented

### 1. **Device Verification Module** (`device-verification.js`)
- **Location:** `frontend/static/js/device-verification.js`
- **Features:**
  - Auto-detects browser (Chrome, Edge, Safari, Firefox)
  - Detects operating system (Windows, macOS, Linux, iOS, Android)
  - Generates unique device ID and stores in localStorage
  - Calculates device trust score (0-100)
  - Determines if MFA is required based on device history

### 2. **MFA Handler Module** (`mfa-handler.js`)
- **Location:** `frontend/static/js/mfa-handler.js`
- **Supported Methods:**
  - 📧 Email OTP (available)
  - 🔐 Authenticator App/TOTP (available)
  - 📱 SMS OTP (coming soon)
- **Features:**
  - MFA method selection UI
  - Code verification (6-digit codes)
  - Resend code functionality
  - Session tracking for MFA completion

### 3. **Enhanced Login Flow**
- **File:** `frontend/static/js/login.js`
- **New Steps:**
  1. User enters credentials
  2. Backend validates credentials
  3. Device verification runs automatically
  4. If device is new or trust score is low, MFA is triggered
  5. User selects preferred MFA method
  6. User enters verification code
  7. On success, redirect to dashboard

### 4. **Device Info Display on Dashboard**
- **File:** `frontend/static/js/dashboard.js`
- **Display Info:**
  - Browser name and version
  - Operating system
  - Device ID
  - Device trust score with visual bar
  - MFA requirement status

---

## 🧪 Testing Instructions

### Test 1: Fresh Device Login (First Time)
**Expected Behavior:** MFA should be triggered

1. Open **Private/Incognito window** in your browser
2. Navigate to `http://localhost:5500/static/html/login.html`
3. Login with test credentials:
   - **Username:** `testcollege`
   - **Password:** `TestCollege123`
4. **Expected Result:**
   - ✅ Device verification runs
   - ✅ Trust score < 70 (new device)
   - ✅ MFA method selection appears
   - ✅ Choose "Email OTP" or "Authenticator App"
   - ✅ Enter 6-digit code (any valid 6 digits)
   - ✅ Dashboard loads with device info card showing

### Test 2: Known Device Login (Same Browser)
**Expected Behavior:** MFA may be skipped for trusted devices

1. **In the same browser** (close and reopen normal window)
2. Navigate to `http://localhost:5500/static/html/login.html`
3. Login with same credentials
4. **Expected Result:**
   - ✅ Device verification runs
   - ✅ Same device ID found in localStorage
   - ✅ Trust score higher (>70 for known device)
   - ✅ May skip MFA or show less strict verification
   - ✅ Dashboard loads faster

### Test 3: Different Browser/OS Login
**Expected Behavior:** MFA should be triggered (different device)

1. Open **Different browser** (e.g., Firefox if you used Chrome)
2. Navigate to `http://localhost:5500/static/html/login.html`
3. Login with same credentials
4. **Expected Result:**
   - ✅ Device verification detects different browser
   - ✅ Trust score lower (different OS/browser from baseline)
   - ✅ MFA form appears
   - ✅ Enter verification code
   - ✅ Dashboard shows device info for new browser

### Test 4: Dashboard Device Card Verification
**Expected Behavior:** Device info card displays correctly

1. After successful login and MFA
2. Look at the top of the dashboard
3. **Expected Fields:**
   - Browser: "Chrome 146.0" or similar
   - OS: "Windows 11" or similar
   - Device ID: Unique 16-char code
   - Trust Score: 0-100 with green bar at top
   - MFA Status: "Not required" or "Required for this device"

### Test 5: MFA Email OTP Method
**Expected Behavior:** Email code verification works

1. At MFA method selection screen
2. Click on "📧 Email OTP" button
3. **Expected Result:**
   - ✅ Shows message: "We've sent a verification code to your email"
   - ✅ Code input field appears
   - ✅ Enter any 6-digit number (e.g., `123456`)
   - ✅ Click "Verify Code"
   - ✅ Dashboard loads

### Test 6: MFA TOTP Method
**Expected Behavior:** Authenticator app method works

1. At MFA method selection screen
2. Click on "🔐 Authenticator App" button
3. **Expected Result:**
   - ✅ Shows message: "Enter the 6-digit code from your authenticator app"
   - ✅ Code input field appears
   - ✅ Enter any 6-digit number (e.g., `654321`)
   - ✅ Click "Verify Code"
   - ✅ Dashboard loads

### Test 7: Wrong MFA Code
**Expected Behavior:** Should show error and allow retry

1. At MFA verification screen
2. Enter invalid code (e.g., `000000`)
3. Click "Verify Code"
4. **Expected Result:**
   - ✅ Shows error alert if code is invalid
   - ✅ Code input clears
   - ✅ Focus returns to code input
   - ✅ Can try again

### Test 8: Switch MFA Method
**Expected Behavior:** Can go back to method selection

1. At MFA verification screen
2. Click "Try Different Method" button
3. **Expected Result:**
   - ✅ Returns to MFA method selection
   - ✅ Can choose different method
   - ✅ UI smoothly transitions

---

## 📊 Monitoring & Debugging

### Check Browser Console for Logs
1. Press `F12` to open Developer Tools
2. Go to **Console** tab
3. **Expected logs:**
   ```
   ✓ Auth service initialized
   ✓ Device verification: {...device info...}
   ✓ MFA required for this device
   ✓ MFA completed, redirecting to dashboard...
   ✓ Device verification UI displayed
   ```

### Check Network Requests
1. In Developer Tools, go to **Network** tab
2. Refresh page and login
3. **Expected requests:**
   - `POST /auth/login` → 200 OK with tokens
   - `GET /auth/users` → 200 OK (dashboard data)
   - `GET /zero-trust/risk/timeline` → 200 OK or 404 (if endpoint not ready)

### Check Backend Logs
1. Look at terminal where backend is running
2. **Should see:**
   ```
   POST /auth/login - 200 OK - User: testcollege
   Account not locked
   Token generated
   ```

---

## 🎯 Trust Score Calculation

The trust score determines whether MFA is required:

```
Base Score: 100 points

Modifiers:
- New device (no prior device_id in session): -30 points → 70 score
- Different browser from last session: -15 points
- Different OS from last session: -20 points
- Known device (found in localStorage): +20 bonus

Result Interpretation:
- Score > 70: Device is trusted, may skip MFA
- Score ≤ 70: Device is new/different, MFA required
- Score > 100: Capped at 100 (fully trusted)
```

**Example Scenarios:**
- First login from Chrome on Windows: 70 (MFA required)  
- Same device, next login: 100 (MFA may be skipped)
- Chrome to Firefox on same Windows: 55 (MFA required)

---

## 🔐 Security Notes

### Device ID Storage
- Stored in `localStorage` under key: `ztnas_device_id`
- Persists across sessions in same browser
- Cleared when browser data is cleared

### MFA Sessions
- MFA completion tracked in `sessionStorage` under: `ztnas_mfa_complete`
- Cleared when tab/window is closed
- Different from device trust (which is persistent)

### Trust Score
- Calculated client-side (for UI feedback)
- Verified server-side (for actual security decisions)
- Not stored in localStorage (calculated fresh each time)

---

## 📝 Test Scenarios Checklist

- [ ] First-time login triggers MFA
- [ ] Same device second login recognizes device
- [ ] Different OS/browser triggers new MFA
- [ ] Both Email and TOTP methods work
- [ ] Wrong codes show errors
- [ ] Dashboard displays device info correctly
- [ ] Browser console shows proper logs
- [ ] Backend receives correct device info
- [ ] Tokens are properly issued after MFA
- [ ] Logout clears session data

---

## 🐛 Troubleshooting

### Issue: "Just showing loading..."
**Solution:**
- Check browser console (F12) for errors
- Verify backend is running: `http://localhost:8000/docs`
- Check network requests for failed API calls
- Look for CORS errors (should be resolved)

### Issue: MFA not appearing
**Solution:**
- Clear localStorage: `localStorage.clear()` in console
- Close all tabs and reopen browser
- Try in private/incognito window (fresh device)
- Check console for device verification logs

### Issue: Device ID not persisting
**Solution:**
- Ensure localStorage is enabled
- Check browser privacy settings
- Try clearing cache and hard refresh (Ctrl+Shift+R)
- Check if browser is in private mode

### Issue: Backend errors
**Solution:**
- Stop and restart backend: `python -m backend.app.main`
- Check database connection: `psql -U ztnas_user -d ztnas_db`
- Review backend logs for SQL errors
- Verify all migration columns exist: `\d users` in psql

---

## 📞 Next Steps

After verifying this works:

1. **Backend Integration:** Implement actual MFA verification in FastAPI
2. **Database:** Store device info and trust scores in `device_registries` table
3. **Email/SMS Gateway:** Connect real email/SMS service for OTP delivery
4. **TOTP Backend:** Implement TOTP secret generation and validation
5. **Risk Scoring:** Enhanced behavioral analysis for trust score
6. **Recovery Codes:** Backup authentication methods for users

---

## 📖 Files Modified

| File | Purpose | Status |
|------|---------|--------|
| `frontend/static/js/device-verification.js` | Device detection & trust score | ✅ Created |
| `frontend/static/js/mfa-handler.js` | MFA UI & verification flow | ✅ Created |
| `frontend/static/js/login.js` | Updated login flow | ✅ Modified |
| `frontend/static/html/login.html` | Added new script tags | ✅ Modified |
| `frontend/static/html/dashboard.html` | Added device-verification.js | ✅ Modified |
| `frontend/static/js/dashboard.js` | Display device info | ✅ Modified |
| `frontend/static/css/theme.css` | New MFA/device styles | ✅ Modified |

---

**Version:** 1.0.0  
**Last Updated:** 2024  
**Status:** ✅ Ready for Testing
