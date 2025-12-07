#!/usr/bin/env python3
"""
Comprehensive Unit Tests for Orion Octave Cubes
Tests core geometry, discovery system, and API endpoints
"""

import unittest
import numpy as np
import json
import tempfile
import shutil
from pathlib import Path
from datetime import datetime

# Import modules to test
from orion_octave_test import (
    Cube, Edge, Face,
    rotation_matrix_z, rotation_matrix_axis,
    edge_face_intersections, edge_edge_intersections,
    unique_points, analyze_distances, analyze_directions,
    scan_for_phi, normalize, almost_equal,
    EPS, PHI
)
from discovery_manager import DiscoveryManager
from config import DevelopmentConfig, ProductionConfig, TestingConfig


class TestGeometryPrimitives(unittest.TestCase):
    """Test basic geometry functions."""
    
    def test_rotation_matrix_z(self):
        """Test Z-axis rotation matrix."""
        # 90-degree rotation
        R = rotation_matrix_z(np.pi / 2)
        v = np.array([1, 0, 0])
        rotated = R @ v
        expected = np.array([0, 1, 0])
        self.assertTrue(np.allclose(rotated, expected, atol=1e-9))
    
    def test_rotation_matrix_axis(self):
        """Test arbitrary axis rotation."""
        # 180-degree rotation around x-axis
        R = rotation_matrix_axis(np.array([1, 0, 0]), np.pi)
        v = np.array([0, 1, 0])
        rotated = R @ v
        expected = np.array([0, -1, 0])
        self.assertTrue(np.allclose(rotated, expected, atol=1e-9))
    
    def test_normalize(self):
        """Test vector normalization."""
        v = np.array([3, 4, 0])
        normalized = normalize(v)
        self.assertAlmostEqual(np.linalg.norm(normalized), 1.0)
        
        # Zero vector should return zero
        zero = np.array([0, 0, 0])
        result = normalize(zero)
        self.assertTrue(np.allclose(result, zero))
    
    def test_almost_equal(self):
        """Test floating point comparison."""
        self.assertTrue(almost_equal(1.0, 1.0 + 1e-10))
        self.assertFalse(almost_equal(1.0, 1.1))


class TestCube(unittest.TestCase):
    """Test Cube class."""
    
    def setUp(self):
        """Create test cubes."""
        self.cube = Cube(center=np.zeros(3), side=2.0, R=np.eye(3))
    
    def test_cube_vertices(self):
        """Test cube vertex generation."""
        vertices = self.cube.vertices()
        self.assertEqual(len(vertices), 8)
        
        # Check all vertices are at correct distance from center
        for v in vertices:
            dist = np.linalg.norm(v)
            self.assertAlmostEqual(dist, np.sqrt(3))  # Half diagonal
    
    def test_cube_edges(self):
        """Test cube edge generation."""
        edges = self.cube.edges()
        self.assertEqual(len(edges), 12)
        
        # Each edge should have length 2.0
        for edge in edges:
            length = np.linalg.norm(edge.p1 - edge.p0)
            self.assertAlmostEqual(length, 2.0)
    
    def test_cube_faces(self):
        """Test cube face generation."""
        faces = self.cube.faces()
        self.assertEqual(len(faces), 6)
        
        # Each face normal should be unit length
        for face in faces:
            norm_length = np.linalg.norm(face.normal)
            self.assertAlmostEqual(norm_length, 1.0)


