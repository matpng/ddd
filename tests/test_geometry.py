#!/usr/bin/env python3
"""
Unit tests for the geometry computation engine (orion_octave_test.py)
"""

import pytest
import numpy as np
import math
from typing import List

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from orion_octave_test import (
    almost_equal,
    normalize,
    round_tuple,
    rotation_matrix_z,
    rotation_matrix_axis,
    Face,
    Edge,
    Cube,
    intersect_line_plane,
    point_in_face,
    edge_face_intersections,
    edge_edge_intersections,
    unique_points,
    analyze_distances,
    scan_for_phi,
    analyze_directions,
    analyze_angles,
    EPS,
    PHI
)


class TestBasicHelpers:
    """Test basic numeric helper functions."""
    
    def test_almost_equal(self):
        assert almost_equal(1.0, 1.0 + 1e-10)
        assert almost_equal(0.0, 1e-12)
        assert not almost_equal(1.0, 1.1)
        assert not almost_equal(0.5, 0.5001, tol=1e-5)
    
    def test_normalize(self):
        v = np.array([3.0, 4.0, 0.0])
        n = normalize(v)
        assert almost_equal(np.linalg.norm(n), 1.0)
        assert almost_equal(n[0], 0.6)
        assert almost_equal(n[1], 0.8)
        
        # Zero vector
        zero = np.array([0.0, 0.0, 0.0])
        n_zero = normalize(zero)
        assert np.allclose(n_zero, zero)
    
    def test_round_tuple(self):
        t = (1.23456789, 2.98765432, 3.14159265)
        rounded = round_tuple(t, ndigits=3)
        assert rounded == (1.235, 2.988, 3.142)
    
    def test_rotation_matrix_z(self):
        # 90-degree rotation
        R = rotation_matrix_z(math.pi / 2)
        v = np.array([1.0, 0.0, 0.0])
        v_rot = R @ v
        assert almost_equal(v_rot[0], 0.0, tol=1e-10)
        assert almost_equal(v_rot[1], 1.0, tol=1e-10)
        assert almost_equal(v_rot[2], 0.0, tol=1e-10)
    
    def test_rotation_matrix_axis(self):
        # Rotation around z-axis should match rotation_matrix_z
        axis = np.array([0.0, 0.0, 1.0])
        theta = math.pi / 6  # 30 degrees
        R1 = rotation_matrix_axis(axis, theta)
        R2 = rotation_matrix_z(theta)
        assert np.allclose(R1, R2, atol=1e-10)


class TestGeometryPrimitives:
    """Test Face, Edge, and Cube classes."""
    
    def test_edge_creation(self):
        p0 = np.array([0.0, 0.0, 0.0])
        p1 = np.array([1.0, 0.0, 0.0])
        edge = Edge(p0, p1)
        
        assert almost_equal(edge.length(), 1.0)
        assert np.allclose(edge.direction(), np.array([1.0, 0.0, 0.0]))
        assert np.allclose(edge.midpoint(), np.array([0.5, 0.0, 0.0]))
    
    def test_face_vertices(self):
        center = np.array([0.0, 0.0, 0.0])
        normal = np.array([0.0, 0.0, 1.0])
        u = np.array([1.0, 0.0, 0.0])
        v = np.array([0.0, 1.0, 0.0])
        face = Face(center, normal, u, v, half_size=1.0)
        
        verts = face.vertices()
        assert len(verts) == 4
        # All vertices should be in the z=0 plane
        for vert in verts:
            assert almost_equal(vert[2], 0.0)
    
    def test_cube_vertices_count(self):
        center = np.zeros(3)
        cube = Cube(center, side=2.0, R=np.eye(3))
        verts = cube.vertices()
        assert len(verts) == 8
    
    def test_cube_edges_count(self):
        center = np.zeros(3)
        cube = Cube(center, side=2.0, R=np.eye(3))
        edges = cube.edges()
        assert len(edges) == 12
    
    def test_cube_faces_count(self):
        center = np.zeros(3)
        cube = Cube(center, side=2.0, R=np.eye(3))
        faces = cube.faces()
        assert len(faces) == 6
    
    def test_cube_rotation(self):
        center = np.zeros(3)
        # 45-degree rotation around z-axis
        R = rotation_matrix_z(math.pi / 4)
        cube = Cube(center, side=2.0, R=R)
        verts = cube.vertices()
        
        # Check that vertices are rotated
        # The vertex at (1,1,1) should be rotated
        for v in verts:
            # All vertices should be distance sqrt(3) from origin
            dist = np.linalg.norm(v)
            assert almost_equal(dist, math.sqrt(3), tol=1e-10)


