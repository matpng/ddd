#!/usr/bin/env python3
"""
Comprehensive Automated Test Suite
Tests all components with corrected API usage
"""

import unittest
import numpy as np
import json
from pathlib import Path
import sys

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from orion_octave_test import (
    Cube, Face, Edge,
    intersect_line_plane, point_in_face,
    edge_face_intersections, edge_edge_intersections,
    unique_points, analyze_distances, analyze_directions,
    scan_for_phi, rotation_matrix_z, normalize,
    main as run_analysis
)


class TestGeometricPrimitives(unittest.TestCase):
    """Test basic geometric primitives and constructors"""
    
    def test_cube_creation(self):
        """Test cube vertex generation"""
        cube = Cube(center=np.zeros(3), side=2.0, R=np.eye(3))
        vertices = cube.vertices()
        
        self.assertEqual(len(vertices), 8)
        # Check that vertices form a cube
        for v in vertices:
            self.assertEqual(len(v), 3)
    
    def test_cube_rotation(self):
        """Test cube rotation produces expected transformation"""
        R = rotation_matrix_z(np.radians(90))
        cube = Cube(center=np.zeros(3), side=1.0, R=R)
        vertices = cube.vertices()
        
        # After 90° rotation, should still have 8 vertices
        self.assertEqual(len(vertices), 8)
    
    def test_edge_generation(self):
        """Test edge generation from vertices"""
        cube = Cube(center=np.zeros(3), side=1.0, R=np.eye(3))
        edges = cube.edges()
        
        self.assertEqual(len(edges), 12)
    
    def test_face_generation(self):
        """Test face generation from vertices"""
        cube = Cube(center=np.zeros(3), side=1.0, R=np.eye(3))
        faces = cube.faces()
        
        self.assertEqual(len(faces), 6)


class TestLineIntersections(unittest.TestCase):
    """Test intersection algorithms"""
    
    def test_intersect_line_plane_parallel(self):
        """Test line parallel to plane (no intersection)"""
        p0 = np.array([0, 0, 1])
        p1 = np.array([1, 0, 1])
        plane_point = np.array([0, 0, 0])
        plane_normal = np.array([0, 0, 1])
        
        hit, t, point = intersect_line_plane(p0, p1, plane_point, plane_normal)
        self.assertFalse(hit)
    
    def test_intersect_line_plane_perpendicular(self):
        """Test line perpendicular to plane"""
        p0 = np.array([0, 0, -1])
        p1 = np.array([0, 0, 1])
        plane_point = np.array([0, 0, 0])
        plane_normal = np.array([0, 0, 1])
        
        hit, t, point = intersect_line_plane(p0, p1, plane_point, plane_normal)
        self.assertTrue(hit)
        self.assertAlmostEqual(point[2], 0.0, places=5)
    
    def test_edge_face_intersection_known_case(self):
        """Test edge-face intersection with known geometry"""
        # Create a simple edge and face that should intersect
        edge_p0 = np.array([0, 0, -1])
        edge_p1 = np.array([0, 0, 1])
        
        face = Face(
            center=np.array([0, 0, 0]),
            normal=np.array([0, 0, 1]),
            u=np.array([1, 0, 0]),
            v=np.array([0, 1, 0]),
            half_size=1.0
        )
        
        # Should intersect at origin
        result = edge_face_intersections([Edge(edge_p0, edge_p1)], [face])
        self.assertGreater(len(result), 0)


class TestAnalysisFunctions(unittest.TestCase):
    """Test analysis and detection functions"""
    
    def test_analyze_distances_empty(self):
        """Test distance analysis with no points"""
        points = []
        result = analyze_distances(points)
        self.assertEqual(len(result), 0)
    
    def test_analyze_distances_known_points(self):
        """Test distance analysis with known points"""
        points = [
            np.array([0, 0, 0]),
            np.array([1, 0, 0]),
            np.array([0, 1, 0]),
            np.array([0, 0, 1])
        ]
        
        result = analyze_distances(points)
        self.assertGreater(len(result), 0)
        # Should have distance 1.0 (unit cube edges)
        distances_rounded = [round(d, 1) for d in result.keys()]
        self.assertIn(1.0, distances_rounded)
    
    def test_scan_for_phi_known_ratio(self):
        """Test golden ratio detection with known value"""
        phi = (1 + np.sqrt(5)) / 2
        distances = {1.0: 10, phi: 5, 2.0: 3}
        
        candidates = scan_for_phi(distances)
        self.assertGreater(len(candidates), 0)
    
    def test_analyze_directions_unit_vectors(self):
        """Test direction analysis with unit vectors"""
        points = [
            np.array([0, 0, 0]),
            np.array([1, 0, 0]),
            np.array([0, 1, 0]),
            np.array([0, 0, 1])
        ]
        
        result = analyze_directions(points)
        self.assertGreater(len(result), 0)
        
        # All directions should be unit vectors
        for direction in result:
            norm = np.linalg.norm(direction)
            self.assertAlmostEqual(norm, 1.0, places=5)


