# ZTNAS Frontend - Production-Ready College Dashboard

## Overview

This is the frontend for the **ZTNAS (Zero Trust Network Access System)** college management dashboard. It provides a sophisticated, role-based interface for managing college network access and security policies.

## ⚡ Quick Start

### Windows Users
```batch
Double-click: start-server.bat
```

Then open your browser: **http://localhost:5500**

### Linux/Mac Users
```bash
python serve_simple.py
```

Then open: **http://localhost:5500**

## 🔧 If You Have Issues

### Navigation Returns 404 Errors
- **Issue:** Clicking "Login" or "Register" shows 404
- **Fix:** See [NAVIGATION_ROUTING_FIXED.md](../NAVIGATION_ROUTING_FIXED.md)
- **Solution:** Server now automatically routes `login.html` → `/html/login.html`

### Page Keeps Refreshing
- **Issue:** Infinite refresh loop or connection drops
- **Fix:** See [SERVER_FIX_GUIDE.md](../SERVER_FIX_GUIDE.md)
- **Solution:** Updated to simplified stable server

## 🎯 What's Fixed

The old Python HTTP server showed a directory listing instead of the application. We've fixed this with a **production-grade server** that:

✅ Automatically serves `index.html` (no more directory listings)  
✅ Adds security headers (X-Frame-Options, CSP, etc.)  
✅ Enables CORS for API calls to backend  
✅ Supports gzip compression  
✅ Provides proper logging  
✅ Prevents directory traversal attacks  
✅ Handles SPA routing correctly  

## 📁 Directory Structure

```
frontend/
├── serve.py                 # Production-ready HTTP server (Python)
├── start-server.bat        # Windows startup script
├── verify_server.py        # Server verification test
├── index.html              # Root landing page (alt)
├── nginx.conf              # Production Nginx configuration
├── static/
│   ├── html/               # HTML pages
│   │   ├── index.html      # Landing page
│   │   ├── login.html      # Login form
│   │   ├── register.html   # Registration form
│   │   ├── dashboard.html  # College dashboard (authenticated)
│   │   └── mfa.html        # MFA enrollment
│   │
│   ├── css/                # Stylesheets
│   │   ├── style.css       # Base styles
│   │   ├── dashboard.css   # Dashboard styles
│   │   ├── theme.css       # Color theme
│   │   └── mfa.css         # MFA styles
│   │
│   ├── js/                 # JavaScript
│   │   ├── login.js        # Login logic
│   │   ├── register.js     # Registration logic
│   │   ├── dashboard.js    # Dashboard logic
│   │   ├── mfa.js          # MFA enrollment
│   │   └── api.js          # API utilities
│   │
│   └── lib/                # Third-party libraries
│       ├── chart.umd.js    # Chart.js (local copy)
│       └── ...
│
└── assets/                 # Static assets (images, fonts)
```

## 🚀 Usage

### 1. Start the Server

**Windows:**
```batch
cd frontend
start-server.bat
```

**Linux/Mac:**
```bash
cd frontend
python serve.py
```

**With Docker:**
```bash
docker run -p 5500:5500 -v $(pwd)/static:/app/static ztnas-frontend:latest
```

### 2. Access the Dashboard

- **Landing Page:** http://localhost:5500
- **Login:** http://localhost:5500/login.html (or click "Sign In")
- **Register:** http://localhost:5500/register.html (or click "Get Started")
- **Dashboard:** http://localhost:5500/dashboard.html (after login)

### 3. Test with Sample Credentials

```
Username: test_user
Password: Test123!@#
```

Or create your own account using the registration page.

## 🔐 Security Features

### Built-in Production Server (serve.py)
- **Directory Listing:** ✅ BLOCKED (no directory listing shown)
- **Directory Traversal:** ✅ PREVENTED (../../ attacks blocked)
- **Security Headers:** ✅ ENABLED
  - `X-Frame-Options: SAMEORIGIN`
  - `X-Content-Type-Options: nosniff`
  - `Content-Security-Policy: strict`
  - `Referrer-Policy: strict-origin-when-cross-origin`

### Frontend Security
- **HTTPS/TLS:** ✅ Ready (with Nginx/Docker)
- **CORS:** ✅ Configured for API calls
- **JWT Storage:** ✅ Secure (localStorage)
- **Input Validation:** ✅ On all forms

### Backend Integration
The frontend connects to the backend API for:
- **Authentication** (`/api/v1/auth/login`)
- **User Management** (`/api/v1/auth/users`)
- **Device Trust** (`/api/v1/devices/trusted`)
- **Risk Assessment** (`/api/v1/zero-trust/risk`)
- **Policies** (`/api/v1/auth/policies`)
- **Audit Logs** (`/api/v1/auth/audit/logs`)

## 🎓 College Dashboard Features

### 4 Role-Based Dashboards

#### 1. **Admin Dashboard**
- Full system access
- User management
- Policy configuration
- Audit log viewing
- System settings

#### 2. **HOD (Head of Department) Dashboard**
- Department user management
- Faculty oversight
- Policy enforcement
- Department-level reports

