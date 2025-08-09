# Error Handling and Logging Strategies

## Technology Stack
- **Logging**: Python logging with structured JSON output
- **Error Tracking**: Sentry for production error monitoring
- **Metrics**: Prometheus with custom metrics
- **Health Checks**: Custom health check endpoints
- **Alerting**: Integration with monitoring systems

## Logging Architecture

### Structured Logging Configuration
```python
import logging
import json
import sys
from datetime import datetime
from typing import Dict, Any, Optional
from contextvars import ContextVar
import uuid

# Context variables for request tracking
request_id_var: ContextVar[Optional[str]] = ContextVar('request_id', default=None)
user_id_var: ContextVar[Optional[str]] = ContextVar('user_id', default=None)
case_id_var: ContextVar[Optional[str]] = ContextVar('case_id', default=None)

class StructuredFormatter(logging.Formatter):
    """Custom formatter for structured JSON logging."""
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as structured JSON."""
        
        # Base log structure
        log_entry = {
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno,
        }
        
        # Add context information
        if request_id := request_id_var.get():
            log_entry['request_id'] = request_id
        
        if user_id := user_id_var.get():
            log_entry['user_id'] = user_id
        
        if case_id := case_id_var.get():
            log_entry['case_id'] = case_id
        
        # Add exception information
        if record.exc_info:
            log_entry['exception'] = {
                'type': record.exc_info[0].__name__,
                'message': str(record.exc_info[1]),
                'traceback': self.formatException(record.exc_info)
            }
        
        # Add extra fields
        if hasattr(record, 'extra_fields'):
            log_entry.update(record.extra_fields)
        
        return json.dumps(log_entry, ensure_ascii=False)

def setup_logging(
    level: str = "INFO",
    enable_console: bool = True,
    log_file: Optional[str] = None
) -> None:
    """Setup application logging configuration."""
    
    # Create root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, level.upper()))
    
    # Remove existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Create formatter
    formatter = StructuredFormatter()
    
    # Console handler
    if enable_console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)
    
    # File handler
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)
    
    # Configure third-party loggers
    logging.getLogger('uvicorn.access').setLevel(logging.WARNING)
    logging.getLogger('sqlalchemy.engine').setLevel(logging.WARNING)
    logging.getLogger('boto3').setLevel(logging.WARNING)
    logging.getLogger('botocore').setLevel(logging.WARNING)

class LoggerMixin:
    """Mixin to add structured logging to classes."""
    
    @property
    def logger(self) -> logging.Logger:
        """Get logger for this class."""
        return logging.getLogger(f"{self.__class__.__module__}.{self.__class__.__name__}")
    
    def log_info(self, message: str, **kwargs):
        """Log info message with extra fields."""
        self.logger.info(message, extra={'extra_fields': kwargs})
    
    def log_warning(self, message: str, **kwargs):
        """Log warning message with extra fields."""
        self.logger.warning(message, extra={'extra_fields': kwargs})
    
    def log_error(self, message: str, exc_info: bool = True, **kwargs):
        """Log error message with extra fields."""
        self.logger.error(message, exc_info=exc_info, extra={'extra_fields': kwargs})
    
    def log_debug(self, message: str, **kwargs):
        """Log debug message with extra fields."""
        self.logger.debug(message, extra={'extra_fields': kwargs})
```

