"""
Unit tests for core analysis logic in orion_octave_test.py
"""
import pytest
import numpy as np
import math
from orion_octave_test import (
    unique_points,
    analyze_distances,
    scan_for_phi,
    analyze_angles,
    analyze_directions,
    normalize,
    PHI
)

class TestAnalysisLogic:
    """Tests for pure geometric analysis functions"""
    
    def test_normalize_vector(self):
        """Test vector normalization"""
        # Standard vector
        v = np.array([3.0, 0.0, 4.0])
        n = normalize(v)
        assert np.allclose(n, np.array([0.6, 0.0, 0.8]))
        assert math.isclose(np.linalg.norm(n), 1.0)
        
        # Zero vector
        z = np.zeros(3)
        nz = normalize(z)
        assert np.allclose(nz, z)
        
        # Already normalized
        unit = np.array([1.0, 0.0, 0.0])
        assert np.allclose(normalize(unit), unit)

    def test_unique_points(self):
        """Test point deduplication"""
        points = [
            np.array([1.0, 2.0, 3.0]),
            np.array([1.000000001, 2.0, 3.0]),  # Duplicate within tolerance
            np.array([4.0, 5.0, 6.0])
        ]
        
        # Test with high precision (default 9 digits)
        unique = unique_points(points, ndigits=6)
        assert len(unique) == 2
        
        # Check that the two distinct points are preserved
        # Note: Order might be preserved
        assert any(np.allclose(p, np.array([1.0, 2.0, 3.0])) for p in unique)
        assert any(np.allclose(p, np.array([4.0, 5.0, 6.0])) for p in unique)

    def test_analyze_distances(self):
        """Test distance calculation between points"""
        # Triangle: (0,0,0), (3,0,0), (0,4,0)
        # Distances: 3, 4, 5 (3-4-5 triangle)
        points = [
            np.array([0.0, 0.0, 0.0]),
            np.array([3.0, 0.0, 0.0]),
            np.array([0.0, 4.0, 0.0])
        ]
        
        results = analyze_distances(points)
        
        assert len(results) == 3
        assert results[3.0] == 1
        assert results[4.0] == 1
        assert results[5.0] == 1
        
        # Test max_pairs limit
        # With 3 points there are only 3 pairs, but if we restricted to 1 pair
        results_limited = analyze_distances(points, max_pairs=1)
        assert sum(results_limited.values()) == 1

    def test_scan_for_phi(self):
        """Test Golden Ratio detection"""
        # Create distances that match Phi relation
        # 1.0, 1.618, 2.0
        # 1.618 / 1.0 ~= Phi
        distances = {
            1.0: 1,
            PHI: 1,
            2.0: 1
        }
        
        candidates = scan_for_phi(distances, tol=1e-4)
        assert len(candidates) >= 1
        
        # Check that one candidate is (PHI, 1.0, PHI)
        match = next((c for c in candidates if math.isclose(c[0], PHI) and math.isclose(c[1], 1.0)), None)
        assert match is not None
        assert math.isclose(match[2], PHI)

    def test_analyze_directions(self):
        """Test direction vector analysis"""
        points = [
            np.array([0.0, 0.0, 0.0]),
            np.array([1.0, 0.0, 0.0]), # X direction
            np.array([0.0, 1.0, 0.0])  # Y direction
        ]
        
        # Pairs: (0,1)->X, (0,2)->Y, (1,2)->(-1, 1, 0) normalized
        dirs = analyze_directions(points)
        assert len(dirs) == 3
        
        # Verify X and Y axis directions are found
        # Directions are normalized and sign-canonicalized
        x_dir = np.array([1.0, 0.0, 0.0])
        y_dir = np.array([0.0, 1.0, 0.0])
        
        has_x = any(np.allclose(d, x_dir) or np.allclose(d, -x_dir) for d in dirs)
        has_y = any(np.allclose(d, y_dir) or np.allclose(d, -y_dir) for d in dirs)
        
        assert has_x
        assert has_y

    def test_analyze_angles(self):
        """Test angle calculation between directions"""
        # Standard axes X, Y, Z
        dirs = [
            np.array([1.0, 0.0, 0.0]),
            np.array([0.0, 1.0, 0.0]),
            np.array([0.0, 0.0, 1.0])
        ]
        
        # All angles should be 90 degrees
        # (X,Y)=90, (X,Z)=90, (Y,Z)=90
        results = analyze_angles(dirs)
        
        assert results[90.0] == 3
        assert len(results) == 1