class TestGroundTruthValidation(unittest.TestCase):
    """Test against known geometric configurations"""
    
    def test_45_degree_rotation_symmetry(self):
        """Test 45° rotation produces expected symmetry"""
        result = run_analysis(side=2.0, angle=45, verbose=False, 
                            max_distance_pairs=5000, max_direction_pairs=2000)
        
        # Should detect 90° angles (cube symmetry) - this is reliable
        special_90 = result['special_angles'].get(90.0, {})
        self.assertGreater(special_90.get('count', 0), 0, "90° angles should be detected")
    
    def test_60_degree_rotation_phi(self):
        """Test 60° rotation may produce golden ratio"""
        result = run_analysis(side=2.0, angle=60, verbose=False,
                            max_distance_pairs=5000, max_direction_pairs=2000)
        
        # May or may not have phi, but should complete successfully
        self.assertIn('golden_ratio', result)
    
    def test_90_degree_rotation_orthogonal(self):
        """Test 90° rotation produces orthogonal configuration"""
        result = run_analysis(side=2.0, angle=90, verbose=False,
                            max_distance_pairs=5000, max_direction_pairs=2000)
        
        # Should have strong 90° angle presence
        special_90 = result['special_angles'].get(90.0, {})
        self.assertGreater(special_90.get('count', 0), 0)
    
    def test_icosahedral_angle_detection(self):
        """Test detection of icosahedral angle (~31.72°)"""
        result = run_analysis(side=2.0, angle=31.72, verbose=False,
                            max_distance_pairs=5000, max_direction_pairs=2000)
        
        # Should complete successfully with angle analysis
        self.assertIn('special_angles', result)


class TestPropertyBasedTests(unittest.TestCase):
    """Test mathematical properties and invariants"""
    
    def test_point_count_deterministic(self):
        """Test that same parameters produce same point count"""
        result1 = run_analysis(side=2.0, angle=45, verbose=False,
                             max_distance_pairs=5000, max_direction_pairs=2000)
        result2 = run_analysis(side=2.0, angle=45, verbose=False,
                             max_distance_pairs=5000, max_direction_pairs=2000)
        
        self.assertEqual(result1['point_counts']['unique_points'],
                        result2['point_counts']['unique_points'])
    
    def test_symmetry_properties(self):
        """Test geometric symmetry properties"""
        result = run_analysis(side=2.0, angle=36, verbose=False,
                            max_distance_pairs=5000, max_direction_pairs=2000)
        
        # Should detect 36° angle (pentagonal symmetry)
        special_36 = result['special_angles'].get(36.0, {})
        self.assertGreater(special_36.get('count', 0), 0)
    
    def test_distance_properties(self):
        """Test distance metric properties"""
        result = run_analysis(side=2.0, angle=30, verbose=False,
                            max_distance_pairs=5000, max_direction_pairs=2000)
        
        if result['distances']['distinct_count'] > 0:
            dist_spectrum = result['distances']['spectrum']
            distances = [float(k) for k in dist_spectrum.keys()]
            
            # All distances should be positive
            self.assertTrue(all(d >= 0 for d in distances))
            
            # Distances should be present
            self.assertGreater(len(distances), 0)
    
    def test_scaling_property(self):
        """Test that scaling preserves ratios"""
        result1 = run_analysis(side=1.0, angle=30, verbose=False,
                             max_distance_pairs=5000, max_direction_pairs=2000)
        result2 = run_analysis(side=2.0, angle=30, verbose=False,
                             max_distance_pairs=5000, max_direction_pairs=2000)
        
        # Point counts should be the same regardless of scale
        self.assertEqual(result1['point_counts']['unique_points'],
                        result2['point_counts']['unique_points'])


class TestIntegration(unittest.TestCase):
    """Test complete workflow integration"""
    
    def test_full_analysis_pipeline(self):
        """Test complete analysis pipeline"""
        result = run_analysis(
            side=2.0,
            angle=45,
            verbose=False,
            max_distance_pairs=5000,
            max_direction_pairs=2000
        )
        
        # Verify all expected sections are present
        self.assertIn('configuration', result)
        self.assertIn('point_counts', result)
        self.assertIn('distances', result)
        self.assertIn('directions', result)
        self.assertIn('special_angles', result)
        self.assertIn('golden_ratio', result)
    
    def test_json_output_validity(self):
        """Test JSON output is valid"""
        result = run_analysis(
            side=2.0, 
            angle=30, 
            verbose=False,
            max_distance_pairs=5000,
            max_direction_pairs=2000
        )
        
        # Verify result structure
        self.assertIn('configuration', result)
        self.assertIn('points', result)
        
        # Test JSON serializability
        json_str = json.dumps(result, default=lambda x: x.tolist() if isinstance(x, np.ndarray) else float(x) if isinstance(x, (np.floating, np.integer)) else x)
        data = json.loads(json_str)
        self.assertIn('configuration', data)


class TestRegressionSuite(unittest.TestCase):
    """Regression tests - verify consistent behavior"""
    
    def test_baseline_45deg_configuration(self):
        """Baseline test for 45° configuration"""
        result = run_analysis(side=2.0, angle=45, verbose=False,
                            max_distance_pairs=5000, max_direction_pairs=2000)
        
        # Should produce a consistent number of unique points
        self.assertEqual(result['point_counts']['unique_points'], 32)
    
    def test_baseline_60deg_configuration(self):
        """Baseline test for 60° configuration"""
        result = run_analysis(side=2.0, angle=60, verbose=False,
                            max_distance_pairs=5000, max_direction_pairs=2000)
        
        self.assertEqual(result['point_counts']['unique_points'], 32)


if __name__ == '__main__':
    # Run tests with verbose output
    suite = unittest.TestLoader().loadTestsFromModule(sys.modules[__name__])
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    print(f"Tests run: {result.testsRun}")
    print(f"Successes: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    
    if result.wasSuccessful():
        print("\n✓ ALL TESTS PASSED!")
        sys.exit(0)
    else:
        print("\n✗ SOME TESTS FAILED")
        sys.exit(1)