### Request Logging Middleware
```python
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
import time
import uuid

class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for request/response logging and context tracking."""
    
    async def dispatch(self, request: Request, call_next):
        # Generate request ID
        request_id = str(uuid.uuid4())
        request_id_var.set(request_id)
        
        # Extract user ID from token if available
        user_id = self._extract_user_id(request)
        if user_id:
            user_id_var.set(user_id)
        
        # Start timing
        start_time = time.time()
        
        # Log request
        logger = logging.getLogger("api.request")
        logger.info(
            "Request started",
            extra={
                'extra_fields': {
                    'method': request.method,
                    'url': str(request.url),
                    'client_ip': request.client.host,
                    'user_agent': request.headers.get('user-agent'),
                    'content_length': request.headers.get('content-length'),
                }
            }
        )
        
        try:
            # Process request
            response = await call_next(request)
            
            # Calculate duration
            duration = time.time() - start_time
            
            # Log response
            logger.info(
                "Request completed",
                extra={
                    'extra_fields': {
                        'status_code': response.status_code,
                        'duration_ms': round(duration * 1000, 2),
                        'response_size': response.headers.get('content-length'),
                    }
                }
            )
            
            # Add request ID to response headers
            response.headers['X-Request-ID'] = request_id
            
            return response
            
        except Exception as e:
            # Calculate duration
            duration = time.time() - start_time
            
            # Log error
            logger.error(
                "Request failed",
                exc_info=True,
                extra={
                    'extra_fields': {
                        'duration_ms': round(duration * 1000, 2),
                        'error_type': type(e).__name__,
                    }
                }
            )
            
            raise
        
        finally:
            # Clear context
            request_id_var.set(None)
            user_id_var.set(None)
            case_id_var.set(None)
    
    def _extract_user_id(self, request: Request) -> Optional[str]:
        """Extract user ID from JWT token."""
        try:
            auth_header = request.headers.get('authorization')
            if not auth_header or not auth_header.startswith('Bearer '):
                return None
            
            token = auth_header[7:]  # Remove 'Bearer ' prefix
            
            # Decode token (simplified - use proper JWT validation in production)
            import jwt
            from app.core.config import settings
            
            payload = jwt.decode(
                token,
                settings.secret_key,
                algorithms=[settings.algorithm]
            )
            
            return payload.get('sub')
            
        except Exception:
            return None
```

## Error Handling Framework

### Custom Exception Hierarchy
```python
from typing import Optional, Dict, Any
from fastapi import HTTPException, status

class LegalWorkspaceError(Exception):
    """Base exception for legal workspace application."""
    
    def __init__(
        self,
        message: str,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.error_code = error_code or self.__class__.__name__
        self.details = details or {}
        super().__init__(self.message)

class ValidationError(LegalWorkspaceError):
    """Data validation error."""
    pass

class AuthenticationError(LegalWorkspaceError):
    """Authentication error."""
    pass

class AuthorizationError(LegalWorkspaceError):
    """Authorization error."""
    pass

class ResourceNotFoundError(LegalWorkspaceError):
    """Resource not found error."""
    pass

class ConflictError(LegalWorkspaceError):
    """Resource conflict error."""
    pass

class ExternalServiceError(LegalWorkspaceError):
    """External service error."""
    pass

class ContainerError(LegalWorkspaceError):
    """Container operation error."""
    pass

class StorageError(LegalWorkspaceError):
    """Storage operation error."""
    pass

class RateLimitError(LegalWorkspaceError):
    """Rate limit exceeded error."""
    pass

# HTTP Exception mapping
ERROR_STATUS_MAP = {
    ValidationError: status.HTTP_400_BAD_REQUEST,
    AuthenticationError: status.HTTP_401_UNAUTHORIZED,
    AuthorizationError: status.HTTP_403_FORBIDDEN,
    ResourceNotFoundError: status.HTTP_404_NOT_FOUND,
    ConflictError: status.HTTP_409_CONFLICT,
    RateLimitError: status.HTTP_429_TOO_MANY_REQUESTS,
    ExternalServiceError: status.HTTP_502_BAD_GATEWAY,
    ContainerError: status.HTTP_503_SERVICE_UNAVAILABLE,
    StorageError: status.HTTP_503_SERVICE_UNAVAILABLE,
}

def to_http_exception(error: LegalWorkspaceError) -> HTTPException:
    """Convert custom exception to HTTP exception."""
    status_code = ERROR_STATUS_MAP.get(type(error), status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    detail = {
        'message': error.message,
        'error_code': error.error_code,
        'details': error.details
    }
    
    return HTTPException(status_code=status_code, detail=detail)
```

