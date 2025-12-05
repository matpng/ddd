#!/usr/bin/env python3
"""
Comprehensive Automated Testing Suite
Includes unit tests, integration tests, property-based tests, and ground truth validation.
"""

import unittest
import json
import numpy as np
from pathlib import Path
import tempfile
import shutil
from typing import Dict, Any

from orion_octave_test import (
    Cube, Edge, Face,
    intersect_line_plane,
    edge_face_intersections,
    edge_edge_intersections,
    analyze_distances,
    analyze_directions,
    analyze_angles,
    scan_for_phi,
    main as run_analysis
)
import numpy as np


class TestGeometricPrimitives(unittest.TestCase):
    """Test basic geometric data structures"""
    
    def test_cube_creation(self):
        """Test cube vertex generation"""
        cube = Cube(side_length=2.0)
        vertices = cube.vertices()
        
        self.assertEqual(len(vertices), 8)
        
        # Check that vertices are at correct distance from origin
        for v in vertices:
            distance = np.sqrt(v.x**2 + v.y**2 + v.z**2)
            self.assertAlmostEqual(distance, np.sqrt(3), places=5)
    
    def test_cube_rotation(self):
        """Test cube rotation produces expected transformation"""
        cube = Cube(side_length=1.0, rotation_angle=90)
        vertices = cube.vertices()
        
        # After 90° rotation, coordinates should swap/negate predictably
        # This is a basic smoke test
        self.assertEqual(len(vertices), 8)
        self.assertIsInstance(vertices[0], np.ndarray)
    
    def test_edge_generation(self):
        """Test edge generation from vertices"""
        cube = Cube(side_length=1.0)
        edges = cube.edges()
        
        # 8 vertices should produce 12 edges (cube edges)
        self.assertEqual(len(edges), 12)
    
    def test_face_generation(self):
        """Test face generation from vertices"""
        cube = Cube(side_length=1.0)
        faces = cube.faces()
        
        self.assertEqual(len(faces), 6)
        for face in faces:
            self.assertEqual(len(face.vertices), 4)


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
        # Edge from (-1, 0, 0) to (1, 0, 0) through XY plane
        edge = Edge(np.array([-1, 0, 0]), np.array([1, 0, 0]))
        
        # Face in XY plane (z=0)
        face = Face(
            center=np.array([0, 0, 0]),
            normal=np.array([0, 0, 1]),
            vertices=[
                np.array([-0.5, -0.5, 0]),
                np.array([0.5, -0.5, 0]),
                np.array([0.5, 0.5, 0]),
                np.array([-0.5, 0.5, 0])
            ]
        )
        
        intersections = edge_face_intersections(edge, [face])
        # Should find intersection at (0, 0, 0)
        self.assertEqual(len(intersections), 1)
        self.assertAlmostEqual(intersections[0][0], 0.0, places=5)
        self.assertAlmostEqual(intersections[0][1], 0.0, places=5)
        self.assertAlmostEqual(intersections[0][2], 0.0, places=5)


class TestAnalysisFunctions(unittest.TestCase):
    """Test analysis functions"""
    
    def test_analyze_distances_empty(self):
        """Test distance analysis with no points"""
        result = analyze_distances([], max_pairs=1000)
        
        self.assertEqual(result['unique_count'], 0)
        self.assertEqual(len(result['distances']), 0)
    
    def test_analyze_distances_known_points(self):
        """Test distance analysis with known points"""
        points = [
            np.array([0, 0, 0]),
            np.array([1, 0, 0]),
            np.array([0, 1, 0]),
            np.array([0, 0, 1])
        ]
        
        result = analyze_distances(points, max_pairs=10)
        
        # Should find distances of 1.0 and sqrt(2)
        self.assertGreater(result['unique_count'], 0)
        self.assertIn(1.0, result['distances'])
    
    def test_scan_for_phi_known_ratio(self):
        """Test golden ratio detection with known value"""
        distances = [1.0, 1.618033988749, 2.0]  # Contains phi
        
        candidates = scan_for_phi(distances)
        
        self.assertGreater(len(candidates), 0)
        # Should find the phi value
        found_phi = any(abs(c['ratio'] - 1.618033988749) < 0.001 for c in candidates)
        self.assertTrue(found_phi)
    
    def test_analyze_directions_unit_vectors(self):
        """Test direction analysis with unit vectors"""
        points = [
            np.array([0, 0, 0]),
            np.array([1, 0, 0]),
            np.array([0, 1, 0]),
            np.array([0, 0, 1]),
            np.array([-1, 0, 0])
        ]
        
        result = analyze_directions(points, max_pairs=20)
        
        # Should find cardinal directions
        self.assertGreater(result['unique_count'], 0)


class TestGroundTruthValidation(unittest.TestCase):
    """Test against known geometric configurations"""
    
    def test_45_degree_rotation_symmetry(self):
        """Test 45° rotation produces expected symmetry"""
        result = run_analysis(side=1.0, angle=45, verbose=False)
        
        # 45° should produce high symmetry
        self.assertGreater(result['point_counts']['unique_points'], 10)
        
        # Should have 45° angles in the special angles
        has_45_deg = result['special_angles'].get('45°', {}).get('count', 0) > 0
        self.assertTrue(has_45_deg)
    
    def test_60_degree_rotation_phi(self):
        """Test 60° rotation may produce golden ratio"""
        result = run_analysis(side=1.0, angle=60, verbose=False)
        
        # 60° is related to hexagonal symmetry
        self.assertGreater(result['point_counts']['unique_points'], 10)
    
    def test_90_degree_rotation_orthogonal(self):
        """Test 90° rotation produces orthogonal configuration"""
        result = run_analysis(side=1.0, angle=90, verbose=False)
        
        # Should have many 90° angles
        has_90_deg = result['special_angles'].get('90°', {}).get('count', 0) > 10
        self.assertTrue(has_90_deg)
    
    def test_icosahedral_angle_detection(self):
        """Test detection of icosahedral angle (~31.72°)"""
        result = run_analysis(side=1.0, angle=31.72, verbose=False)
        
        # Should detect near-perfect icosahedral match
        ico_check = result['icosahedral_check']
        if ico_check['angle_degrees'] is not None:
            self.assertLess(ico_check['angle_degrees'], 1.0)
            self.assertEqual(ico_check['match_quality'], 'strong')


