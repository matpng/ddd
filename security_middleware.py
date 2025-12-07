#!/usr/bin/env python3
"""
Security Middleware for Flask Application
Includes rate limiting, CORS, request validation, and security headers
"""

import os
from functools import wraps
from flask import request, jsonify, make_response
from datetime import datetime, timedelta
from collections import defaultdict
import threading
import logging
import re
import hashlib

logger = logging.getLogger(__name__)


# ============================================================================
# RATE LIMITING
# ============================================================================

class RateLimiter:
    """
    Token bucket rate limiter with per-IP tracking.
    Supports both global and per-endpoint limits.
    """
    
    def __init__(self):
        self.buckets = defaultdict(lambda: {'tokens': 0, 'last_update': datetime.utcnow()})
        self.lock = threading.Lock()
        
        # Rate limit configurations (requests per minute)
        self.limits = {
            'default': 60,          # 60 requests/minute for most endpoints
            'analyze': 10,          # 10 analysis requests/minute (expensive)
            'ml_analyze': 5,        # 5 ML analysis requests/minute (very expensive)
            'download': 30,         # 30 downloads/minute
            'search': 30,           # 30 search requests/minute
        }
        
        # Burst allowances
        self.burst_limits = {
            'default': 10,
            'analyze': 3,
            'ml_analyze': 2,
            'download': 5,
            'search': 5,
        }
    
    def _get_client_id(self):
        """Get unique client identifier (IP + User-Agent hash)."""
        ip = request.remote_addr or 'unknown'
        user_agent = request.headers.get('User-Agent', '')
        ua_hash = hashlib.md5(user_agent.encode()).hexdigest()[:8]
        return f"{ip}:{ua_hash}"
    
    def _refill_tokens(self, bucket, limit_type='default'):
        """Refill tokens based on elapsed time (token bucket algorithm)."""
        now = datetime.utcnow()
        elapsed = (now - bucket['last_update']).total_seconds()
        
        # Tokens refill at rate per second
        rate_per_second = self.limits[limit_type] / 60.0
        tokens_to_add = elapsed * rate_per_second
        
        max_tokens = self.limits[limit_type] + self.burst_limits[limit_type]
        bucket['tokens'] = min(bucket['tokens'] + tokens_to_add, max_tokens)
        bucket['last_update'] = now
    
    def check_rate_limit(self, limit_type='default'):
        """
        Check if request is within rate limit.
        Returns (allowed: bool, retry_after: int)
        """
        client_id = self._get_client_id()
        key = f"{client_id}:{limit_type}"
        
        with self.lock:
            bucket = self.buckets[key]
            self._refill_tokens(bucket, limit_type)
            
            if bucket['tokens'] >= 1.0:
                bucket['tokens'] -= 1.0
                return True, 0
            else:
                # Calculate retry_after (seconds until 1 token available)
                rate_per_second = self.limits[limit_type] / 60.0
                tokens_needed = 1.0 - bucket['tokens']
                retry_after = int(tokens_needed / rate_per_second) + 1
                return False, retry_after
    
    def reset_client(self, client_id=None):
        """Reset rate limit for a client (useful for testing)."""
        if client_id is None:
            client_id = self._get_client_id()
        
        with self.lock:
            # Remove all buckets for this client
            keys_to_remove = [k for k in self.buckets.keys() if k.startswith(client_id)]
            for key in keys_to_remove:
                del self.buckets[key]


# Global rate limiter instance
rate_limiter = RateLimiter()


