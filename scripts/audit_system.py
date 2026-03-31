#!/usr/bin/env python3
"""
ZTNAS Enterprise System Audit & Verification
Comprehensive system check for production readiness
"""

import os
import sys
import json
import subprocess
from pathlib import Path
from datetime import datetime

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    END = '\033[0m'

class SystemAudit:
    def __init__(self):
        self.root_dir = Path(__file__).parent
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "status": "PENDING",
            "checks": {},
            "critical_issues": [],
            "warnings": [],
            "success": True
        }
    
    def print_header(self, title):
        print(f"\n{Colors.CYAN}{'='*70}{Colors.END}")
        print(f"{Colors.CYAN}{title}{Colors.END}")
        print(f"{Colors.CYAN}{'='*70}{Colors.END}\n")
    
    def check(self, name, condition, critical=False):
        """Record a check result"""
        status = "✓" if condition else "✗"
        color = Colors.GREEN if condition else Colors.RED
        print(f"{color}{status}{Colors.END} {name}")
        
        self.results["checks"][name] = condition
        
        if not condition:
            self.results["success"] = False
            if critical:
                self.results["critical_issues"].append(name)
            else:
                self.results["warnings"].append(name)
    
    def section_header(self, title):
        print(f"\n{Colors.BLUE}► {title}{Colors.END}")
    
    # ============================================================
    # FILE STRUCTURE CHECKS
    # ============================================================
    
    def check_file_structure(self):
        self.print_header("STEP 1: File Structure Verification")
        
        required_files = {
            "Backend": [
                "backend/main.py",
                "backend/requirements.txt",
                "backend/.env",
                "backend/app/routes/auth.py",
                "backend/app/models/__init__.py",
                "backend/app/services/auth_service.py",
                "backend/utils/security.py",
            ],
            "Frontend": [
                "frontend/static/html/login.html",
                "frontend/static/html/register.html",
                "frontend/static/html/dashboard.html",
                "frontend/static/js/auth.js",
                "frontend/static/js/login.js",
                "frontend/static/js/dashboard.js",
                "frontend/serve_simple.py",
            ],
            "Database": [
                "backend/config/database.py",
                "backend/config/settings.py",
            ]
        }
        
        for category, files in required_files.items():
            self.section_header(f"{category} Files")
            for file in files:
                path = self.root_dir / file
                exists = path.exists()
                self.check(f"  {file}", exists, critical=True)
    
    # ============================================================
    # DEPENDENCIES CHECK
    # ============================================================
    
    def check_dependencies(self):
        self.print_header("STEP 2: Python Dependencies Check")
        
        self.section_header("Backend Requirements")
        req_file = self.root_dir / "backend/requirements.txt"
        
        if req_file.exists():
            with open(req_file) as f:
                content = f.read()
            
            required_packages = {
                "fastapi": "FastAPI framework",
                "uvicorn": "ASGI server",
                "sqlalchemy": "ORM",
                "psycopg2": "PostgreSQL driver",
                "pydantic": "Data validation",
                "bcrypt": "Password hashing",
                "python-jose": "JWT",
                "slowapi": "Rate limiting",
                "python-json-logger": "Structured logging",
            }
            
            for package, description in required_packages.items():
                has_package = package.lower() in content.lower()
                self.check(f"  {package:20} - {description}", has_package, critical=True)
        else:
            self.check("  requirements.txt exists", False, critical=True)
    
    # ============================================================
    # ENVIRONMENT CONFIGURATION CHECK
    # ============================================================
    
    def check_environment(self):
        self.print_header("STEP 3: Environment Configuration")
        
        self.section_header("Backend Environment (.env)")
        env_file = self.root_dir / "backend/.env"
        
        if env_file.exists():
            with open(env_file) as f:
                env_content = f.read()
            
            required_vars = [
                "DATABASE_URL",
                "SECRET_KEY",
                "ENVIRONMENT",
                "CORS_ORIGINS",
            ]
            
            for var in required_vars:
                has_var = var in env_content
                self.check(f"  {var}", has_var, critical=True)
        else:
            self.check("  .env file exists", False, critical=True)
            print(f"    {Colors.YELLOW}⚠ Create backend/.env with DATABASE_URL and SECRET_KEY{Colors.END}")
    
    # ============================================================
    # DATABASE CHECK
    # ============================================================
    
    def check_database(self):
        self.print_header("STEP 4: Database Schema & Models")
        
        self.section_header("SQLAlchemy Models")
        models_file = self.root_dir / "backend/app/models/__init__.py"
        
        if models_file.exists():
            with open(models_file) as f:
                content = f.read()
            
            required_models = {
                "User": "User model",
                "Role": "Role model",
                "Permission": "Permission model",
                "MFAMethod": "MFA methods",
                "AuditLog": "Audit logging",
                "DeviceRegistry": "Device trust",
                "Session": "Session management",
            }
            
            for model, desc in required_models.items():
                has_model = f"class {model}" in content
                self.check(f"  {model:20} - {desc}", has_model, critical=True)
        else:
            self.check("  Models file exists", False, critical=True)
    
    # ============================================================
    # API ENDPOINTS CHECK
    # ============================================================
    
    def check_api_endpoints(self):
        self.print_header("STEP 5: API Endpoints Verification")
        
        self.section_header("Authentication Endpoints")
        auth_file = self.root_dir / "backend/app/routes/auth.py"
        
        if auth_file.exists():
            with open(auth_file) as f:
                content = f.read()
            
            endpoints = {
                "/register": "User registration",
                "/login": "User login",
                "/refresh": "Token refresh",
                "/logout": "User logout",
                "/change-password": "Password change",
                "/admin/unlock-account": "Admin account unlock",
                "/admin/account-status": "Admin account status",
                "@limiter.limit": "Rate limiting",
                "AccountLockoutPolicy": "Account lockout",
            }
            
            for endpoint, desc in endpoints.items():
                has_endpoint = endpoint in content
                self.check(f"  {endpoint:30} - {desc}", has_endpoint, critical=True)
        else:
            self.check("  Auth routes file exists", False, critical=True)
    
    # ============================================================
    # FRONTEND CHECK
    # ============================================================
    
    def check_frontend(self):
        self.print_header("STEP 6: Frontend Files & Configuration")
        
        self.section_header("HTML Pages")
        pages = ["login.html", "register.html", "dashboard.html", "mfa.html"]
        for page in pages:
            html_file = self.root_dir / f"frontend/static/html/{page}"
            self.check(f"  {page}", html_file.exists(), critical=True)
        
        self.section_header("JavaScript Services")
        scripts = ["auth.js", "login.js", "register.js", "dashboard.js", "mfa.js"]
        for script in scripts:
            js_file = self.root_dir / f"frontend/static/js/{script}"
            self.check(f"  {script}", js_file.exists(), critical=True)
        
        self.section_header("Frontend Server")
        serve_file = self.root_dir / "frontend/serve_simple.py"
        if serve_file.exists():
            with open(serve_file) as f:
                content = f.read()
            self.check("  serve_simple.py exists", True)
            self.check("  Query parameter stripping", "split('?')[0]" in content)
        else:
            self.check("  serve_simple.py exists", False, critical=True)
    
    # ============================================================
    # CODE QUALITY CHECK
    # ============================================================
    
    def check_code_quality(self):
        self.print_header("STEP 7: Code Quality & Security")
        
        self.section_header("Security Features")
        
        # Check rate limiting
        rate_limit_file = self.root_dir / "backend/utils/rate_limiting.py"
        self.check("  Rate limiting module", rate_limit_file.exists(), critical=False)
        
        # Check account lockout
        lockout_file = self.root_dir / "backend/utils/account_lockout.py"
        self.check("  Account lockout policy", lockout_file.exists(), critical=False)
        
        # Check security module
        security_file = self.root_dir / "backend/utils/security.py"
        if security_file.exists():
            with open(security_file) as f:
                content = f.read()
            self.check("  Password hashing (bcrypt)", "bcrypt" in content, critical=True)
            self.check("  JWT token creation", "create_access_token" in content, critical=True)
            self.check("  Token verification", "verify_access_token" in content, critical=True)
        else:
            self.check("  Security module exists", False, critical=True)
    
    # ============================================================
    # DOCUMENTATION CHECK
    # ============================================================
    
    def check_documentation(self):
        self.print_header("STEP 8: Documentation")
        
        docs = {
            "ENTERPRISE_SECURITY_IMPLEMENTATION.md": "Enterprise security guide",
            "IMPLEMENTATION_PHASE1_SUMMARY.md": "Phase 1 summary",
            "PHASE1_COMPLETE.md": "Phase 1 completion",
            "backend/tests/test_enterprise_security.py": "Enterprise security tests",
        }
        
        for doc, desc in docs.items():
            doc_file = self.root_dir / doc
            self.check(f"  {doc:40} - {desc}", doc_file.exists())
    
    # ============================================================
    # CONFIGURATION CHECK
    # ============================================================
    
    def check_configuration(self):
        self.print_header("STEP 9: Configuration Files")
        
        configs = {
            "backend/.env": "Backend environment",
            "backend/config/settings.py": "Settings configuration",
            "backend/config/database.py": "Database configuration",
            "backend/pytest.ini": "Pytest configuration",
            "docker-compose.yml": "Docker compose",
        }
        
        for config, desc in configs.items():
            config_file = self.root_dir / config
            exists = config_file.exists()
            self.check(f"  {config:30} - {desc}", exists, critical=(config.endswith(".env") or config.endswith("settings.py")))
    
    # ============================================================
    # RUNTIME CHECK
    # ============================================================
    
    def check_runtime(self):
        self.print_header("STEP 10: Runtime Components")
        
        self.section_header("Python Version")
        try:
            version = sys.version_info
            py_version = f"{version.major}.{version.minor}.{version.micro}"
            supports_py310 = version.major >= 3 and version.minor >= 10
            self.check(f"  Python {py_version} (requires 3.10+)", supports_py310, critical=True)
        except Exception as e:
            self.check("  Python version check", False, critical=True)
        
        self.section_header("Required Directories")
        dirs = [
            ("backend/logs", "Logs directory"),
            ("backend/migrations", "Database migrations"),
            ("frontend/static/html", "HTML templates"),
        ]
        
        for dir_path, desc in dirs:
            dir_full = self.root_dir / dir_path
            self.check(f"  {dir_path:30} - {desc}", dir_full.exists())
    
    # ============================================================
    # GENERATE REPORT
    # ============================================================
    
    def generate_report(self):
        self.print_header("AUDIT SUMMARY")
        
        total_checks = len(self.results["checks"])
        passed_checks = sum(1 for v in self.results["checks"].values() if v)
        failed_checks = total_checks - passed_checks
        
        print(f"Total Checks:        {total_checks}")
        print(f"{Colors.GREEN}Passed:              {passed_checks}{Colors.END}")
        print(f"{Colors.RED}Failed:              {failed_checks}{Colors.END}")
        
        if self.results["critical_issues"]:
            print(f"\n{Colors.RED}🔴 CRITICAL ISSUES ({len(self.results['critical_issues'])}){Colors.END}")
            for issue in self.results["critical_issues"]:
                print(f"  {Colors.RED}✗{Colors.END} {issue}")
        
        if self.results["warnings"]:
            print(f"\n{Colors.YELLOW}🟡 WARNINGS ({len(self.results['warnings'])}){Colors.END}")
            for warning in self.results["warnings"]:
                print(f"  {Colors.YELLOW}⚠{Colors.END} {warning}")
        
        if self.results["success"]:
            self.results["status"] = "PASSED"
            print(f"\n{Colors.GREEN}✅ All critical checks passed!{Colors.END}")
            print(f"{Colors.GREEN}System is ready for production deployment.{Colors.END}")
        else:
            self.results["status"] = "FAILED"
            print(f"\n{Colors.RED}❌ System has critical issues.{Colors.END}")
            print(f"{Colors.RED}Please fix the issues above before deployment.{Colors.END}")
        
        # Save results to file
        self.save_results()
    
    def save_results(self):
        """Save audit results to JSON file"""
        results_file = self.root_dir / "AUDIT_RESULTS.json"
        with open(results_file, 'w') as f:
            json.dump(self.results, f, indent=2)
        print(f"\n📊 Audit results saved to: {results_file}")
    
    def run_full_audit(self):
        """Run all audit checks"""
        print(f"\n{Colors.CYAN}ZTNAS Enterprise System Audit{Colors.END}")
        print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        
        self.check_file_structure()
        self.check_dependencies()
        self.check_environment()
        self.check_database()
        self.check_api_endpoints()
        self.check_frontend()
        self.check_code_quality()
        self.check_documentation()
        self.check_configuration()
        self.check_runtime()
        self.generate_report()
        
        return self.results["success"]

if __name__ == "__main__":
    audit = SystemAudit()
    success = audit.run_full_audit()
    sys.exit(0 if success else 1)
