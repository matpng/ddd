#!/usr/bin/env python3
"""
Example: Using Custom Exceptions and Validation Utilities

This example demonstrates how to use the new exception handling
and validation utilities in your code.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from models.exceptions import (
    InvalidParameterError,
    CalculationError,
    ValidationError
)
from utils.validation import (
    validate_side_length,
    validate_angle,
    validate_analysis_params,
    safe_divide,
    format_number
)
from config import Config


def example_1_basic_validation():
    """Example 1: Basic parameter validation."""
    print("=" * 70)
    print("Example 1: Basic Parameter Validation")
    print("=" * 70)
    
    # Valid parameters
    try:
        side = validate_side_length(2.5, min_val=0.01, max_val=100.0)
        angle = validate_angle(45.0, min_val=0.0, max_val=360.0)
        print(f"✓ Valid parameters: side={side}, angle={angle}")
    except InvalidParameterError as e:
        print(f"✗ Error: {e}")
    
    # Invalid parameters
    try:
        side = validate_side_length(-1.0)  # Negative value
        print(f"Side: {side}")
    except InvalidParameterError as e:
        print(f"✓ Caught expected error: {e}")
    
    print()


def example_2_comprehensive_validation():
    """Example 2: Validate all analysis parameters at once."""
    print("=" * 70)
    print("Example 2: Comprehensive Validation")
    print("=" * 70)
    
    # Valid parameters dictionary
    params = {
        'side': 2.0,
        'angle': 30.0,
        'max_distance_pairs': 5000,
        'max_direction_pairs': 2000
    }
    
    try:
        side, angle, max_dist, max_dir = validate_analysis_params(params, Config)
        print(f"✓ All parameters valid:")
        print(f"  - Side length: {side}")
        print(f"  - Angle: {angle}°")
        print(f"  - Max distance pairs: {max_dist}")
        print(f"  - Max direction pairs: {max_dir}")
    except ValidationError as e:
        print(f"✗ Validation failed: {e}")
    
    # Invalid parameters
    invalid_params = {
        'side': 200.0,  # Too large
        'angle': 30.0
    }
    
    try:
        validate_analysis_params(invalid_params, Config)
    except ValidationError as e:
        print(f"✓ Caught expected error: {e}")
    
    print()


def example_3_safe_operations():
    """Example 3: Safe mathematical operations."""
    print("=" * 70)
    print("Example 3: Safe Mathematical Operations")
    print("=" * 70)
    
    # Safe division
    result1 = safe_divide(10.0, 2.0)
    result2 = safe_divide(10.0, 0.0, default=0.0)
    result3 = safe_divide(10.0, 1e-15, default=0.0)
    
    print(f"10 / 2 = {result1}")
    print(f"10 / 0 = {result2} (safe, returned default)")
    print(f"10 / 1e-15 = {result3} (safe, returned default)")
    
    # Format numbers
    numbers = [0.0, 1e-12, 3.141592653589793, 1234.5678, 12345.6789]
    print("\nFormatted numbers:")
    for num in numbers:
        formatted = format_number(num, precision=6)
        print(f"  {num:15.10f} → {formatted}")
    
    print()


def example_4_custom_exceptions():
    """Example 4: Using custom exceptions in your code."""
    print("=" * 70)
    print("Example 4: Custom Exception Handling")
    print("=" * 70)
    
    def analyze_geometry(side: float) -> dict:
        """Example function using custom exceptions."""
        if side <= 0:
            raise InvalidParameterError('side', side, 'must be positive')
        
        if side > 1000:
            raise InvalidParameterError('side', side, 'too large for analysis')
        
        # Simulate calculation
        try:
            result = 100.0 / side
            if result < 0.001:
                raise CalculationError('geometry analysis', 'result too small')
        except ZeroDivisionError:
            raise CalculationError('geometry analysis', 'division by zero')
        
        return {'side': side, 'result': result}
    
    # Test with valid value
    try:
        result = analyze_geometry(5.0)
        print(f"✓ Analysis successful: {result}")
    except (InvalidParameterError, CalculationError) as e:
        print(f"✗ Error: {e}")
    
    # Test with invalid value
    try:
        result = analyze_geometry(-2.0)
        print(f"Result: {result}")
    except InvalidParameterError as e:
        print(f"✓ Caught expected error: {e}")
    
    print()


def example_5_real_world_usage():
    """Example 5: Real-world usage combining multiple features."""
    print("=" * 70)
    print("Example 5: Real-World Analysis Pipeline")
    print("=" * 70)
    
    from orion_octave_test import main
    
    # Define parameters
    params = {
        'side': 2.0,
        'angle': 30.0,
        'max_distance_pairs': 1000,
        'max_direction_pairs': 500
    }
    
    try:
        # Validate parameters
        side, angle, max_dist, max_dir = validate_analysis_params(params, Config)
        print(f"✓ Parameters validated")
        
        # Run analysis
        print(f"Running analysis with:")
        print(f"  - Cube side: {side}")
        print(f"  - Rotation: {angle}°")
        print(f"  - Distance pairs: {max_dist}")
        print(f"  - Direction pairs: {max_dir}")
        
        results = main(
            side=side,
            angle=angle,
            max_distance_pairs=max_dist,
            max_direction_pairs=max_dir,
            verbose=False
        )
        
        # Display results
        print(f"\n✓ Analysis complete!")
        print(f"  - Unique points: {results['point_counts']['unique_points']}")
        print(f"  - Distance variations: {results['distances']['distinct_count']}")
        print(f"  - Direction vectors: {results['directions']['unique_count']}")
        print(f"  - Golden ratio candidates: {results['golden_ratio']['candidate_count']}")
        
        # Check for special angles
        special = results['special_angles']
        print(f"\nSpecial angles detected:")
        for angle_val, data in sorted(special.items(), key=lambda x: float(x[0])):
            if data['count'] > 0:
                print(f"  - {angle_val}° ({data['description']}): {data['count']} occurrences")
        
    except ValidationError as e:
        print(f"✗ Validation error: {e}")
    except CalculationError as e:
        print(f"✗ Calculation error: {e}")
    except Exception as e:
        print(f"✗ Unexpected error: {e}")
    
    print()


def main():
    """Run all examples."""
    print("\n")
    print("╔" + "=" * 68 + "╗")
    print("║" + " " * 15 + "ORION OCTAVE CUBES - EXAMPLES" + " " * 24 + "║")
    print("║" + " " * 10 + "Demonstrating New Features and Improvements" + " " * 15 + "║")
    print("╚" + "=" * 68 + "╝")
    print("\n")
    
    example_1_basic_validation()
    example_2_comprehensive_validation()
    example_3_safe_operations()
    example_4_custom_exceptions()
    example_5_real_world_usage()
    
    print("=" * 70)
    print("All examples completed!")
    print("=" * 70)
    print("\nFor more information:")
    print("  - See docs/DEVELOPMENT.md for full development guide")
    print("  - See docs/QUICK_REFERENCE.md for quick command reference")
    print("  - Run 'pytest' to execute the full test suite")
    print()


if __name__ == '__main__':
    main()
