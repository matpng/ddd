#!/usr/bin/env python3
"""
Ultimate Test Suite - Complete Coverage
Tests EVERY angle, axis, and analysis technique to discover all possible
geometric patterns and ensure no stone is left unturned.
"""

import unittest
import numpy as np
import json
from pathlib import Path
import sys
from typing import Dict, List
import time

sys.path.insert(0, str(Path(__file__).parent))

from orion_octave_test import main as run_analysis
from advanced_discovery_engine import AdvancedDiscoveryEngine


class TestUltimateAngleSweep(unittest.TestCase):
    """Test all angles from 0° to 180° to find critical configurations"""
    
    @classmethod
    def setUpClass(cls):
        """Set up test data directory"""
        cls.results_dir = Path('test_results')
        cls.results_dir.mkdir(exist_ok=True)
        cls.engine = AdvancedDiscoveryEngine(verbose=False)
        cls.discoveries = []
    
    def test_cardinal_angles(self):
        """Test all cardinal angles: 0°, 30°, 45°, 60°, 90°, 120°, 180°"""
        print("\n🔍 Testing cardinal angles...")
        cardinal_angles = [0, 30, 36, 45, 54, 60, 72, 90, 108, 120, 144, 180]
        
        for angle in cardinal_angles:
            result = run_analysis(side=2.0, angle=angle, verbose=False,
                                max_distance_pairs=5000, max_direction_pairs=2000)
            
            # Record if phi found
            if result['golden_ratio']['candidate_count'] > 0:
                self.discoveries.append({
                    'angle': angle,
                    'phi_count': result['golden_ratio']['candidate_count'],
                    'type': 'cardinal'
                })
                print(f"   ✨ {angle}°: {result['golden_ratio']['candidate_count']} phi candidates!")
            
            # Basic validation
            self.assertGreater(result['point_counts']['unique_points'], 0)
            self.assertIn('distances', result)
    
    def test_pentagonal_angles(self):
        """Test pentagonal/icosahedral angles: 36°, 72°, 108°, 144°"""
        print("\n⭐ Testing pentagonal angles...")
        pentagonal = [36, 72, 108, 144]
        
        for angle in pentagonal:
            result = run_analysis(side=2.0, angle=angle, verbose=False,
                                max_distance_pairs=5000, max_direction_pairs=2000)
            
            # Should detect 36° angles (pentagonal symmetry)
            special_36 = result['special_angles'].get(36.0, {})
            self.assertGreater(special_36.get('count', 0), 0,
                             f"36° angle should be detected at {angle}° rotation")
    
    def test_hexagonal_angles(self):
        """Test hexagonal angles: 60°, 120°"""
        print("\n🔷 Testing hexagonal angles...")
        hexagonal = [60, 120]
        
        for angle in hexagonal:
            result = run_analysis(side=2.0, angle=angle, verbose=False,
                                max_distance_pairs=5000, max_direction_pairs=2000)
            
            # Should detect 60° angles (hexagonal symmetry)
            special_60 = result['special_angles'].get(60.0, {})
            self.assertGreater(special_60.get('count', 0), 0,
                             f"60° angle should be detected at {angle}° rotation")
    
    def test_fine_sweep_0_to_90(self):
        """Fine sweep from 0° to 90° at 5° intervals"""
        print("\n🌊 Fine sweep 0° to 90°...")
        results = {}
        
        for angle in range(0, 95, 5):
            result = run_analysis(side=2.0, angle=angle, verbose=False,
                                max_distance_pairs=5000, max_direction_pairs=2000)
            
            results[angle] = {
                'unique_points': result['point_counts']['unique_points'],
                'phi_count': result['golden_ratio']['candidate_count']
            }
            
            if result['golden_ratio']['candidate_count'] > 0:
                print(f"   ✨ {angle}°: PHI DETECTED!")
                self.discoveries.append({
                    'angle': angle,
                    'phi_count': result['golden_ratio']['candidate_count'],
                    'type': 'fine_sweep'
                })
        
        # Save sweep results
        with open(self.results_dir / 'fine_sweep_0_90.json', 'w') as f:
            json.dump(results, f, indent=2)
        
        self.assertGreater(len(results), 0)
    
    def test_multi_axis_exploration(self):
        """Test rotation about different axes"""
        print("\n🌐 Multi-axis exploration...")
        
        axes = ['x', 'y', 'z']
        angle = 60  # Known good angle
        
        for axis in axes:
            if axis == 'x':
                R_func = lambda a: self.engine._create_rotation_matrix([1, 0, 0], a)
            elif axis == 'y':
                R_func = lambda a: self.engine._create_rotation_matrix([0, 1, 0], a)
            else:
                R_func = lambda a: self.engine._create_rotation_matrix([0, 0, 1], a)
            
            # We can't directly test multi-axis with current API, but we validate the engine works
            results = self.engine.multi_axis_exploration(side=2.0, angle=angle, num_axes=5)
            
            self.assertGreater(len(results), 0)
            # Check that different axes produce different results
            scores = [r['interestingness_score'] for r in results]
            self.assertGreater(len(set(scores)), 1, "Different axes should produce different scores")