### Global Exception Handler
```python
from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
import logging

logger = logging.getLogger("api.errors")

async def legal_workspace_exception_handler(
    request: Request,
    exc: LegalWorkspaceError
) -> JSONResponse:
    """Handle custom application exceptions."""
    
    # Log the error
    logger.error(
        f"Application error: {exc.message}",
        exc_info=True,
        extra={
            'extra_fields': {
                'error_code': exc.error_code,
                'error_details': exc.details,
                'request_path': request.url.path,
                'request_method': request.method,
            }
        }
    )
    
    # Convert to HTTP exception
    http_exc = to_http_exception(exc)
    
    return JSONResponse(
        status_code=http_exc.status_code,
        content=http_exc.detail
    )

async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError
) -> JSONResponse:
    """Handle request validation errors."""
    
    logger.warning(
        "Validation error",
        extra={
            'extra_fields': {
                'validation_errors': exc.errors(),
                'request_path': request.url.path,
                'request_method': request.method,
            }
        }
    )
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            'message': 'Validation error',
            'error_code': 'VALIDATION_ERROR',
            'details': {
                'validation_errors': exc.errors()
            }
        }
    )

async def http_exception_handler(
    request: Request,
    exc: StarletteHTTPException
) -> JSONResponse:
    """Handle HTTP exceptions."""
    
    logger.warning(
        f"HTTP error: {exc.status_code}",
        extra={
            'extra_fields': {
                'status_code': exc.status_code,
                'detail': exc.detail,
                'request_path': request.url.path,
                'request_method': request.method,
            }
        }
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            'message': exc.detail,
            'error_code': f'HTTP_{exc.status_code}',
            'details': {}
        }
    )

async def unhandled_exception_handler(
    request: Request,
    exc: Exception
) -> JSONResponse:
    """Handle unhandled exceptions."""
    
    logger.error(
        "Unhandled exception",
        exc_info=True,
        extra={
            'extra_fields': {
                'exception_type': type(exc).__name__,
                'request_path': request.url.path,
                'request_method': request.method,
            }
        }
    )
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            'message': 'Internal server error',
            'error_code': 'INTERNAL_ERROR',
            'details': {}
        }
    )

# Register exception handlers
def register_exception_handlers(app):
    """Register all exception handlers with FastAPI app."""
    app.add_exception_handler(LegalWorkspaceError, legal_workspace_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(Exception, unhandled_exception_handler)
```

## Error Recovery and Retry Logic

### Retry Decorator
```python
import asyncio
import functools
from typing import Callable, Type, Tuple, Optional
import random

def async_retry(
    max_attempts: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    jitter: bool = True,
    exceptions: Tuple[Type[Exception], ...] = (Exception,)
):
    """Async retry decorator with exponential backoff."""
    
    def decorator(func: Callable):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(max_attempts):
                try:
                    return await func(*args, **kwargs)
                    
                except exceptions as e:
                    last_exception = e
                    
                    if attempt == max_attempts - 1:
                        # Last attempt, re-raise the exception
                        raise
                    
                    # Calculate delay with exponential backoff
                    current_delay = delay * (backoff ** attempt)
                    
                    # Add jitter to prevent thundering herd
                    if jitter:
                        current_delay *= (0.5 + random.random() * 0.5)
                    
                    logger.warning(
                        f"Attempt {attempt + 1} failed, retrying in {current_delay:.2f}s",
                        extra={
                            'extra_fields': {
                                'function': func.__name__,
                                'attempt': attempt + 1,
                                'max_attempts': max_attempts,
                                'delay': current_delay,
                                'exception': str(e),
                            }
                        }
                    )
                    
                    await asyncio.sleep(current_delay)
            
            # This should never be reached, but just in case
            raise last_exception
        
        return wrapper
    return decorator

# Usage example
@async_retry(
    max_attempts=3,
    delay=1.0,
    exceptions=(StorageError, ExternalServiceError)
)
async def upload_to_storage(key: str, content: bytes):
    """Upload with automatic retry on failure."""
    # Implementation here
    pass
```

## Health Checks and Monitoring

