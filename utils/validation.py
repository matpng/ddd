#!/usr/bin/env python3
"""
Utility functions for validation and error handling
"""

from typing import Any, Dict, Tuple, Optional
import numpy as np
from models.exceptions import InvalidParameterError, ValidationError


def validate_side_length(side: float, min_val: float = 0.01, max_val: float = 100.0) -> float:
    """
    Validate cube side length parameter.
    
    Args:
        side: Side length to validate
        min_val: Minimum allowed value
        max_val: Maximum allowed value
        
    Returns:
        Validated side length
        
    Raises:
        InvalidParameterError: If side length is out of bounds
    """
    if not isinstance(side, (int, float)):
        raise InvalidParameterError('side', side, 'must be a number')
    
    if not (min_val <= side <= max_val):
        raise InvalidParameterError(
            'side', 
            side, 
            f'must be between {min_val} and {max_val}'
        )
    
    return float(side)


def validate_angle(angle: float, min_val: float = 0.0, max_val: float = 360.0) -> float:
    """
    Validate rotation angle parameter.
    
    Args:
        angle: Angle in degrees to validate
        min_val: Minimum allowed value
        max_val: Maximum allowed value
        
    Returns:
        Validated angle
        
    Raises:
        InvalidParameterError: If angle is out of bounds
    """
    if not isinstance(angle, (int, float)):
        raise InvalidParameterError('angle', angle, 'must be a number')
    
    if not (min_val <= angle <= max_val):
        raise InvalidParameterError(
            'angle',
            angle,
            f'must be between {min_val} and {max_val} degrees'
        )
    
    return float(angle)


def validate_sample_count(count: int, max_val: int, param_name: str = 'sample_count') -> int:
    """
    Validate sampling parameter (e.g., max_distance_pairs).
    
    Args:
        count: Sample count to validate
        max_val: Maximum allowed value
        param_name: Parameter name for error messages
        
    Returns:
        Validated count
        
    Raises:
        InvalidParameterError: If count is invalid
    """
    if not isinstance(count, int):
        try:
            count = int(count)
        except (ValueError, TypeError):
            raise InvalidParameterError(param_name, count, 'must be an integer')
    
    if count <= 0:
        raise InvalidParameterError(param_name, count, 'must be positive')
    
    if count > max_val:
        raise InvalidParameterError(
            param_name,
            count,
            f'must not exceed {max_val}'
        )
    
    return count


def validate_analysis_params(
    params: Dict[str, Any],
    config: Any
) -> Tuple[float, float, int, int]:
    """
    Validate all analysis parameters at once.
    
    Args:
        params: Dictionary of parameters
        config: Configuration object with limits
        
    Returns:
        Tuple of (side, angle, max_distance_pairs, max_direction_pairs)
        
    Raises:
        ValidationError: If any parameter is invalid
    """
    try:
        side = validate_side_length(
            params.get('side', config.DEFAULT_SIDE),
            min_val=config.MIN_SIDE_LENGTH,
            max_val=config.MAX_SIDE_LENGTH
        )
        
        angle = validate_angle(
            params.get('angle', config.DEFAULT_ANGLE),
            min_val=config.MIN_ANGLE,
            max_val=config.MAX_ANGLE
        )
        
        max_distance_pairs = validate_sample_count(
            params.get('max_distance_pairs', config.DEFAULT_DISTANCE_PAIRS),
            max_val=config.MAX_DISTANCE_PAIRS,
            param_name='max_distance_pairs'
        )
        
        max_direction_pairs = validate_sample_count(
            params.get('max_direction_pairs', config.DEFAULT_DIRECTION_PAIRS),
            max_val=config.MAX_DIRECTION_PAIRS,
            param_name='max_direction_pairs'
        )
        
        return side, angle, max_distance_pairs, max_direction_pairs
        
    except InvalidParameterError as e:
        raise ValidationError(e.parameter_name, e.value, str(e))


def safe_divide(a: float, b: float, default: float = 0.0) -> float:
    """
    Safely divide two numbers, returning default if division by zero.
    
    Args:
        a: Numerator
        b: Denominator
        default: Value to return if b is zero
        
    Returns:
        Result of a/b or default
    """
    if abs(b) < 1e-10:
        return default
    return a / b


def clamp(value: float, min_val: float, max_val: float) -> float:
    """
    Clamp a value between min and max.
    
    Args:
        value: Value to clamp
        min_val: Minimum value
        max_val: Maximum value
        
    Returns:
        Clamped value
    """
    return max(min_val, min(max_val, value))


def format_number(value: float, precision: int = 6) -> str:
    """
    Format a number for display with appropriate precision.
    
    Args:
        value: Number to format
        precision: Number of decimal places
        
    Returns:
        Formatted string
    """
    if abs(value) < 1e-10:
        return "0.0"
    
    if abs(value) >= 1000:
        return f"{value:.2e}"
    
    return f"{value:.{precision}f}"


def dict_to_summary(data: Dict[str, Any], max_depth: int = 2, current_depth: int = 0) -> str:
    """
    Convert a dictionary to a human-readable summary string.
    
    Args:
        data: Dictionary to summarize
        max_depth: Maximum nesting depth
        current_depth: Current depth (for recursion)
        
    Returns:
        Summary string
    """
    if current_depth >= max_depth:
        return f"<{type(data).__name__} with {len(data)} items>"
    
    lines = []
    indent = "  " * current_depth
    
    for key, value in data.items():
        if isinstance(value, dict):
            lines.append(f"{indent}{key}:")
            lines.append(dict_to_summary(value, max_depth, current_depth + 1))
        elif isinstance(value, (list, tuple)) and len(value) > 0:
            lines.append(f"{indent}{key}: [{len(value)} items]")
        elif isinstance(value, (int, float, str, bool)):
            lines.append(f"{indent}{key}: {value}")
        else:
            lines.append(f"{indent}{key}: <{type(value).__name__}>")
    
    return "\n".join(lines)


def sanitize_filename(filename: str, max_length: int = 200) -> str:
    """
    Sanitize a filename by removing invalid characters.
    
    Args:
        filename: Original filename
        max_length: Maximum filename length
        
    Returns:
        Sanitized filename
    """
    import re
    
    # Remove invalid characters
    filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
    
    # Remove control characters
    filename = ''.join(char for char in filename if ord(char) >= 32)
    
    # Trim to max length
    if len(filename) > max_length:
        filename = filename[:max_length]
    
    # Remove leading/trailing spaces and dots
    filename = filename.strip('. ')
    
    if not filename:
        filename = 'unnamed'
    
    return filename


def calculate_percentage(part: float, total: float, precision: int = 1) -> str:
    """
    Calculate percentage with safe division.
    
    Args:
        part: Part value
        total: Total value
        precision: Decimal places
        
    Returns:
        Formatted percentage string
    """
    if total == 0:
        return "0.0%"
    
    percentage = (part / total) * 100
    return f"{percentage:.{precision}f}%"
