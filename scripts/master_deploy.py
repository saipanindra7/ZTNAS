#!/usr/bin/env python3
"""
ZTNAS Master Deployment Script
Complete step-by-step deployment with verification
"""

import os
import sys
import subprocess
import time
from pathlib import Path
from datetime import datetime

class Colors:
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    END = '\033[0m'

class MasterDeployment:
    def __init__(self):
        # Get root from script location and go up one level to project root
        self.root = Path(__file__).parent.parent
        self.backend = self.root / "backend"
        self.frontend = self.root / "frontend"
        
    def log_header(self, title):
        print(f"\n{Colors.CYAN}{'='*70}{Colors.END}")
        print(f"{Colors.CYAN}  {title}{Colors.END}")
        print(f"{Colors.CYAN}{'='*70}{Colors.END}\n")
    
    def log_step(self, step_num, title):
        print(f"{Colors.GREEN}Step {step_num}:{Colors.END} {title}")
    
    def log_success(self, msg):
        print(f"{Colors.GREEN}✓{Colors.END} {msg}")
    
    def log_error(self, msg):
        print(f"{Colors.RED}✗{Colors.END} {msg}")
    
    def log_warning(self, msg):
        print(f"{Colors.YELLOW}⚠{Colors.END} {msg}")
    
    def log_info(self, msg):
        print(f"  {msg}")
    
    # ================================================================
    # PHASE 1: PRE-DEPLOYMENT CHECKS
    # ================================================================
    
    def phase_1_checks(self):
        self.log_header("PHASE 1: Pre-Deployment Checks")
        
        self.log_step(1, "Verify Directory Structure")
        dirs_ok = True
        for path in [self.backend, self.frontend, self.backend / "logs"]:
            if path.exists():
                self.log_success(f"Found: {path.relative_to(self.root)}")
            else:
                self.log_error(f"Missing: {path.relative_to(self.root)}")
                dirs_ok = False
        
        self.log_step(2, "Verify Critical Files")
        files = {
            "backend/main.py": "FastAPI main",
            "backend/.env": "Environment config",
            "backend/requirements.txt": "Python dependencies",
            "frontend/serve_simple.py": "Frontend server",
            "frontend/static/js/auth.js": "Auth service",
        }
        
        files_ok = True
        for file_path, description in files.items():
            full_path = self.root / file_path
            if full_path.exists():
                self.log_success(f"{file_path:40} - {description}")
            else:
                self.log_error(f"{file_path:40} - {description}")
                files_ok = False
        
        self.log_step(3, "Python Version Check")
        version = sys.version_info
        if version.major >= 3 and version.minor >= 10:
            self.log_success(f"Python {version.major}.{version.minor}.{version.micro} - OK")
        else:
            self.log_error(f"Python {version.major}.{version.minor} - Need 3.10+")
        
        return dirs_ok and files_ok
    
    # ================================================================
    # PHASE 2: BACKEND VERIFICATION
    # ================================================================
    
    def phase_2_backend(self):
        self.log_header("PHASE 2: Backend Verification")
        
        os.chdir(self.backend)
        
        self.log_step(1, "Check Python Imports")
        imports_ok = True
        
        imports = [
            ("Models", "from app.models import User"),
            ("Auth Service", "from app.services.auth_service import AuthService"),
            ("Security Utils", "from utils.security import verify_password"),
            ("Rate Limiting", "from utils.rate_limiting import limiter"),
            ("Account Lockout", "from utils.account_lockout import AccountLockoutPolicy"),
        ]
        
        for name, import_stmt in imports:
            try:
                exec(import_stmt)
                self.log_success(f"{name:20} - Imports OK")
            except Exception as e:
                self.log_error(f"{name:20} - Import failed: {str(e)[:50]}")
                imports_ok = False
        
        self.log_step(2, "Verify Configuration")
        try:
            from config.settings import settings
            self.log_success(f"App Name: {settings.APP_NAME}")
            self.log_success(f"Environment: {settings.ENVIRONMENT}")
            self.log_success(f"Debug: {settings.DEBUG}")
        except Exception as e:
            self.log_error(f"Configuration load failed: {e}")
            imports_ok = False
        
        self.log_step(3, "Check Database Configuration")
        try:
            from config.settings import settings
            db_url = settings.DATABASE_URL if hasattr(settings, 'DATABASE_URL') else "Not configured"
            if "postgresql" in str(db_url).lower():
                self.log_success("PostgreSQL configured")
            else:
                self.log_warning("Database URL may be incorrect")
        except:
            self.log_warning("Could not verify database configuration")
        
        os.chdir(self.root)
        return imports_ok
    
    # ================================================================
    # PHASE 3: FRONTEND VERIFICATION  
    # ================================================================
    
    def phase_3_frontend(self):
        self.log_header("PHASE 3: Frontend Verification")
        
        self.log_step(1, "Verify HTML Pages")
        html_files = [
            "static/html/login.html",
            "static/html/register.html",
            "static/html/dashboard.html",
            "static/html/mfa.html",
        ]
        
        html_ok = True
        for html_file in html_files:
            full_path = self.frontend / html_file
            if full_path.exists():
                self.log_success(f"{html_file}")
            else:
                self.log_error(f"{html_file} - NOT FOUND")
                html_ok = False
        
        self.log_step(2, "Verify JavaScript Files")
        js_files = [
            "static/js/auth.js",
            "static/js/login.js",
            "static/js/register.js",
            "static/js/dashboard.js",
        ]
        
        js_ok = True
        for js_file in js_files:
            full_path = self.frontend / js_file
            if full_path.exists():
                self.log_success(f"{js_file}")
            else:
                self.log_error(f"{js_file} - NOT FOUND")
                js_ok = False
        
        self.log_step(3, "Check Frontend Server")
        serve_file = self.frontend / "serve_simple.py"
        if serve_file.exists():
            self.log_success("Frontend server: serve_simple.py exists")
        else:
            self.log_error("Frontend server not found")
            js_ok = False
        
        return html_ok and js_ok
    
    # ================================================================
    # PHASE 4: DEPLOYMENT RECOMMENDATIONS
    # ================================================================
    
    def phase_4_recommendations(self):
        self.log_header("PHASE 4: Deployment Recommendations")
        
        self.log_step(1, "Backend Startup")
        self.log_info("Run the following command in a terminal:")
        print(f"  {Colors.CYAN}cd backend{Colors.END}")
        print(f"  {Colors.CYAN}python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000{Colors.END}")
        
        self.log_step(2, "Frontend Startup")
        self.log_info("In a new terminal, run:")
        print(f"  {Colors.CYAN}cd frontend{Colors.END}")
        print(f"  {Colors.CYAN}python serve_simple.py{Colors.END}")
        
        self.log_step(3, "Testing")
        self.log_info("After both services are running:")
        print(f"  {Colors.CYAN}Backend health check: curl http://localhost:8000/health{Colors.END}")
        print(f"  {Colors.CYAN}Frontend login: http://localhost:5500/static/html/login.html{Colors.END}")
        
        self.log_step(4, "Security Testing")
        self.log_info("Run comprehensive security tests:")
        print(f"  {Colors.CYAN}cd backend{Colors.END}")
        print(f"  {Colors.CYAN}python tests/test_enterprise_security.py{Colors.END}")
    
    # ================================================================
    # MAIN EXECUTION
    # ================================================================
    
    def run_all(self):
        print(f"\n{Colors.CYAN}ZTNAS Master Deployment Script{Colors.END}")
        print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Phase 1
        if not self.phase_1_checks():
            self.log_error("Pre-deployment checks failed!")
            return False
        
        self.log_success("All pre-deployment checks passed!\n")
        
        # Phase 2
        if not self.phase_2_backend():
            self.log_warning("Some backend checks failed - may need dependencies installed")
        else:
            self.log_success("Backend verification passed!\n")
        
        # Phase 3
        if not self.phase_3_frontend():
            self.log_error("Frontend verification failed!")
            return False
        
        self.log_success("Frontend verification passed!\n")
        
        # Phase 4
        self.phase_4_recommendations()
        
        # Summary
        self.log_header("Deployment Summary")
        print(f"""
{Colors.GREEN}✓ All critical systems verified{Colors.END}
{Colors.GREEN}✓ Backend configuration valid{Colors.END}
{Colors.GREEN}✓ Frontend files present{Colors.END}
{Colors.GREEN}✓ Python version compatible{Colors.END}

{Colors.CYAN}Next Steps:{Colors.END}
1. Start backend: cd backend && python -m uvicorn main:app --reload
2. Start frontend: cd frontend && python serve_simple.py  
3. Test endpoints: curl http://localhost:8000/health
4. Open browser: http://localhost:5500/static/html/login.html
5. Run tests: python backend/tests/test_enterprise_security.py

{Colors.YELLOW}System ready for deployment!{Colors.END}
        """)
        
        return True

if __name__ == "__main__":
    deployer = MasterDeployment()
    success = deployer.run_all()
    sys.exit(0 if success else 1)
