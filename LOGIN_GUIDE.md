# 🔐 COLLEGE SYSTEM - LOGIN GUIDE

## ✅ How to Login

Your login form accepts **BOTH username AND email**. You can use either one!

### Quickest Way: Use Demo Login Button
1. Go to login page: `http://localhost:5500/html/login.html`
2. Click the **"Demo Login"** button
3. You're instantly logged in to the dashboard

---

## 📝 Test Credentials (Ready to Use)

### Primary Test Account
- **Username:** `testcollege`
- **Email:** `testcollege@example.edu`
- **Password:** `TestCollege123`
- **Status:** ✅ Working (use this for testing)

### Secondary Test Account
- **Username:** `collegeadmin`
- **Email:** `collegeadmin@example.edu`
- **Password:** `CollegeTest123`
- **Status:** ✅ Working

---

## 🔑 How to Login - Both Methods Work

### Method 1: Use Username
```
Username/Email field: testcollege
Password field:       TestCollege123
```

### Method 2: Use Email
```
Username/Email field: testcollege@example.edu
Password field:       TestCollege123
```

### Method 3: Use Demo Button (Easiest)
- Click "Demo Login" button on login page
- Automatically fills in and logs you in

---

## ❌ If Login Fails

### "Invalid username/email or password"
- ✓ Double-check spelling (case-sensitive password)
- ✓ Make sure you're entering username OR email correctly
- ✓ Try the Demo Login button

### "Account temporarily locked"
- ✓ Wait a few minutes and try again
- ✓ Or create a new account via Registration

### "Network error"
- ✓ Make sure backend is running: `http://localhost:8000/health`
- ✓ Make sure frontend is running: `http://localhost:5500`

---

## ✨ Creating New Accounts

Want to create more college accounts?

1. Click **"Register"** button on login page
2. Fill in the registration form:
   - Email: any valid email
   - Username: your preferred username
   - Password: must be 8+ characters
   - First/Last name: your name

3. Click "Register"
4. Login with your new credentials

---

## 🎯 Form Field Explained

### "Username or Email Address" Field
- Enter EITHER your username (e.g., `testcollege`)
- OR your email address (e.g., `testcollege@example.edu`)
- The backend will recognize which one you used

### "Password" Field
- Enter your password exactly as created
- Passwords are case-sensitive
- Min 8 characters required

---

## 🔒 Security Notes

✅ Passwords are hashed with Argon2 (military-grade security)
✅ Login tokens automatically expire for security
✅ Failed login attempts are tracked and logged
✅ Accounts lock after too many failed attempts

---

## 📊 Status Check

- Backend Health: `http://localhost:8000/health`
- API Documentation: `http://localhost:8000/docs`
- Dashboard: `http://localhost:5500/html/dashboard.html` (after login)

---

## 💡 Pro Tips

✓ Use **Demo Login** button for instant access  
✓ Both username and email format work  
✓ Register new accounts anytime  
✓ Passwords are case-sensitive  
✓ Account lockout is temporary (wait a few minutes)  

---

**Need more help?** Check the application logs or contact support.

---

**System Status:** ✅ READY FOR COLLEGE USE
