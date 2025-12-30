"""
Shared Utilities for PDF Services.

Provides standardized logging and performance instrumentation.
"""

import logging
import time
import functools
from typing import Callable, Any, Optional

# Try importing structlog for JSON logging, fallback to standard
try:
    import structlog
    STRUCTLOG_AVAILABLE = True
except ImportError:
    STRUCTLOG_AVAILABLE = False


def get_logger(name: str):
    """
    Get a pre-configured logger instance.
    
    Returns a structlog logger if available, otherwise a standard logger
    wrapped to behave similarly.
    """
    if STRUCTLOG_AVAILABLE:
        return structlog.get_logger(name)
    else:
        return logging.getLogger(name)



# =============================================================================
# Performance Warning Thresholds (Placeholders for SLA enforcement)
# =============================================================================
WARN_SLOW_OPERATION_THRESHOLD = 2.0  # Seconds
MAX_OPERATION_TIMEOUT = 30.0         # Seconds (for future timeout logic)


def benchmark(operation_name: str, warn_threshold: float = WARN_SLOW_OPERATION_THRESHOLD):
    """
    Decorator to measure and log execution time of a function.
    
    Args:
        operation_name: Human-readable name of the operation.
        warn_threshold: Seconds after which to log a warning (SLA breach).
    """
    def decorator(func: Callable):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            logger = get_logger(func.__module__)
            start_time = time.perf_counter()
            
            try:
                result = func(*args, **kwargs)
                duration = time.perf_counter() - start_time
                
                if hasattr(logger, "info"):
                    # Handle both standard and structlog
                    if STRUCTLOG_AVAILABLE:
                         logger.info(f"{operation_name}_complete", duration_seconds=duration)
                    else:
                         logger.info(f"{operation_name} completed in {duration:.4f}s")
                
                # Check performance threshold
                if duration > warn_threshold:
                    msg = f"⚠️ Performance Warning: {operation_name} took {duration:.2f}s (Threshold: {warn_threshold}s)"
                    if hasattr(logger, "warning"):
                        logger.warning(msg)
                
                return result
            except Exception as e:
                duration = time.perf_counter() - start_time
                if hasattr(logger, "error"):
                     if STRUCTLOG_AVAILABLE:
                          logger.error(f"{operation_name}_failed", duration_seconds=duration, error=str(e))
                     else:
                          logger.error(f"{operation_name} failed after {duration:.4f}s: {e}")
                raise
        return wrapper
    return decorator


class PerformanceTimer:
    """Context manager for fine-grained timing."""
    
    def __init__(self, name: str, logger: Optional[Any] = None):
        self.name = name
        self.logger = logger or get_logger(__name__)
        self.start_time = 0
        self.duration = 0
        
    def __enter__(self):
        self.start_time = time.perf_counter()
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.duration = time.perf_counter() - self.start_time
        if exc_type:
            status = "failed"
            error_info = f" error={str(exc_val)}"
        else:
            status = "completed"
            error_info = ""
            
        msg = f"⏱️  {self.name} {status} in {self.duration:.4f}s{error_info}"
        
        if self.logger:
            self.logger.info(msg)