#### 3. **Faculty Dashboard**
- Personal device management
- Access to college resources
- Trust score status
- Policy acknowledgment

#### 4. **Student Dashboard**
- Device registration
- Trust score status
- Resource access
- Policy information

## 📊 Dashboard Metrics

The dashboard displays real-time metrics:
- **Device Trust Score** - Overall trust assessment
- **Risk Score** - Behavioral and device-based risk
- **Access Status** - Current access level
- **Login Patterns** - Login attempt timeline
- **Policy Compliance** - Policy adherence status
- **Audit Trail** - Recent actions and events

## 🛠️ Development

### Modify Frontend

1. Edit files in `static/html/`, `static/css/`, or `static/js/`
2. Refresh browser (Ctrl+F5 to clear cache)
3. Changes appear immediately

### Add New Page

```html
<!-- Create: static/html/newpage.html -->
<!DOCTYPE html>
<html>
<head>
    <link rel="stylesheet" href="../css/style.css">
</head>
<body>
    <h1>New Page</h1>
    <script src="../js/api.js"></script>
</body>
</html>
```

### Test API Calls

```javascript
// In browser console
const response = await fetch('http://localhost:8000/api/v1/auth/me', {
    headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` }
});
console.log(await response.json());
```

## 🧪 Verification

### Run Server Tests

```bash
# Terminal 1: Start backend
cd backend && python -m uvicorn main:app --reload

# Terminal 2: Start frontend
cd frontend && python serve.py

# Terminal 3: Run tests
cd frontend
python verify_server.py
```

Expected output:
```
✓ PASS: Root served successfully (200 OK)
✓ PASS: Directory listing blocked (403 Forbidden)
✓ PASS: All security headers present
✓ PASS: All static files found
✓ PASS: CORS headers present

✅ ALL TESTS PASSED - Server is production-ready!
```

## 📋 Deployment Checklist

### Development Setup
- [ ] Python 3.8+ installed
- [ ] Backend running on http://localhost:8000
- [ ] Frontend running on http://localhost:5500
- [ ] Can access http://localhost:5500/login.html

### Production Setup (Nginx)
- [ ] Install Nginx
- [ ] Copy `nginx.conf` to `/etc/nginx/nginx.conf`
- [ ] Copy `static/` to `/usr/share/nginx/html/`
- [ ] Configure SSL certificates
- [ ] Update backend upstream address
- [ ] Start Nginx: `sudo systemctl start nginx`

### Production Setup (Docker)
- [ ] Build image: `docker build -t ztnas-frontend:latest .`
- [ ] Run container: `docker run -p 5500:5500 ztnas-frontend:latest`
- [ ] Verify: `curl http://localhost:5500`

### College Deployment
- [ ] Backend deployed
- [ ] Database configured
- [ ] SSL certificates installed
- [ ] Domain DNS configured
- [ ] Firewall rules updated
- [ ] Backup strategy in place

## 🐛 Troubleshooting

### Issue: Directory Listing on localhost:5500
**Solution:** Use `python serve.py` instead of basic HTTP server
```bash
cd frontend
python serve.py
```

### Issue: 404 on CSS/JS
**Solution:** Ensure `static/` folder exists with CSS and JS files
```bash
ls static/css/
ls static/js/
```

### Issue: CORS Error in Console
**Solution:** Check backend is running and `.env` has correct CORS_ORIGINS
```bash
curl http://localhost:8000/health
```

### Issue: Login Fails (401)
**Solution:** Verify backend is running and database is populated
```bash
python backend/scripts/create_admin.py
```

### Issue: Blank Dashboard
**Solution:** Check browser console for errors (F12 → Console tab)
```javascript
// Manually test API
fetch('http://localhost:8000/api/v1/auth/me', {
    headers: { 'Authorization': `Bearer ${localStorage.token}` }
}).then(r => r.json()).then(console.log)
```

## 📚 Documentation

- **Production Deployment:** See `PRODUCTION_DEPLOYMENT_GUIDE.md`
- **Admin Operations:** See `ADMIN_OPERATIONS_GUIDE.md`
- **API Reference:** See backend `docs/` folder
- **System Architecture:** See `PROJECT_ANALYSIS_OVERVIEW.md`

## 🔗 Backend Connection

The frontend expects a backend API at:

```javascript
const API_BASE = 'http://localhost:8000';  // Development
// const API_BASE = 'https://api.college.edu';  // Production
```

Update in `static/js/api.js` or environment configuration.

## 📞 Support

For issues or questions:
1. Check the troubleshooting section above
2. Review browser console (F12)
3. Check backend logs: `docker logs backend`
4. Read `DEPLOYMENT_COMPLETE.md` for detailed info

## ✅ Status

✅ **Production-Ready**
- All security headers implemented
- Directory listing disabled
- CORS properly configured
- Role-based access control working
- College management system compatible
- Ready for college deployment

---

**Version:** 1.0  
**Status:** Production Ready  
**Last Updated:** 2026-03-28
