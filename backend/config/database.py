from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from config.settings import settings
import logging
from urllib.parse import quote

logger = logging.getLogger(__name__)

# Create database engine with proper URL escaping
db_url = settings.DATABASE_URL
# If DATABASE_URL needs escaping, use the individual settings
if '@' in settings.DB_PASSWORD:
    escaped_password = quote(settings.DB_PASSWORD, safe="")
    db_url = f"postgresql://{settings.DB_USER}:{escaped_password}@{settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}"

engine = create_engine(
    db_url,
    echo=settings.DEBUG,  # Log all SQL statements in debug mode
    pool_pre_ping=True,   # Verify connections before using
    pool_size=20,
    max_overflow=0
)

# Create session factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

# Base class for all models
Base = declarative_base()

def get_db():
    """
    Dependency for FastAPI to inject database sessions
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    """
    Initialize database - create all tables
    """
    try:
        # Import models to register them
        from app.models import (
            User, Role, Permission, MFAMethod, Session, 
            DeviceRegistry, AuditLog, BehaviorProfile, Anomaly,
            Class, AttendanceRecord, MarksRecord, StudentFees,
            user_roles_association, role_permissions_association
        )
        
        Base.metadata.create_all(bind=engine)
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Error initializing database: {e}")
        raise