### Health Check System
```python
from typing import Dict, Any, List
from enum import Enum
import asyncio
import time

class HealthStatus(str, Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"

class HealthCheck:
    """Individual health check."""
    
    def __init__(self, name: str, check_func: Callable, timeout: float = 5.0):
        self.name = name
        self.check_func = check_func
        self.timeout = timeout
    
    async def run(self) -> Dict[str, Any]:
        """Run health check with timeout."""
        start_time = time.time()
        
        try:
            result = await asyncio.wait_for(
                self.check_func(),
                timeout=self.timeout
            )
            
            duration = time.time() - start_time
            
            return {
                'name': self.name,
                'status': HealthStatus.HEALTHY,
                'duration_ms': round(duration * 1000, 2),
                'details': result
            }
            
        except asyncio.TimeoutError:
            duration = time.time() - start_time
            return {
                'name': self.name,
                'status': HealthStatus.UNHEALTHY,
                'duration_ms': round(duration * 1000, 2),
                'error': 'Health check timeout'
            }
            
        except Exception as e:
            duration = time.time() - start_time
            return {
                'name': self.name,
                'status': HealthStatus.UNHEALTHY,
                'duration_ms': round(duration * 1000, 2),
                'error': str(e)
            }

class HealthCheckService:
    """Service for managing health checks."""
    
    def __init__(self):
        self.checks: List[HealthCheck] = []
    
    def add_check(self, check: HealthCheck):
        """Add health check."""
        self.checks.append(check)
    
    async def run_all_checks(self) -> Dict[str, Any]:
        """Run all health checks."""
        start_time = time.time()
        
        # Run all checks concurrently
        results = await asyncio.gather(
            *[check.run() for check in self.checks],
            return_exceptions=True
        )
        
        # Process results
        check_results = []
        overall_status = HealthStatus.HEALTHY
        
        for result in results:
            if isinstance(result, Exception):
                check_results.append({
                    'name': 'unknown',
                    'status': HealthStatus.UNHEALTHY,
                    'error': str(result)
                })
                overall_status = HealthStatus.UNHEALTHY
            else:
                check_results.append(result)
                if result['status'] == HealthStatus.UNHEALTHY:
                    overall_status = HealthStatus.UNHEALTHY
                elif result['status'] == HealthStatus.DEGRADED and overall_status == HealthStatus.HEALTHY:
                    overall_status = HealthStatus.DEGRADED
        
        total_duration = time.time() - start_time
        
        return {
            'status': overall_status,
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'duration_ms': round(total_duration * 1000, 2),
            'checks': check_results
        }

# Health check implementations
async def database_health_check() -> Dict[str, Any]:
    """Check database connectivity."""
    try:
        async with AsyncSessionLocal() as session:
            result = await session.execute(text("SELECT 1"))
            return {'database': 'connected'}
    except Exception as e:
        raise HealthCheckError(f"Database check failed: {e}")

async def storage_health_check() -> Dict[str, Any]:
    """Check storage service connectivity."""
    try:
        storage = get_storage_service()
        # Try to list objects (lightweight operation)
        objects = await storage.list_objects(prefix="health-check", max_keys=1)
        return {'storage': 'connected'}
    except Exception as e:
        raise HealthCheckError(f"Storage check failed: {e}")

async def container_health_check() -> Dict[str, Any]:
    """Check container service health."""
    try:
        container_manager = get_container_manager()
        # Check Docker daemon connectivity
        info = container_manager.docker_client.info()
        return {
            'docker': 'connected',
            'containers_running': info.get('ContainersRunning', 0)
        }
    except Exception as e:
        raise HealthCheckError(f"Container check failed: {e}")

# Setup health checks
health_service = HealthCheckService()
health_service.add_check(HealthCheck("database", database_health_check))
health_service.add_check(HealthCheck("storage", storage_health_check))
health_service.add_check(HealthCheck("containers", container_health_check))
```

## Metrics and Monitoring

### Custom Metrics
```python
from prometheus_client import Counter, Histogram, Gauge, generate_latest
import time

# Define metrics
request_count = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status_code']
)

request_duration = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration',
    ['method', 'endpoint']
)

active_containers = Gauge(
    'active_containers_total',
    'Number of active containers'
)

file_upload_count = Counter(
    'file_uploads_total',
    'Total file uploads',
    ['status']
)

file_upload_size = Histogram(
    'file_upload_size_bytes',
    'File upload size in bytes'
)

database_connections = Gauge(
    'database_connections_active',
    'Active database connections'
)

class MetricsMiddleware(BaseHTTPMiddleware):
    """Middleware for collecting HTTP metrics."""
    
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        
        try:
            response = await call_next(request)
            
            # Record metrics
            duration = time.time() - start_time
            
            request_count.labels(
                method=request.method,
                endpoint=request.url.path,
                status_code=response.status_code
            ).inc()
            
            request_duration.labels(
                method=request.method,
                endpoint=request.url.path
            ).observe(duration)
            
            return response
            
        except Exception as e:
            # Record error metrics
            request_count.labels(
                method=request.method,
                endpoint=request.url.path,
                status_code=500
            ).inc()
            
            raise

# Metrics endpoint
@app.get("/metrics")
async def get_metrics():
    """Prometheus metrics endpoint."""
    return Response(
        generate_latest(),
        media_type="text/plain"
    )
```

This comprehensive error handling and logging system provides structured logging, proper exception handling, health checks, and metrics collection for robust production operation of the legal workspace application.
