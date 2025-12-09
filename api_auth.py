"""
API Authentication Middleware
Provides token-based authentication for AGI integration endpoints
"""

from functools import wraps
from flask import request, jsonify
import os
import secrets
import hashlib
from typing import Optional

# API token management
# In production, use a secure secrets manager (Vault, AWS Secrets Manager, etc.)
AGI_API_TOKENS = {
    # Generate with: python -c "import secrets; print(secrets.token_urlsafe(32))"
    os.environ.get('AGI_API_TOKEN', 'dev-token-change-in-production'): {
        'name': 'agi-system',
        'permissions': ['read', 'write', 'admin']
    }
}

def generate_api_token() -> str:
    """Generate a secure API token"""
    return secrets.token_urlsafe(32)

def hash_token(token: str) -> str:
    """Hash token for secure storage"""
    return hashlib.sha256(token.encode()).hexdigest()

def validate_token(token: str) -> Optional[dict]:
    """
    Validate an API token and return associated metadata
    Returns None if token is invalid
    """
    return AGI_API_TOKENS.get(token)

def require_api_token(permissions: list = None):
    """
    Decorator to require valid API token for endpoint access
    
    Usage:
        @app.route('/api/secure')
        @require_api_token(['read'])
        def secure_endpoint():
            return jsonify({'data': 'secret'})
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Get token from Authorization header
            auth_header = request.headers.get('Authorization')
            
            if not auth_header:
                return jsonify({
                    'error': 'Missing Authorization header',
                    'message': 'Include: Authorization: Bearer <token>'
                }), 401
            
            # Parse Bearer token
            parts = auth_header.split()
            if len(parts) != 2 or parts[0].lower() != 'bearer':
                return jsonify({
                    'error': 'Invalid Authorization header format',
                    'message': 'Use: Authorization: Bearer <token>'
                }), 401
            
            token = parts[1]
            
            # Validate token
            token_info = validate_token(token)
            if not token_info:
                return jsonify({
                    'error': 'Invalid API token',
                    'message': 'Token not recognized or expired'
                }), 403
            
            # Check permissions if specified
            if permissions:
                token_perms = token_info.get('permissions', [])
                if not any(perm in token_perms for perm in permissions):
                    return jsonify({
                        'error': 'Insufficient permissions',
                        'message': f'Required: {permissions}, Have: {token_perms}'
                    }), 403
            
            # Add token info to request context
            request.api_token_info = token_info
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

# Optional: Rate limiting per token
_token_request_counts = {}

def get_token_request_count(token: str) -> int:
    """Get request count for token (for rate limiting)"""
    return _token_request_counts.get(hash_token(token), 0)

def increment_token_requests(token: str):
    """Increment request count for token"""
    token_hash = hash_token(token)
    _token_request_counts[token_hash] = _token_request_counts.get(token_hash, 0) + 1

# Example usage in app.py:
# from api_auth import require_api_token
#
# @app.route('/api/agi/metrics')
# @require_api_token(['read'])
# def agi_metrics():
#     return jsonify({'metrics': ...})