class TestAdvancedAnalyses(unittest.TestCase):
    """Test all advanced analysis techniques"""
    
    @classmethod
    def setUpClass(cls):
        """Set up test configuration"""
        cls.engine = AdvancedDiscoveryEngine(verbose=False)
        
        # Run analysis on a known good configuration
        cls.result = run_analysis(side=2.0, angle=60, verbose=False,
                                 max_distance_pairs=10000, max_direction_pairs=5000)
        cls.points = [np.array(p) for p in cls.result['points']]
    
    def test_topological_analysis(self):
        """Test topological analysis"""
        print("\n🔬 Testing topological analysis...")
        
        topo = self.engine.topological_analysis(self.points)
        
        if 'error' in topo:
            self.skipTest(f"Topological analysis unavailable: {topo['error']}")
        
        self.assertIn('centroid', topo)
        self.assertIn('point_cloud_radius', topo)
        self.assertGreater(topo['point_cloud_radius'], 0)
        
        if 'euler_characteristic' in topo:
            print(f"   Euler characteristic: {topo['euler_characteristic']}")
    
    def test_symmetry_detection(self):
        """Test symmetry group detection"""
        print("\n🔍 Testing symmetry detection...")
        
        symmetries = self.engine.detect_symmetry_groups(self.points)
        
        self.assertIn('reflection_planes', symmetries)
        self.assertIn('rotation_axes', symmetries)
        self.assertIn('classification', symmetries)
        
        print(f"   Symmetry group: {symmetries['classification']}")
        print(f"   Reflection planes: {symmetries['reflection_planes']}")
        print(f"   Rotation axes: {len(symmetries['rotation_axes'])}")
    
    def test_fractal_dimension(self):
        """Test fractal dimension calculation"""
        print("\n📐 Testing fractal dimension...")
        
        fractal = self.engine.fractal_dimension(self.points)
        
        if 'error' in fractal:
            self.skipTest(f"Fractal analysis unavailable: {fractal['error']}")
        
        self.assertIn('fractal_dimension', fractal)
        self.assertGreater(fractal['fractal_dimension'], 0)
        self.assertLess(fractal['fractal_dimension'], 4)  # Can't exceed embedding dimension + 1
        
        print(f"   Fractal dimension: {fractal['fractal_dimension']:.3f}")
    
    def test_information_entropy(self):
        """Test information entropy calculation"""
        print("\n📊 Testing information entropy...")
        
        from orion_octave_test import analyze_distances, analyze_directions
        
        distances = analyze_distances(self.points, max_pairs=10000)
        directions = analyze_directions(self.points, max_pairs=5000)
        
        entropy = self.engine.information_entropy(distances, directions)
        
        self.assertIn('distance_entropy', entropy)
        self.assertIn('direction_entropy', entropy)
        self.assertIn('total_entropy', entropy)
        
        self.assertGreater(entropy['total_entropy'], 0)
        
        print(f"   Distance entropy: {entropy['distance_entropy']:.3f}")
        print(f"   Direction entropy: {entropy['direction_entropy']:.3f}")
        print(f"   Total entropy: {entropy['total_entropy']:.3f}")
    
    def test_fourier_analysis(self):
        """Test Fourier analysis of angle spectrum"""
        print("\n🌊 Testing Fourier analysis...")
        
        # Create angle spectrum from result
        angle_spectrum = {}
        for angle_str, count in self.result['angles']['spectrum'].items():
            angle = float(angle_str)
            angle_spectrum[angle] = count
        
        fourier = self.engine.fourier_analysis(angle_spectrum)
        
        if 'error' in fourier:
            self.skipTest(f"Fourier analysis unavailable: {fourier['error']}")
        
        self.assertIn('dominant_frequencies', fourier)
        self.assertGreater(len(fourier['dominant_frequencies']), 0)
        
        print(f"   Dominant periodicities:")
        for i, freq in enumerate(fourier['dominant_frequencies'][:3], 1):
            print(f"      {i}. Period: {freq['period_degrees']:.1f}°")