class TestIntersections(unittest.TestCase):
    """Test intersection algorithms."""
    
    def setUp(self):
        """Create test cubes."""
        self.cube_a = Cube(center=np.zeros(3), side=2.0, R=np.eye(3))
        self.cube_b = Cube(center=np.zeros(3), side=2.0, 
                          R=rotation_matrix_z(np.radians(30)))
    
    def test_edge_face_intersections(self):
        """Test edge-face intersection detection."""
        edges = self.cube_a.edges()
        faces = self.cube_b.faces()
        
        intersections = edge_face_intersections(edges, faces)
        self.assertIsInstance(intersections, list)
        self.assertGreater(len(intersections), 0)
        
        # All intersections should be 3D points
        for point in intersections:
            self.assertEqual(len(point), 3)
    
    def test_edge_edge_intersections(self):
        """Test edge-edge intersection detection."""
        edges_a = self.cube_a.edges()
        edges_b = self.cube_b.edges()
        
        intersections = edge_edge_intersections(edges_a, edges_b)
        self.assertIsInstance(intersections, list)
        
        # Intersections should be within reasonable bounds
        for point in intersections:
            self.assertLess(np.linalg.norm(point), 10.0)
    
    def test_unique_points(self):
        """Test point deduplication."""
        points = [
            np.array([1.0, 2.0, 3.0]),
            np.array([1.0, 2.0, 3.0]),  # Duplicate
            np.array([1.0 + 1e-10, 2.0, 3.0]),  # Near duplicate
            np.array([4.0, 5.0, 6.0])
        ]
        
        unique = unique_points(points)
        self.assertEqual(len(unique), 2)


class TestAnalysis(unittest.TestCase):
    """Test analysis functions."""
    
    def test_analyze_distances(self):
        """Test distance spectrum analysis."""
        points = [
            np.array([0, 0, 0]),
            np.array([1, 0, 0]),
            np.array([0, 1, 0]),
            np.array([1, 1, 0])
        ]
        
        distances = analyze_distances(points, max_pairs=10)
        self.assertIsInstance(distances, dict)
        self.assertGreater(len(distances), 0)
        
        # Check for expected distances
        self.assertIn(1.0, distances.values() or distances.keys())
    
    def test_analyze_directions(self):
        """Test direction spectrum analysis."""
        points = [
            np.array([0, 0, 0]),
            np.array([1, 0, 0]),
            np.array([0, 1, 0]),
            np.array([0, 0, 1])
        ]
        
        directions = analyze_directions(points, max_pairs=10)
        self.assertIsInstance(directions, dict)
    
    def test_scan_for_phi(self):
        """Test golden ratio detection."""
        # Create distances with phi relationship
        distances = {
            1.0: 10,
            PHI: 5,
            PHI * PHI: 3
        }
        
        candidates = scan_for_phi(distances)
        self.assertIsInstance(candidates, list)


class TestDiscoveryManager(unittest.TestCase):
    """Test discovery management system."""
    
    def setUp(self):
        """Create temporary directory for test discoveries."""
        self.temp_dir = tempfile.mkdtemp()
        self.manager = DiscoveryManager(self.temp_dir)
    
    def tearDown(self):
        """Clean up temporary directory."""
        shutil.rmtree(self.temp_dir)
    
    def test_save_discovery(self):
        """Test saving a discovery."""
        discovery_data = {
            'angle': 30.0,
            'summary': {
                'unique_points': 24,
                'golden_ratio_candidates': 2
            },
            'full_results': {'test': 'data'}
        }
        
        discovery_id = self.manager.save_discovery(discovery_data, 'test')
        self.assertIsNotNone(discovery_id)
        self.assertIn('test', discovery_id)
    
    def test_get_latest(self):
        """Test retrieving latest discoveries."""
        # Save a few discoveries
        for i in range(3):
            self.manager.save_discovery(
                {'angle': i * 30, 'summary': {}, 'full_results': {}},
                'test'
            )
        
        latest = self.manager.get_latest(count=2)
        self.assertEqual(len(latest), 2)
    
    def test_get_by_id(self):
        """Test retrieving discovery by ID."""
        discovery_data = {'angle': 45, 'summary': {}, 'full_results': {}}
        discovery_id = self.manager.save_discovery(discovery_data, 'test')
        
        retrieved = self.manager.get_by_id(discovery_id)
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved['id'], discovery_id)
    
    def test_get_stats(self):
        """Test getting discovery statistics."""
        # Save discoveries
        for i in range(5):
            self.manager.save_discovery(
                {'angle': i, 'summary': {}, 'full_results': {}},
                f'type{i % 2}'
            )
        
        stats = self.manager.get_stats()
        self.assertEqual(stats['total_discoveries'], 5)
        self.assertIn('discoveries_by_type', stats)
        self.assertIn('discoveries_by_date', stats)
    
    def test_search(self):
        """Test discovery search."""
        # Save discoveries
        self.manager.save_discovery(
            {'angle': 30, 'summary': {}, 'full_results': {}},
            'angle_sweep'
        )
        self.manager.save_discovery(
            {'angle': 60, 'summary': {}, 'full_results': {}},
            'golden_ratio'
        )
        
        results = self.manager.search(discovery_type='angle_sweep')
        self.assertGreater(len(results), 0)
        self.assertEqual(results[0]['type'], 'angle_sweep')


