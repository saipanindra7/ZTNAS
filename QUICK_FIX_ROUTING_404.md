# QUICK FIX: Routing 404 Errors

## 🔴 The Problem
```
GET http://localhost:5500/login.html → 404 (File not found)
```

## ✅ Why It's Happening
You're likely running an **old version** of the server that doesn't have the routing fix.

## 🚀 IMMEDIATE FIX (3 Steps)

### Step 1: CLOSE the Current Server
```
In your terminal, press: Ctrl+C
Wait 3-5 seconds for port to release
```

### Step 2: VERIFY You're Using New Server
```bash
# Make SURE you're running serve_simple.py (not serve.py)
cd d:\projects\ztnas\frontend

# Check the file exists with latest routing fix
cat serve_simple.py | findstr "translate_path"
```

Should show the `translate_path` method with routing logic.

### Step 3: START The Updated Server
**Windows (Recommended):**
```batch
# Double-click this file:
start-server.bat

# OR run manually:
python serve_simple.py
```

**Linux/Mac:**
```bash
python serve_simple.py
```

### Step 4: TEST
Open browser and go to: **http://localhost:5500/login.html**

You should see:
- ✅ Login form loads
- ✅ Browser console shows NO CSP warnings
- ✅ Server logs show: `GET /login.html HTTP/1.1 → 200` (not 404)

---

## 📋 What's Fixed

### Fix #1: CSP Header
**BEFORE:**
```
Content-Security-Policy: ... connect-src 'self' ... https://
                                                       ^^^^^^ Invalid!
```

**AFTER:**
```
Content-Security-Policy: ... connect-src 'self' ... https:
                                                    ^^^^^ Correct!
```

**Result:** ✅ No more CSP warning

### Fix #2: Routing Logic
**Added to serve_simple.py:**
```python
def translate_path(self, path):
    if path == '/' or path == '':
        path = '/html/index.html'  # Root goes to landing page
    
    filepath = super().translate_path(path)
    
    # If HTML file not found, check /html/ subdirectory
    if not os.path.exists(filepath) and path.endswith('.html'):
        filename = os.path.basename(path)
        html_path = super().translate_path('/html/' + filename)
        if os.path.exists(html_path):
            return html_path  # Found in /html/!
    
    return filepath
```

**Result:** ✅ `/login.html` → `/html/login.html` (200 OK)

---

## 🧪 Verification Checklist

After restarting server:

- [ ] No errors in terminal when starting
- [ ] Terminal shows "🚀 Server is running"
- [ ] Open http://localhost:5500
- [ ] Landing page loads instantly
- [ ] Click "Sign In" button
- [ ] Login page loads (NOT 404)
- [ ] Click "Get Started" button
- [ ] Registration page loads (NOT 404)
- [ ] Browser console has NO warnings (F12)
- [ ] Server log shows all 200 responses

---

## 📍 Key Files

Always use these:
- ✅ `frontend/serve_simple.py` ← Main production server
- ✅ `frontend/start-server.bat` ← Windows launcher

Never use:
- ❌ `frontend/serve.py` ← Old version (has compression issues)

---

## 🆘 If It STILL Doesn't Work

### Check 1: Is old server still running?
```bash
# Look for processes using port 5500
netstat -ano | findstr ":5500"

# If found, kill it (you may need admin)
taskkill /PID <PID> /F
```

### Check 2: Restart completely
1. Close all terminals
2. Close all Chrome/Firefox instances
3. Wait 10 seconds
4. Open fresh terminal
5. Run: `python serve_simple.py`
6. Open fresh browser window
7. Go to: http://localhost:5500

### Check 3: Check server version
Make sure `serve_simple.py` has the routing logic:
```bash
cd frontend
python -c "
import serve_simple
import inspect
source = inspect.getsource(serve_simple.Handler.translate_path)
print('✓ Routing found!' if '/html/' in source else '✗ Routing missing!')
"
```

---

## 🎯 Expected Output

### Server Startup
```
============================================================
  ZTNAS Frontend Server (Production-Ready)
============================================================

✓ Dashboard: http://localhost:5500

Features:
  ✓ Automatic index.html serving
  ✓ Security headers enabled
  ✓ Directory listing blocked

Press Ctrl+C to stop
============================================================

🚀 Server is running - open http://localhost:5500

2026-03-29 10:15:23 - INFO - Server running on port 5500
```

### When You Access Pages
```
2026-03-29 10:15:30 - INFO - "GET / HTTP/1.1" 200 ←Root goes to index.html
2026-03-29 10:15:32 - INFO - Routing /login.html → /html/login.html
2026-03-29 10:15:32 - INFO - "GET /login.html HTTP/1.1" 200 ← SUCCESS!
2026-03-29 10:15:35 - INFO - Routing /register.html → /html/register.html
2026-03-29 10:15:35 - INFO - "GET /register.html HTTP/1.1" 200 ← SUCCESS!
```

---

## ✨ Summary

```
Old Server          New Server
-----------         ----------
❌ 404 on /login    ✅ Routes to /html/login.html
❌ 404 on /register ✅ Routes to /html/register.html
❌ CSP warning      ✅ Fixed header
❌ Complex code     ✅ Simple & stable
```

**Action Required:** Restart server with `serve_simple.py`

---