class TestComprehensiveDiscovery(unittest.TestCase):
    """Test comprehensive discovery on multiple configurations"""
    
    @classmethod
    def setUpClass(cls):
        """Set up discovery engine"""
        cls.engine = AdvancedDiscoveryEngine(verbose=False)
        cls.all_discoveries = []
    
    def test_discovery_at_60_degrees(self):
        """Full discovery at 60° (known to have phi)"""
        print("\n🚀 Comprehensive discovery at 60°...")
        
        result = self.engine.comprehensive_discovery(side=2.0, angle=60, axis='z')
        
        self.assertIsNotNone(result)
        self.assertEqual(result.configuration['angle'], 60)
        self.assertGreater(len(result.discoveries), 0)
        self.assertGreater(len(result.recommendations), 0)
        self.assertGreater(len(result.potential_applications), 0)
        
        # Should find phi at 60°
        self.assertGreater(result.metrics['phi_candidates'], 0)
        
        print(f"   Discoveries: {len(result.discoveries)}")
        print(f"   Recommendations: {len(result.recommendations)}")
        print(f"   Applications: {len(result.potential_applications)}")
        
        self.all_discoveries.append(result)
    
    def test_discovery_at_36_degrees(self):
        """Full discovery at 36° (pentagonal angle)"""
        print("\n🚀 Comprehensive discovery at 36°...")
        
        result = self.engine.comprehensive_discovery(side=2.0, angle=36, axis='z')
        
        self.assertIsNotNone(result)
        self.assertGreater(len(result.discoveries), 0)
        
        # Should detect high symmetry
        self.assertGreater(result.metrics['symmetry_score'], 0)
        
        self.all_discoveries.append(result)
    
    def test_discovery_at_54_degrees(self):
        """Full discovery at 54° (related to icosahedron)"""
        print("\n🚀 Comprehensive discovery at 54°...")
        
        result = self.engine.comprehensive_discovery(side=2.0, angle=54, axis='z')
        
        self.assertIsNotNone(result)
        self.all_discoveries.append(result)
    
    def test_discovery_body_diagonal(self):
        """Full discovery with body diagonal rotation"""
        print("\n🚀 Comprehensive discovery - body diagonal...")
        
        result = self.engine.comprehensive_discovery(side=2.0, angle=60, axis='body')
        
        self.assertIsNotNone(result)
        self.assertEqual(result.configuration['axis'], 'body')
        
        self.all_discoveries.append(result)
    
    @classmethod
    def tearDownClass(cls):
        """Save all discoveries"""
        output_file = Path('test_results') / 'all_discoveries.json'
        output_file.parent.mkdir(exist_ok=True)
        
        # Convert to JSON-serializable format
        discoveries_data = []
        for discovery in cls.all_discoveries:
            from dataclasses import asdict
            discoveries_data.append(asdict(discovery))
        
        with open(output_file, 'w') as f:
            json.dump(discoveries_data, f, indent=2, default=str)
        
        print(f"\n💾 All discoveries saved to: {output_file}")


class TestExtremeConfigurations(unittest.TestCase):
    """Test extreme and edge case configurations"""
    
    def test_very_small_angle(self):
        """Test very small rotation angle (0.1°)"""
        print("\n🔬 Testing very small angle (0.1°)...")
        
        result = run_analysis(side=2.0, angle=0.1, verbose=False,
                            max_distance_pairs=5000, max_direction_pairs=2000)
        
        self.assertGreater(result['point_counts']['unique_points'], 0)
        # Even small angles produce full interference pattern (32 points is typical)
        self.assertLessEqual(result['point_counts']['unique_points'], 40)
    
    def test_near_perpendicular(self):
        """Test near-perpendicular angles (89.9°, 90.1°)"""
        print("\n🔬 Testing near-perpendicular angles...")
        
        for angle in [89.9, 90.0, 90.1]:
            result = run_analysis(side=2.0, angle=angle, verbose=False,
                                max_distance_pairs=5000, max_direction_pairs=2000)
            
            # Should detect strong 90° angles
            special_90 = result['special_angles'].get(90.0, {})
            self.assertGreater(special_90.get('count', 0), 0)
    
    def test_large_cube_size(self):
        """Test with very large cubes"""
        print("\n📏 Testing large cube size...")
        
        result = run_analysis(side=100.0, angle=60, verbose=False,
                            max_distance_pairs=5000, max_direction_pairs=2000)
        
        # Should have same point count regardless of size (scale invariance)
        result_small = run_analysis(side=2.0, angle=60, verbose=False,
                                   max_distance_pairs=5000, max_direction_pairs=2000)
        
        self.assertEqual(result['point_counts']['unique_points'],
                        result_small['point_counts']['unique_points'])
    
    def test_tiny_cube_size(self):
        """Test with very small cubes"""
        print("\n🔬 Testing tiny cube size...")
        
        result = run_analysis(side=0.01, angle=60, verbose=False,
                            max_distance_pairs=5000, max_direction_pairs=2000)
        
        self.assertGreater(result['point_counts']['unique_points'], 0)