class TestConfiguration(unittest.TestCase):
    """Test configuration management."""
    
    def test_development_config(self):
        """Test development configuration."""
        config = DevelopmentConfig()
        self.assertTrue(config.DEBUG)
        self.assertFalse(config.TESTING)
        self.assertEqual(config.LOG_LEVEL, 'DEBUG')
    
    def test_production_config(self):
        """Test production configuration."""
        import os
        # Set required environment variable
        os.environ['SECRET_KEY'] = 'test-secret-key-for-testing'
        
        config = ProductionConfig()
        self.assertFalse(config.DEBUG)
        self.assertFalse(config.TESTING)
        
        # Validate should not raise error
        try:
            config.validate()
        except ValueError:
            self.fail("Production config validation failed")
        
        # Clean up
        del os.environ['SECRET_KEY']
    
    def test_testing_config(self):
        """Test testing configuration."""
        config = TestingConfig()
        self.assertTrue(config.DEBUG)
        self.assertTrue(config.TESTING)
        self.assertFalse(config.CACHE_ENABLED)
    
    def test_config_validation(self):
        """Test configuration validation."""
        # Should validate successfully
        DevelopmentConfig.validate()
        
        # Test invalid configuration
        with self.assertRaises(ValueError):
            class InvalidConfig(DevelopmentConfig):
                MIN_SIDE_LENGTH = 100
                MAX_SIDE_LENGTH = 10
            InvalidConfig.validate()


class TestGoldenRatio(unittest.TestCase):
    """Test golden ratio detection."""
    
    def test_phi_constant(self):
        """Test PHI constant value."""
        self.assertAlmostEqual(PHI, 1.618033988749895, places=10)
        self.assertAlmostEqual(PHI * PHI, PHI + 1, places=10)
    
    def test_phi_detection_in_distances(self):
        """Test detection of golden ratio in distance pairs."""
        # Create distances with exact phi relationship
        distances = {
            1.0: 10,
            PHI: 8,
            PHI * PHI: 6,
            2.0: 5
        }
        
        candidates = scan_for_phi(distances)
        self.assertGreater(len(candidates), 0)
        
        # Verify ratio
        for a, b, ratio in candidates:
            self.assertAlmostEqual(ratio, PHI, delta=0.01)


def run_tests():
    """Run all tests and generate report."""
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add all test classes
    suite.addTests(loader.loadTestsFromTestCase(TestGeometryPrimitives))
    suite.addTests(loader.loadTestsFromTestCase(TestCube))
    suite.addTests(loader.loadTestsFromTestCase(TestIntersections))
    suite.addTests(loader.loadTestsFromTestCase(TestAnalysis))
    suite.addTests(loader.loadTestsFromTestCase(TestDiscoveryManager))
    suite.addTests(loader.loadTestsFromTestCase(TestConfiguration))
    suite.addTests(loader.loadTestsFromTestCase(TestGoldenRatio))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    print(f"Tests run: {result.testsRun}")
    print(f"Successes: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print("=" * 70)
    
    return result.wasSuccessful()


if __name__ == '__main__':
    import sys
    success = run_tests()
    sys.exit(0 if success else 1)