def rate_limit(limit_type='default'):
    """
    Decorator to apply rate limiting to Flask routes.
    
    Usage:
        @app.route('/api/analyze')
        @rate_limit('analyze')
        def analyze():
            ...
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            allowed, retry_after = rate_limiter.check_rate_limit(limit_type)
            
            if not allowed:
                logger.warning(f"Rate limit exceeded for {request.remote_addr} on {request.path}")
                response = jsonify({
                    'error': 'Rate limit exceeded',
                    'retry_after': retry_after,
                    'limit_type': limit_type,
                    'message': f'Please wait {retry_after} seconds before retrying'
                })
                response.status_code = 429
                response.headers['Retry-After'] = str(retry_after)
                response.headers['X-RateLimit-Limit'] = str(rate_limiter.limits[limit_type])
                response.headers['X-RateLimit-Remaining'] = '0'
                return response
            
            # Add rate limit headers to successful response
            response = make_response(f(*args, **kwargs))
            response.headers['X-RateLimit-Limit'] = str(rate_limiter.limits[limit_type])
            return response
        
        return decorated_function
    return decorator


# ============================================================================
# CORS CONFIGURATION
# ============================================================================

def configure_cors(app):
    """
    Configure CORS (Cross-Origin Resource Sharing) for the Flask app.
    Allows frontend to make requests from different origins.
    """
    
    @app.after_request
    def add_cors_headers(response):
        # Allow requests from localhost during development
        origin = request.headers.get('Origin')
        
        # Whitelist of allowed origins
        allowed_origins = [
            'http://localhost:5000',
            'http://127.0.0.1:5000',
            'http://localhost:3000',  # Common frontend dev server
        ]
        
        # In production, add your actual domain
        if app.config.get('ENV') == 'production':
            # Add production origins from environment variable
            production_origins = os.environ.get('ALLOWED_ORIGINS', '').split(',')
            allowed_origins.extend([origin.strip() for origin in production_origins if origin.strip()])
        
        if origin in allowed_origins or app.config.get('DEBUG'):
            response.headers['Access-Control-Allow-Origin'] = origin or '*'
            response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
            response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization, X-Requested-With'
            response.headers['Access-Control-Max-Age'] = '3600'
        
        return response
    
    @app.route('/api/cors-check', methods=['OPTIONS', 'GET'])
    def cors_check():
        """Simple endpoint to check CORS configuration."""
        return jsonify({'cors': 'enabled', 'origin': request.headers.get('Origin')})


# ============================================================================
# SECURITY HEADERS
# ============================================================================

def add_security_headers(app):
    """Add security headers to all responses."""
    
    @app.after_request
    def set_security_headers(response):
        # Prevent clickjacking
        response.headers['X-Frame-Options'] = 'SAMEORIGIN'
        
        # Prevent MIME sniffing
        response.headers['X-Content-Type-Options'] = 'nosniff'
        
        # Enable XSS protection
        response.headers['X-XSS-Protection'] = '1; mode=block'
        
        # Content Security Policy (adjust as needed)
        if not app.config.get('DEBUG'):
            response.headers['Content-Security-Policy'] = (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
                "style-src 'self' 'unsafe-inline'; "
                "img-src 'self' data:; "
                "font-src 'self' data:;"
            )
        
        # Referrer policy
        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        
        # Don't send server version
        response.headers.pop('Server', None)
        
        return response


# ============================================================================
# REQUEST VALIDATION
# ============================================================================

class RequestValidator:
    """Validate incoming requests for security issues."""
    
    # Regex patterns for validation
    SQL_INJECTION_PATTERN = re.compile(r"(\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC|EXECUTE)\b)", re.IGNORECASE)
    XSS_PATTERN = re.compile(r"<script[^>]*>.*?</script>", re.IGNORECASE | re.DOTALL)
    PATH_TRAVERSAL_PATTERN = re.compile(r"\.\./|\.\.\\")
    
    @staticmethod
    def validate_json_payload(data, max_size_kb=100):
        """
        Validate JSON payload for common security issues.
        Returns (is_valid: bool, error_message: str or None)
        """
        if data is None:
            return True, None
        
        # Check payload size
        import json
        payload_size = len(json.dumps(data)) / 1024
        if payload_size > max_size_kb:
            return False, f"Payload too large ({payload_size:.1f}KB > {max_size_kb}KB)"
        
        # Check for suspicious patterns in string values
        def check_value(value):
            if isinstance(value, str):
                if RequestValidator.SQL_INJECTION_PATTERN.search(value):
                    return False, "Potential SQL injection detected"
                if RequestValidator.XSS_PATTERN.search(value):
                    return False, "Potential XSS detected"
                if RequestValidator.PATH_TRAVERSAL_PATTERN.search(value):
                    return False, "Potential path traversal detected"
            elif isinstance(value, dict):
                for v in value.values():
                    valid, error = check_value(v)
                    if not valid:
                        return valid, error
            elif isinstance(value, list):
                for item in value:
                    valid, error = check_value(item)
                    if not valid:
                        return valid, error
            return True, None
        
        return check_value(data)
    
    @staticmethod
    def validate_query_params():
        """Validate URL query parameters."""
        for key, value in request.args.items():
            if RequestValidator.SQL_INJECTION_PATTERN.search(value):
                return False, f"Suspicious pattern in parameter '{key}'"
            if RequestValidator.PATH_TRAVERSAL_PATTERN.search(value):
                return False, f"Path traversal attempt in parameter '{key}'"
            if len(value) > 1000:
                return False, f"Parameter '{key}' too long"
        
        return True, None


def validate_request(max_payload_kb=100):
    """
    Decorator to validate requests before processing.
    
    Usage:
        @app.route('/api/analyze', methods=['POST'])
        @validate_request(max_payload_kb=50)
        def analyze():
            ...
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Validate query parameters
            valid, error = RequestValidator.validate_query_params()
            if not valid:
                logger.warning(f"Invalid query params from {request.remote_addr}: {error}")
                return jsonify({'error': 'Invalid request parameters', 'details': error}), 400
            
            # Validate JSON payload for POST/PUT requests
            if request.method in ['POST', 'PUT']:
                try:
                    data = request.get_json(silent=True)
                    valid, error = RequestValidator.validate_json_payload(data, max_payload_kb)
                    if not valid:
                        logger.warning(f"Invalid payload from {request.remote_addr}: {error}")
                        return jsonify({'error': 'Invalid request payload', 'details': error}), 400
                except Exception as e:
                    logger.error(f"Error validating request: {e}")
                    return jsonify({'error': 'Request validation failed'}), 400
            
            return f(*args, **kwargs)
        
        return decorated_function
    return decorator


# ============================================================================
# INITIALIZATION FUNCTION
# ============================================================================

def initialize_security(app):
    """
    Initialize all security middleware for the Flask app.
    
    Usage in app.py:
        from security_middleware import initialize_security
        
        app = Flask(__name__)
        initialize_security(app)
    """
    logger.info("Initializing security middleware...")
    
    # Configure CORS
    configure_cors(app)
    logger.info("✓ CORS configured")
    
    # Add security headers
    add_security_headers(app)
    logger.info("✓ Security headers configured")
    
    # Log rate limiter initialization
    logger.info(f"✓ Rate limiter initialized (default: {rate_limiter.limits['default']}/min)")
    
    logger.info("Security middleware initialization complete")


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def get_rate_limit_status(client_id=None):
    """Get current rate limit status for a client (for monitoring)."""
    if client_id is None:
        client_id = rate_limiter._get_client_id()
    
    status = {}
    with rate_limiter.lock:
        for key, bucket in rate_limiter.buckets.items():
            if key.startswith(client_id):
                limit_type = key.split(':')[-1]
                status[limit_type] = {
                    'tokens': bucket['tokens'],
                    'max_tokens': rate_limiter.limits[limit_type] + rate_limiter.burst_limits[limit_type],
                    'limit_per_minute': rate_limiter.limits[limit_type],
                    'last_update': bucket['last_update'].isoformat()
                }
    
    return status