class TestStatisticalValidation(unittest.TestCase):
    """Statistical validation of patterns across many configurations"""
    
    def test_phi_occurrence_rate(self):
        """Measure how often phi appears across angle range"""
        print("\n📊 Statistical analysis: Phi occurrence rate...")
        
        angles_with_phi = []
        total_angles = 0
        
        for angle in range(0, 181, 10):
            result = run_analysis(side=2.0, angle=angle, verbose=False,
                                max_distance_pairs=5000, max_direction_pairs=2000)
            total_angles += 1
            
            if result['golden_ratio']['candidate_count'] > 0:
                angles_with_phi.append(angle)
        
        occurrence_rate = len(angles_with_phi) / total_angles
        
        print(f"   Phi detected at: {angles_with_phi}")
        print(f"   Occurrence rate: {occurrence_rate:.1%}")
        
        self.assertGreater(len(angles_with_phi), 0, "Phi should appear at some angles")
    
    def test_point_count_distribution(self):
        """Analyze distribution of unique point counts"""
        print("\n📊 Statistical analysis: Point count distribution...")
        
        point_counts = []
        
        for angle in range(0, 181, 15):
            result = run_analysis(side=2.0, angle=angle, verbose=False,
                                max_distance_pairs=5000, max_direction_pairs=2000)
            point_counts.append(result['point_counts']['unique_points'])
        
        mean_points = np.mean(point_counts)
        std_points = np.std(point_counts)
        
        print(f"   Mean points: {mean_points:.1f}")
        print(f"   Std dev: {std_points:.1f}")
        print(f"   Range: {min(point_counts)} to {max(point_counts)}")
        
        self.assertGreater(mean_points, 0)
    
    def test_symmetry_correlation(self):
        """Test correlation between special angles and symmetry"""
        print("\n📊 Statistical analysis: Symmetry correlation...")
        
        special_angle_configs = [36, 45, 60, 72, 90, 120]
        symmetry_scores = []
        
        engine = AdvancedDiscoveryEngine(verbose=False)
        
        for angle in special_angle_configs:
            result = run_analysis(side=2.0, angle=angle, verbose=False,
                                max_distance_pairs=5000, max_direction_pairs=2000)
            
            points = [np.array(p) for p in result['points']]
            symmetries = engine.detect_symmetry_groups(points)
            
            score = len(symmetries.get('rotation_axes', [])) + len(symmetries.get('reflection_planes', []))
            symmetry_scores.append(score)
        
        print(f"   Symmetry scores: {symmetry_scores}")
        print(f"   Mean symmetry: {np.mean(symmetry_scores):.1f}")
        
        # Special angles should generally have higher symmetry
        self.assertGreater(np.mean(symmetry_scores), 2)


def run_ultimate_test_suite():
    """Run all tests and generate comprehensive report"""
    
    print("=" * 70)
    print("🚀 ULTIMATE TEST SUITE - COMPLETE COVERAGE")
    print("=" * 70)
    print()
    
    # Create test results directory
    results_dir = Path('test_results')
    results_dir.mkdir(exist_ok=True)
    
    # Run all test suites
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add all test classes
    suite.addTests(loader.loadTestsFromTestCase(TestUltimateAngleSweep))
    suite.addTests(loader.loadTestsFromTestCase(TestAdvancedAnalyses))
    suite.addTests(loader.loadTestsFromTestCase(TestComprehensiveDiscovery))
    suite.addTests(loader.loadTestsFromTestCase(TestExtremeConfigurations))
    suite.addTests(loader.loadTestsFromTestCase(TestStatisticalValidation))
    
    # Run with detailed output
    runner = unittest.TextTestRunner(verbosity=2)
    start_time = time.time()
    result = runner.run(suite)
    elapsed_time = time.time() - start_time
    
    # Generate report
    print("\n" + "=" * 70)
    print("📊 ULTIMATE TEST SUITE SUMMARY")
    print("=" * 70)
    print(f"Total tests run: {result.testsRun}")
    print(f"Successes: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Execution time: {elapsed_time:.2f} seconds")
    print()
    
    # Save report
    report = {
        'total_tests': result.testsRun,
        'successes': result.testsRun - len(result.failures) - len(result.errors),
        'failures': len(result.failures),
        'errors': len(result.errors),
        'execution_time': elapsed_time,
        'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
    }
    
    with open(results_dir / 'ultimate_test_report.json', 'w') as f:
        json.dump(report, f, indent=2)
    
    if result.wasSuccessful():
        print("✅ ALL ULTIMATE TESTS PASSED!")
        return 0
    else:
        print("❌ SOME TESTS FAILED")
        return 1


if __name__ == '__main__':
    sys.exit(run_ultimate_test_suite())