class TestIntersections:
    """Test intersection computation functions."""
    
    def test_intersect_line_plane_hit(self):
        p0 = np.array([0.0, 0.0, -1.0])
        p1 = np.array([0.0, 0.0, 1.0])
        plane_point = np.array([0.0, 0.0, 0.0])
        plane_normal = np.array([0.0, 0.0, 1.0])
        
        hit, t, point = intersect_line_plane(p0, p1, plane_point, plane_normal)
        
        assert hit
        assert almost_equal(t, 0.5)
        assert np.allclose(point, [0.0, 0.0, 0.0])
    
    def test_intersect_line_plane_parallel(self):
        # Line parallel to plane
        p0 = np.array([0.0, 0.0, 1.0])
        p1 = np.array([1.0, 0.0, 1.0])
        plane_point = np.array([0.0, 0.0, 0.0])
        plane_normal = np.array([0.0, 0.0, 1.0])
        
        hit, t, point = intersect_line_plane(p0, p1, plane_point, plane_normal)
        
        assert not hit
    
    def test_point_in_face(self):
        center = np.array([0.0, 0.0, 0.0])
        normal = np.array([0.0, 0.0, 1.0])
        u = np.array([1.0, 0.0, 0.0])
        v = np.array([0.0, 1.0, 0.0])
        face = Face(center, normal, u, v, half_size=1.0)
        
        # Point inside face
        p_inside = np.array([0.5, 0.5, 0.0])
        assert point_in_face(face, p_inside)
        
        # Point outside face
        p_outside = np.array([2.0, 0.0, 0.0])
        assert not point_in_face(face, p_outside)
        
        # Point not in plane
        p_offplane = np.array([0.5, 0.5, 1.0])
        assert not point_in_face(face, p_offplane)
    
    def test_edge_edge_intersections_simple(self):
        # Two perpendicular edges that intersect
        e1 = Edge(np.array([-1.0, 0.0, 0.0]), np.array([1.0, 0.0, 0.0]))
        e2 = Edge(np.array([0.0, -1.0, 0.0]), np.array([0.0, 1.0, 0.0]))
        
        intersections = edge_edge_intersections([e1], [e2])
        
        assert len(intersections) == 1
        assert np.allclose(intersections[0], [0.0, 0.0, 0.0], atol=1e-6)


class TestAnalysisFunctions:
    """Test analysis helper functions."""
    
    def test_unique_points(self):
        points = [
            np.array([1.0, 2.0, 3.0]),
            np.array([1.0, 2.0, 3.0 + 1e-10]),  # Duplicate within tolerance
            np.array([4.0, 5.0, 6.0]),
            np.array([1.0, 2.0, 3.0]),  # Exact duplicate
        ]
        
        unique = unique_points(points)
        assert len(unique) == 2
    
    def test_analyze_distances(self):
        points = [
            np.array([0.0, 0.0, 0.0]),
            np.array([1.0, 0.0, 0.0]),
            np.array([0.0, 1.0, 0.0]),
        ]
        
        dist_counts = analyze_distances(points)
        
        # Should have distances 1.0 and sqrt(2)
        assert len(dist_counts) >= 2
        assert 1.0 in [round(d, 6) for d in dist_counts.keys()]
    
    def test_scan_for_phi(self):
        # Create distances with golden ratio relationship
        distances = {
            1.0: 1,
            PHI: 1,  # Golden ratio
            2.0: 1
        }
        
        candidates = scan_for_phi(distances, tol=0.01)
        
        # Should find the φ relationship
        assert len(candidates) >= 1
    
    def test_analyze_directions(self):
        points = [
            np.array([0.0, 0.0, 0.0]),
            np.array([1.0, 0.0, 0.0]),
            np.array([0.0, 1.0, 0.0]),
            np.array([0.0, 0.0, 1.0]),
        ]
        
        dirs = analyze_directions(points)
        
        # Should have 3 main directions (x, y, z axes)
        assert len(dirs) >= 3
        
        # All should be normalized
        for d in dirs:
            norm = np.linalg.norm(d)
            assert almost_equal(norm, 1.0, tol=1e-6)
    
    def test_analyze_angles(self):
        # Orthogonal directions
        dirs = [
            np.array([1.0, 0.0, 0.0]),
            np.array([0.0, 1.0, 0.0]),
            np.array([0.0, 0.0, 1.0]),
        ]
        
        angle_counts = analyze_angles(dirs)
        
        # Should have 90-degree angles
        assert 90.0 in [round(a, 2) for a in angle_counts.keys()]


class TestEndToEndAnalysis:
    """Test complete analysis pipeline."""
    
    @pytest.mark.integration
    def test_full_analysis_30_degrees(self):
        from orion_octave_test import main
        
        results = main(
            side=2.0,
            angle=30.0,
            max_distance_pairs=1000,
            max_direction_pairs=500,
            verbose=False
        )
        
        # Validate structure
        assert 'configuration' in results
        assert 'point_counts' in results
        assert 'distances' in results
        assert 'golden_ratio' in results
        assert 'directions' in results
        assert 'angles' in results
        assert 'special_angles' in results
        assert 'icosahedral_check' in results
        
        # Validate point counts
        counts = results['point_counts']
        assert counts['vertices_A'] == 8
        assert counts['vertices_B'] == 8
        assert counts['unique_points'] > 0
        
        # Validate configuration
        config = results['configuration']
        assert config['side_length'] == 2.0
        assert config['rotation_angle_degrees'] == 30.0
    
    @pytest.mark.integration
    def test_full_analysis_45_degrees(self):
        from orion_octave_test import main
        
        results = main(
            side=2.0,
            angle=45.0,
            max_distance_pairs=1000,
            max_direction_pairs=500,
            verbose=False
        )
        
        assert results['configuration']['rotation_angle_degrees'] == 45.0
        assert results['point_counts']['unique_points'] > 0
    
    @pytest.mark.slow
    def test_large_analysis(self):
        """Test with higher sampling for comprehensive analysis."""
        from orion_octave_test import main
        
        results = main(
            side=3.0,
            angle=60.0,
            max_distance_pairs=10000,
            max_direction_pairs=5000,
            verbose=False
        )
        
        # Should complete without errors
        assert results['point_counts']['unique_points'] > 0
        assert len(results['distances']['spectrum']) > 0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