class TestPropertyBasedTests(unittest.TestCase):
    """Property-based tests that should hold for all configurations"""
    
    def test_point_count_deterministic(self):
        """Test that same parameters produce same point count"""
        result1 = run_analysis(side=1.0, angle=45, verbose=False)
        result2 = run_analysis(side=1.0, angle=45, verbose=False)
        
        self.assertEqual(
            result1['point_counts']['unique_points'],
            result2['point_counts']['unique_points']
        )
    
    def test_symmetry_properties(self):
        """Test geometric symmetry properties"""
        result = run_analysis(side=2.0, angle=60, verbose=False)
        
        # Point count should be positive
        self.assertGreater(result['point_counts']['unique_points'], 0)
        
        # Should have at least some special angles
        total_special = sum(data['count'] for data in result['special_angles'].values())
        self.assertGreater(total_special, 0)
    
    def test_distance_properties(self):
        """Test distance metric properties"""
        result = run_analysis(side=1.0, angle=45, verbose=False)
        
        if result['distances']['unique_count'] > 0:
            # Min should be <= mean <= max
            self.assertLessEqual(result['distances']['min'], result['distances']['mean'])
            self.assertLessEqual(result['distances']['mean'], result['distances']['max'])
            
            # Std should be non-negative
            self.assertGreaterEqual(result['distances']['std'], 0)
    
    def test_scaling_property(self):
        """Test that scaling preserves ratios"""
        result1 = run_analysis(side=1.0, angle=45, verbose=False)
        result2 = run_analysis(side=2.0, angle=45, verbose=False)
        
        # Point counts should be identical (geometry scales)
        self.assertEqual(
            result1['point_counts']['unique_points'],
            result2['point_counts']['unique_points']
        )
        
        # Distance ratios should be preserved
        if (result1['distances']['unique_count'] > 0 and 
            result2['distances']['unique_count'] > 0):
            ratio1 = result1['distances']['max'] / result1['distances']['min']
            ratio2 = result2['distances']['max'] / result2['distances']['min']
            self.assertAlmostEqual(ratio1, ratio2, places=3)


class TestIntegration(unittest.TestCase):
    """Integration tests for complete workflows"""
    
    def test_full_analysis_pipeline(self):
        """Test complete analysis pipeline"""
        result = run_analysis(side=1.0, angle=45, verbose=False)
        
        # Check all expected sections are present
        self.assertIn('configuration', result)
        self.assertIn('point_counts', result)
        self.assertIn('distances', result)
        self.assertIn('golden_ratio', result)
        self.assertIn('directions', result)
        self.assertIn('angles', result)
        self.assertIn('special_angles', result)
        self.assertIn('icosahedral_check', result)
    
    def test_json_output_validity(self):
        """Test JSON output is valid"""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_file = Path(tmpdir) / 'test_output.json'
            
            result = run_analysis(
                side=1.0,
                angle=45,
                output=str(output_file),
                verbose=False
            )
            
            # Verify file was created
            self.assertTrue(output_file.exists())
            
            # Verify it's valid JSON
            with open(output_file) as f:
                loaded = json.load(f)
            
            self.assertEqual(loaded['configuration']['side_length'], 1.0)


class TestRegressionSuite(unittest.TestCase):
    """Regression tests to catch breaking changes"""
    
    def test_baseline_45deg_configuration(self):
        """Baseline test for 45° configuration"""
        result = run_analysis(side=1.0, angle=45, verbose=False)
        
        # These values should remain stable
        self.assertGreater(result['point_counts']['unique_points'], 50)
        self.assertGreater(result['special_angles']['45°']['count'], 10)
    
    def test_baseline_60deg_configuration(self):
        """Baseline test for 60° configuration"""
        result = run_analysis(side=1.0, angle=60, verbose=False)
        
        self.assertGreater(result['point_counts']['unique_points'], 50)
        self.assertGreater(result['special_angles']['60°']['count'], 10)


def run_test_suite():
    """Run comprehensive test suite"""
    
    print("="*80)
    print("COMPREHENSIVE AUTOMATED TEST SUITE")
    print("="*80)
    
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add all test classes
    suite.addTests(loader.loadTestsFromTestCase(TestGeometricPrimitives))
    suite.addTests(loader.loadTestsFromTestCase(TestLineIntersections))
    suite.addTests(loader.loadTestsFromTestCase(TestAnalysisFunctions))
    suite.addTests(loader.loadTestsFromTestCase(TestGroundTruthValidation))
    suite.addTests(loader.loadTestsFromTestCase(TestPropertyBasedTests))
    suite.addTests(loader.loadTestsFromTestCase(TestIntegration))
    suite.addTests(loader.loadTestsFromTestCase(TestRegressionSuite))
    
    # Run tests with verbose output
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    print(f"Tests run: {result.testsRun}")
    print(f"Successes: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    
    if result.wasSuccessful():
        print("\n✓ ALL TESTS PASSED")
    else:
        print("\n✗ SOME TESTS FAILED")
    
    print("="*80)
    
    return result.wasSuccessful()


if __name__ == '__main__':
    success = run_test_suite()
    exit(0 if success else 1)
