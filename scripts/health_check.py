#!/usr/bin/env python3
"""
ZTNAS System Health Check - Detailed Verification
Checks all systems and generates a detailed report
"""

import os
import sys
import json
from pathlib import Path
from datetime import datetime
import subprocess

class HealthCheck:
    def __init__(self):
        self.root = Path(__file__).parent
        self.checks = {}
        self.critical_issues = []
        self.warnings = []
    
    def print_header(self, title):
        print(f"\n{'='*70}")
        print(f"  {title}")
        print(f"{'='*70}\n")
    
    def check(self, name, result, critical=False):
        status = "✓" if result else "✗"
        color = "\033[92m" if result else "\033[91m"
        print(f"{color}{status}\033[0m {name}")
        self.checks[name] = result
        
        if not result:
            if critical:
                self.critical_issues.append(name)
            else:
                self.warnings.append(name)
    
    # TASK 1: Backend Files
    def verify_backend_files(self):
        self.print_header("1. Backend Files")
        
        backend_files = [
            "backend/main.py",
            "backend/.env",
            "backend/requirements.txt",
            "backend/app/models/__init__.py",
            "backend/app/routes/auth.py",
            "backend/app/services/auth_service.py",
            "backend/utils/security.py",
            "backend/config/settings.py",
            "backend/config/database.py",
        ]
        
        for file in backend_files:
            path = self.root / file
            self.check(f"File: {file}", path.exists(), critical=True)
    
    # TASK 2: Frontend Files
    def verify_frontend_files(self):
        self.print_header("2. Frontend Files")
        
        frontend_files = [
            "frontend/static/html/login.html",
            "frontend/static/html/register.html",
            "frontend/static/html/dashboard.html",
            "frontend/static/js/auth.js",
            "frontend/static/js/login.js",
            "frontend/static/js/dashboard.js",
            "frontend/serve_simple.py",
        ]
        
        for file in frontend_files:
            path = self.root / file
            self.check(f"File: {file}", path.exists(), critical=True)
    
    # TASK 3: Python Imports
    def verify_python_imports(self):
        self.print_header("3. Python Module Imports")
        
        os.chdir(self.root / "backend")
        
        test_imports = [
            ("App Models", "from app.models import User, Role, Permission, AuditLog"),
            ("Auth Service", "from app.services.auth_service import AuthService"),
            ("Security Utils", "from utils.security import verify_password, create_access_token"),
            ("Rate Limiting", "from utils.rate_limiting import limiter"),
            ("Account Lockout", "from utils.account_lockout import AccountLockoutPolicy"),
            ("Database", "from config.database import get_db, init_db"),
            ("Settings", "from config.settings import settings"),
        ]
        
        for name, import_stmt in test_imports:
            try:
                exec(import_stmt)
                self.check(f"Import: {name}", True)
            except Exception as e:
                self.check(f"Import: {name} ({str(e)[:40]})", False, critical=True)
        
        os.chdir(self.root)
    
    # TASK 4: Environment Variables
    def verify_environment(self):
        self.print_header("4. Environment Configuration")
        
        env_file = self.root / "backend/.env"
        if env_file.exists():
            with open(env_file) as f:
                content = f.read()
            
            required_vars = [
                ("DATABASE_URL", "PostgreSQL database URL"),
                ("SECRET_KEY", "JWT secret key"),
                ("CORS_ORIGINS", "Allowed CORS origins"),
                ("APP_NAME", "Application name"),
            ]
            
            for var, desc in required_vars:
                has_var = var in content and len(content.split(f"{var}=")[1].split('\n')[0].strip()) > 0
                self.check(f"Config: {var} ({desc})", has_var, critical=True)
        else:
            self.check("ENV file exists", False, critical=True)
    
    # TASK 5: API Endpoints
    def verify_api_endpoints(self):
        self.print_header("5. API Endpoints")
        
        auth_file = self.root / "backend/app/routes/auth.py"
        if auth_file.exists():
            with open(auth_file) as f:
                content = f.read()
            
            endpoints = [
                ("Register", '@router.post("/register")', "User registration"),
                ("Login", '@router.post("/login")', "User login"),
                ("Refresh", '@router.post("/refresh")', "Token refresh"),
                ("Logout", '@router.post("/logout")', "User logout"),
                ("Change Password", '@router.post("/change-password")', "Password change"),
                ("Admin Unlock", '@router.post("/admin/unlock-account")', "Admin unlock"),
                ("Admin Status", '@router.get("/admin/account-status")', "Account status"),
            ]
            
            for name, decorator, desc in endpoints:
                has_endpoint = decorator in content
                self.check(f"Endpoint: {name:20} - {desc}", has_endpoint, critical=True)
    
    # TASK 6: Security Features
    def verify_security_features(self):
        self.print_header("6. Security Features")
        
        checks = [
            ("Rate Limiting Active", self.root / "backend/utils/rate_limiting.py"),
            ("Account Lockout Policy", self.root / "backend/utils/account_lockout.py"),
            ("Password Hashing", self.root / "backend/utils/security.py"),
        ]
        
        for name, file_path in checks:
            if file_path.exists():
                with open(file_path) as f:
                    content = f.read()
                
                if "rate_limiting" in file_path.name:
                    has_feature = "RATE_LIMITS" in content and "MAX_FAILED_ATTEMPTS" not in content
                elif "account_lockout" in file_path.name:
                    has_feature = "MAX_FAILED_ATTEMPTS" in content and "check_account_locked" in content
                elif "security" in file_path.name:
                    has_feature = "bcrypt" in content and "create_access_token" in content
                
                self.check(f"Security: {name}", has_feature, critical=not ("lockout" in file_path.name))
            else:
                critical = "rate_limiting" in file_path.name
                self.check(f"Security: {name}", False, critical=critical)
    
    # TASK 7: Frontend Configuration
    def verify_frontend_config(self):
        self.print_header("7. Frontend Configuration")
        
        serve_file = self.root / "frontend/serve_simple.py"
        if serve_file.exists():
            with open(serve_file) as f:
                content = f.read()
            
            checks = [
                ("Server Port 5500", "5500" in content),
                ("HTML Routing", "\.html" in content),
                ("Query Parameter Handling", "split('?')" in content),
                ("Static Files Serving", "static" in content.lower()),
            ]
            
            for check_name, condition in checks:
                self.check(f"Config: {check_name}", condition, critical=True)
        else:
            self.check("Frontend server exists", False, critical=True)
    
    # TASK 8: Documentation
    def verify_documentation(self):
        self.print_header("8. Documentation Files")
        
        docs = [
            ("Phase 1 Complete", "PHASE1_COMPLETE.md"),
            ("Enterprise Security", "ENTERPRISE_SECURITY_IMPLEMENTATION.md"),
            ("Step-by-Step Plan", "STEP_BY_STEP_COMPLETION.md"),
            ("API Routes", "backend/app/routes/auth.py"),
        ]
        
        for name, file_path in docs:
            path = self.root / file_path
            self.check(f"Doc: {name}", path.exists())
    
    # TASK 9: Database Setup
    def verify_database_setup(self):
        self.print_header("9. Database Setup")
        
        db_file = self.root / "backend/config/database.py"
        if db_file.exists():
            with open(db_file) as f:
                content = f.read()
            
            checks = [
                ("SQLAlchemy Import", "SQLAlchemy" in content or "sqlalchemy" in content),
                ("Database URL", "DATABASE_URL" in content),
                ("Session Factory", "SessionLocal" in content),
                ("Base Model", "Base" in content),
            ]
            
            for check_name, condition in checks:
                self.check(f"Database: {check_name}", condition, critical=True)
    
    # TASK 10: Test Files
    def verify_tests(self):
        self.print_header("10. Test Files")
        
        test_file = self.root / "backend/tests/test_enterprise_security.py"
        self.check("Test Suite: Enterprise Security", test_file.exists())
    
    def generate_report(self):
        self.print_header("Health Check Summary")
        
        total = len(self.checks)
        passed = sum(1 for v in self.checks.values() if v)
        
        print(f"Total Checks:        {total}")
        print(f" ✓ Passed:           {passed}")
        print(f" ✗ Failed:           {total - passed}")
        
        if self.critical_issues:
            print(f"\n🔴 CRITICAL ISSUES ({len(self.critical_issues)}):")
            for issue in self.critical_issues:
                print(f"   ✗ {issue}")
        
        if self.warnings:
            print(f"\n🟡 WARNINGS ({len(self.warnings)}):")
            for warning in self.warnings[:5]:
                print(f"   ⚠ {warning}")
        
        if not self.critical_issues:
            print(f"\n✅ All critical checks passed!")
            print(f"System is ready for deployment!")
        else:
            print(f"\n❌ Critical issues found!")
            print(f"Please fix the above issues before proceeding.")
    
    def run_all(self):
        print("\n" + "="*70)
        print("  ZTNAS System Health Check")
        print("="*70)
        
        self.verify_backend_files()
        self.verify_frontend_files()
        self.verify_python_imports()
        self.verify_environment()
        self.verify_api_endpoints()
        self.verify_security_features()
        self.verify_frontend_config()
        self.verify_documentation()
        self.verify_database_setup()
        self.verify_tests()
        self.generate_report()
        
        return len(self.critical_issues) == 0

if __name__ == "__main__":
    check = HealthCheck()
    success = check.run_all()
    sys.exit(0 if success else 1)
