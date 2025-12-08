#!/usr/bin/env python3
"""
Custom Exception Classes for Orion Octave Cubes
Provides domain-specific exceptions for better error handling
"""


class GeometryError(Exception):
    """Base exception for all geometry-related errors."""
    pass


class InvalidParameterError(GeometryError):
    """Raised when invalid parameters are provided to geometry functions."""
    
    def __init__(self, parameter_name: str, value, reason: str = ""):
        self.parameter_name = parameter_name
        self.value = value
        self.reason = reason
        message = f"Invalid parameter '{parameter_name}': {value}"
        if reason:
            message += f" - {reason}"
        super().__init__(message)


class CalculationError(GeometryError):
    """Raised when a geometric calculation fails."""
    
    def __init__(self, operation: str, details: str = ""):
        self.operation = operation
        self.details = details
        message = f"Calculation failed during {operation}"
        if details:
            message += f": {details}"
        super().__init__(message)


class IntersectionError(GeometryError):
    """Raised when intersection computation fails."""
    
    def __init__(self, geometry_type: str, reason: str = ""):
        self.geometry_type = geometry_type
        self.reason = reason
        message = f"Intersection computation failed for {geometry_type}"
        if reason:
            message += f": {reason}"
        super().__init__(message)


class CacheError(Exception):
    """Base exception for cache-related errors."""
    pass


class CacheKeyError(CacheError):
    """Raised when a cache key is not found."""
    
    def __init__(self, key: str):
        self.key = key
        super().__init__(f"Cache key not found: {key}")


class CacheSizeError(CacheError):
    """Raised when cache size limits are exceeded."""
    
    def __init__(self, current_size: int, max_size: int):
        self.current_size = current_size
        self.max_size = max_size
        super().__init__(f"Cache size {current_size} exceeds maximum {max_size}")


class DiscoveryError(Exception):
    """Base exception for discovery-related errors."""
    pass


class DiscoveryNotFoundError(DiscoveryError):
    """Raised when a discovery is not found."""
    
    def __init__(self, discovery_id: str):
        self.discovery_id = discovery_id
        super().__init__(f"Discovery not found: {discovery_id}")


class DiscoveryGenerationError(DiscoveryError):
    """Raised when discovery generation fails."""
    
    def __init__(self, discovery_type: str, reason: str = ""):
        self.discovery_type = discovery_type
        self.reason = reason
        message = f"Failed to generate {discovery_type} discovery"
        if reason:
            message += f": {reason}"
        super().__init__(message)


class ValidationError(Exception):
    """Raised when input validation fails."""
    
    def __init__(self, field: str, value, constraint: str):
        self.field = field
        self.value = value
        self.constraint = constraint
        super().__init__(f"Validation failed for '{field}': {value} - {constraint}")


class APIError(Exception):
    """Base exception for API-related errors."""
    
    def __init__(self, message: str, status_code: int = 400):
        self.message = message
        self.status_code = status_code
        super().__init__(message)


class RateLimitError(APIError):
    """Raised when rate limit is exceeded."""
    
    def __init__(self, retry_after: int, limit_type: str = "default"):
        self.retry_after = retry_after
        self.limit_type = limit_type
        message = f"Rate limit exceeded for {limit_type}. Retry after {retry_after} seconds."
        super().__init__(message, status_code=429)
