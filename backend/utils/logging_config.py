# Structured Logging with Correlation IDs
# Enables production debugging by tracing requests across systems

import logging
import json
import uuid
from datetime import datetime
from typing import Any, Dict, Optional
from contextlib import contextmanager
import structlog
from pythonjsonlogger import jsonlogger

# Context variable for storing correlation ID
_correlation_id_context = {}

class CorrelationIdFilter(logging.Filter):
    """
    Adds correlation ID to every log record
    Enables tracing requests across distributed systems
    """
    
    def filter(self, record):
        correlation_id = _correlation_id_context.get(
            "correlation_id",
            str(uuid.uuid4())
        )
        record.correlation_id = correlation_id
        record.timestamp = datetime.utcnow().isoformat()
        return True

def setup_structured_logging(log_level=logging.INFO):
    """
    Configure structured JSON logging for production
    All logs output as JSON for easy parsing in ELK/Splunk/CloudWatch
    """
    
    # Get root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    
    # Create console handler for JSON output
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(
        jsonlogger.JsonFormatter(
            '%(timestamp)s %(level)s %(correlation_id)s %(name)s %(message)s'
        )
    )
    
    # Add correlation ID filter
    console_handler.addFilter(CorrelationIdFilter())
    
    # Remove existing handlers and add new one
    root_logger.handlers.clear()
    root_logger.addHandler(console_handler)
    
    # Configure structlog
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer()
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True
    )
    
    return root_logger

def get_logger(name: str) -> logging.Logger:
    """Get a logger with structured logging capabilities"""
    return logging.getLogger(name)

@contextmanager
def correlation_id(request_id: Optional[str] = None):
    """
    Context manager for correlation ID
    Usage: with correlation_id("request-123"): ...
    """
    
    if request_id is None:
        request_id = str(uuid.uuid4())
    
    old_id = _correlation_id_context.get("correlation_id")
    _correlation_id_context["correlation_id"] = request_id
    
    try:
        yield request_id
    finally:
        if old_id is None:
            _correlation_id_context.pop("correlation_id", None)
        else:
            _correlation_id_context["correlation_id"] = old_id

def set_correlation_id(request_id: str):
    """Set correlation ID for current request"""
    _correlation_id_context["correlation_id"] = request_id

def get_correlation_id() -> str:
    """Get current correlation ID"""
    return _correlation_id_context.get(
        "correlation_id",
        str(uuid.uuid4())
    )

class ProductionLogger:
    """
    Wrapper for production-grade logging with:
    - Automatic correlation ID injection
    - Structured context information
    - Performance metrics
    - Error tracking
    """
    
    def __init__(self, name: str):
        self.logger = get_logger(name)
        self.correlation_id = get_correlation_id()
    
    def info(
        self,
        message: str,
        extra: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> None:
        """Log info with correlation ID and context"""
        context = {
            "correlation_id": self.correlation_id,
            **(extra or {}),
            **kwargs
        }
        self.logger.info(message, extra=context)
    
    def error(
        self,
        message: str,
        exception: Optional[Exception] = None,
        extra: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> None:
        """Log error with stack trace and context"""
        context = {
            "correlation_id": self.correlation_id,
            "error_type": type(exception).__name__ if exception else None,
            **(extra or {}),
            **kwargs
        }
        self.logger.error(message, exc_info=exception, extra=context)
    
    def warning(
        self,
        message: str,
        extra: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> None:
        """Log warning with correlation ID"""
        context = {
            "correlation_id": self.correlation_id,
            **(extra or {}),
            **kwargs
        }
        self.logger.warning(message, extra=context)
    
    def debug(
        self,
        message: str,
        extra: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> None:
        """Log debug information"""
        context = {
            "correlation_id": self.correlation_id,
            **(extra or {}),
            **kwargs
        }
        self.logger.debug(message, extra=context)
