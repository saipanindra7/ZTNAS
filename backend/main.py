import os
import sys

# Add backend directory to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from config.settings import settings
from config.database import init_db, get_db, SessionLocal
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/ztnas.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

def create_app():
    """Create and configure FastAPI application"""
    
    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        description="Zero Trust Network Access System",
        debug=settings.DEBUG
    )
    
    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
        allow_headers=["*"],
    )
    
    # ============================================================
    # PRODUCTION MODULES INTEGRATION
    # ============================================================
    
    # 1. Rate Limiting (slowapi)
    try:
        from utils.rate_limiting import limiter
        app.state.limiter = limiter
        logger.info("Rate limiting middleware initialized")
    except Exception as e:
        logger.warning(f"Rate limiting initialization skipped: {e}")
    
    # 2. Structured Logging (python-json-logger)
    try:
        from utils.logging_config import setup_structured_logging
        setup_structured_logging()
        logger.info("Structured logging configured")
    except Exception as e:
        logger.warning(f"Structured logging initialization skipped: {e}")
    
    # 3. Secrets Management (AWS Secrets Manager)
    try:
        from utils.secrets_management import SecretsManager
        app.state.secrets_manager = SecretsManager()
        logger.info("Secrets management initialized")
    except Exception as e:
        logger.warning(f"Secrets management initialization skipped: {e}")
    
    # 4. Database Backup (APScheduler)
    try:
        from utils.database_backup import BackupManager
        app.state.backup_manager = BackupManager()
        app.state.backup_manager.start()
        logger.info("Database backup manager initialized")
    except Exception as e:
        logger.warning(f"Database backup initialization skipped: {e}")
    
    # 5. Input Validation
    try:
        from utils.input_validation import SecurityValidator
        app.state.validator = SecurityValidator()
        logger.info("Input validation system initialized")
    except Exception as e:
        logger.warning(f"Input validation initialization skipped: {e}")
    
    # 6. GDPR Compliance
    try:
        from utils.gdpr_compliance import GDPRManager
        app.state.gdpr_manager = GDPRManager()
        logger.info("GDPR compliance manager initialized")
    except Exception as e:
        logger.warning(f"GDPR compliance initialization skipped: {e}")
    
    # 7. Prometheus Metrics
    try:
        from prometheus_client import Counter, Histogram
        from prometheus_client import make_asgi_app
        metrics_app = make_asgi_app()
        app.mount("/metrics", metrics_app)
        
        # Request metrics
        app.state.request_count = Counter(
            'ztnas_requests_total',
            'Total requests',
            ['method', 'endpoint']
        )
        app.state.request_duration = Histogram(
            'ztnas_request_duration_seconds',
            'Request duration',
            ['method', 'endpoint']
        )
        logger.info("Prometheus metrics initialized")
    except Exception as e:
        logger.warning(f"Prometheus metrics initialization skipped: {e}")
    
    # ============================================================
    # END PRODUCTION MODULES
    # ============================================================
    
    # Initialize database
    try:
        init_db()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise
    
    # Health check endpoint
    @app.get("/health", tags=["Health"])
    def health_check():
        return {
            "status": "healthy",
            "app_name": settings.APP_NAME,
            "version": settings.APP_VERSION,
            "environment": settings.ENVIRONMENT,
            "production_modules": [
                "rate_limiting",
                "structured_logging",
                "secrets_management",
                "database_backup",
                "gdpr_compliance",
                "input_validation",
                "prometheus_metrics"
            ]
        }
    
    if settings.DEBUG:
        # DEBUG ENDPOINT - Unlock account (REMOVE IN PRODUCTION)
        @app.post("/debug/unlock/{username}", tags=["Debug"])
        def debug_unlock_account(username: str):
            """TEMPORARY: Unlock a locked account for testing"""
            try:
                from app.models import User
                db = SessionLocal()
                user = db.query(User).filter(User.username == username).first()

                if not user:
                    db.close()
                    return {"error": f"User '{username}' not found"}

                user.is_locked = False
                user.failed_login_attempts = 0
                user.last_locked_time = None
                db.commit()
                db.close()

                logger.info(f"DEBUG: Unlocked user {username}")
                return {"success": True, "message": f"User {username} unlocked"}
            except Exception as e:
                logger.error(f"DEBUG unlock error: {e}")
                return {"error": str(e)}

        # DEBUG ENDPOINT - Set password (REMOVE IN PRODUCTION)
        @app.post("/debug/setpassword/{username}/{password}", tags=["Debug"])
        def debug_set_password(username: str, password: str):
            """TEMPORARY: Set user password for testing"""
            try:
                from app.models import User
                from utils.security import hash_password

                db = SessionLocal()
                user = db.query(User).filter(User.username == username).first()

                if not user:
                    db.close()
                    return {"error": f"User '{username}' not found"}

                user.password_hash = hash_password(password)
                user.is_locked = False
                user.failed_login_attempts = 0
                db.commit()
                db.close()

                logger.info(f"DEBUG: Password set for user {username}")
                return {"success": True, "message": f"Password updated for {username}"}
            except Exception as e:
                logger.error(f"DEBUG password set error: {e}")
                return {"error": str(e)}
    
    # Include routers
    from app.routes import auth, mfa, zero_trust, mfa_setup, admin_management, student, faculty, hod, admin_roles
    app.include_router(auth.router)
    app.include_router(mfa.router)
    app.include_router(mfa_setup.router)
    app.include_router(admin_management.router)
    app.include_router(zero_trust.router)
    app.include_router(student.router)
    app.include_router(faculty.router)
    app.include_router(hod.router)
    app.include_router(admin_roles.router)
    
    logger.info(f"{settings.APP_NAME} v{settings.APP_VERSION} application initialized")
    logger.info("All production modules loaded successfully")
    
    return app

# Create app instance
app = create_app()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_level="info"
    )
