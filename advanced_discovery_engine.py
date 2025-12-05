#!/usr/bin/env python3
"""
Advanced Discovery Engine - Pushing the Boundaries
This module implements cutting-edge analysis techniques to discover
new geometric patterns, mathematical relationships, and potential
applications in physics, crystallography, and engineering.
"""

import numpy as np
import json
from pathlib import Path
from typing import Dict, List, Tuple, Any, Optional
from collections import defaultdict
import itertools
from dataclasses import dataclass, asdict
import sys

from orion_octave_test import (
    Cube, rotation_matrix_z, rotation_matrix_axis,
    edge_face_intersections, edge_edge_intersections,
    unique_points, analyze_distances, analyze_directions,
    scan_for_phi, normalize, EPS
)


@dataclass
class DiscoveryResult:
    """Container for discovery analysis results"""
    configuration: Dict[str, Any]
    discoveries: List[Dict[str, Any]]
    metrics: Dict[str, float]
    recommendations: List[str]
    potential_applications: List[str]


class AdvancedDiscoveryEngine:
    """
    Advanced analysis engine for discovering novel geometric patterns
    and their potential real-world applications.
    """
    
    def __init__(self, verbose: bool = True):
        self.verbose = verbose
        self.results_cache = {}
        
    def log(self, message: str):
        """Print message if verbose mode enabled"""
        if self.verbose:
            print(message)
    
    # ============== COMPREHENSIVE ANGLE SWEEPS ==============
    
    def fine_angle_sweep(self, side: float = 2.0, 
                        start: float = 0, end: float = 180,
                        step: float = 1.0,
                        axis: str = 'z') -> Dict[float, Dict]:
        """
        Perform fine-grained angle sweep to detect all critical angles.
        
        Args:
            side: Cube side length
            start: Start angle in degrees
            end: End angle in degrees
            step: Step size in degrees
            axis: Rotation axis ('x', 'y', 'z', or 'arbitrary')
        
        Returns:
            Dictionary mapping angle to analysis results
        """
        self.log(f"🔍 Fine angle sweep: {start}° to {end}° (step={step}°) on {axis}-axis")
        
        results = {}
        angles = np.arange(start, end + step, step)
        
        for i, angle in enumerate(angles):
            if self.verbose and i % 10 == 0:
                progress = (i / len(angles)) * 100
                self.log(f"   Progress: {progress:.1f}% ({i}/{len(angles)})")
            
            # Create rotation matrix based on axis
            if axis == 'z':
                R = rotation_matrix_z(np.radians(angle))
            elif axis == 'x':
                R = rotation_matrix_axis(np.array([1, 0, 0]), np.radians(angle))
            elif axis == 'y':
                R = rotation_matrix_axis(np.array([0, 1, 0]), np.radians(angle))
            else:
                # Arbitrary axis (1,1,1) - body diagonal
                R = rotation_matrix_axis(normalize(np.array([1, 1, 1])), np.radians(angle))
            
            # Analyze this configuration
            cube_a = Cube(center=np.zeros(3), side=side, R=np.eye(3))
            cube_b = Cube(center=np.zeros(3), side=side, R=R)
            
            # Get intersection points
            points = []
            points.extend(cube_a.vertices())
            points.extend(cube_b.vertices())
            
            ef_ab = edge_face_intersections(cube_a.edges(), cube_b.faces())
            ef_ba = edge_face_intersections(cube_b.edges(), cube_a.faces())
            points.extend(ef_ab)
            points.extend(ef_ba)
            
            ee = edge_edge_intersections(cube_a.edges(), cube_b.edges())
            points.extend(ee)
            
            # Deduplicate
            unique_pts = unique_points(points)
            
            # Quick analysis
            distances = analyze_distances(unique_pts, max_pairs=1000)
            directions = analyze_directions(unique_pts, max_pairs=500)
            phi_candidates = scan_for_phi(distances)
            
            results[angle] = {
                'unique_points': len(unique_pts),
                'distance_count': len(distances),
                'direction_count': len(directions),
                'phi_count': len(phi_candidates),
                'has_phi': len(phi_candidates) > 0
            }
        
        self.log(f"✅ Sweep complete: {len(results)} angles analyzed")
        return results
    
    # ============== MULTI-AXIS ANALYSIS ==============
    
    def multi_axis_exploration(self, side: float = 2.0,
                               angle: float = 60,
                               num_axes: int = 20) -> List[Dict]:
        """
        Test rotation about multiple arbitrary axes to find optimal symmetries.
        
        Args:
            side: Cube side length
            angle: Rotation angle in degrees
            num_axes: Number of random axes to test
        
        Returns:
            List of results sorted by interesting-ness score
        """
        self.log(f"🌐 Multi-axis exploration: {num_axes} random axes at {angle}°")
        
        results = []
        
        # Test cardinal axes first
        cardinal_axes = [
            ('x-axis', np.array([1, 0, 0])),
            ('y-axis', np.array([0, 1, 0])),
            ('z-axis', np.array([0, 0, 1])),
            ('body-diagonal', normalize(np.array([1, 1, 1]))),
            ('face-diagonal-xy', normalize(np.array([1, 1, 0]))),
            ('face-diagonal-xz', normalize(np.array([1, 0, 1]))),
            ('face-diagonal-yz', normalize(np.array([0, 1, 1])))
        ]
        
        # Add random axes
        np.random.seed(42)
        for i in range(num_axes - len(cardinal_axes)):
            axis = normalize(np.random.randn(3))
            cardinal_axes.append((f'random-{i+1}', axis))
        
        for axis_name, axis in cardinal_axes:
            R = rotation_matrix_axis(axis, np.radians(angle))
            
            cube_a = Cube(center=np.zeros(3), side=side, R=np.eye(3))
            cube_b = Cube(center=np.zeros(3), side=side, R=R)
            
            points = self._get_all_intersection_points(cube_a, cube_b)
            unique_pts = unique_points(points)
            
            distances = analyze_distances(unique_pts, max_pairs=5000)
            directions = analyze_directions(unique_pts, max_pairs=2000)
            phi_candidates = scan_for_phi(distances)
            
            # Calculate "interesting-ness" score
            score = self._calculate_interestingness(
                len(unique_pts), len(distances), len(directions), len(phi_candidates)
            )
            
            results.append({
                'axis_name': axis_name,
                'axis': axis.tolist(),
                'unique_points': len(unique_pts),
                'distance_diversity': len(distances),
                'direction_diversity': len(directions),
                'phi_candidates': len(phi_candidates),
                'interestingness_score': score
            })
        
        # Sort by interestingness
        results.sort(key=lambda x: x['interestingness_score'], reverse=True)
        
        self.log(f"✅ Top 3 most interesting axes:")
        for i, r in enumerate(results[:3], 1):
            self.log(f"   {i}. {r['axis_name']}: score={r['interestingness_score']:.2f}, "
                    f"points={r['unique_points']}, phi={r['phi_candidates']}")
        
        return results
    
    # ============== TOPOLOGICAL ANALYSIS ==============
    
    def topological_analysis(self, points: List[np.ndarray]) -> Dict[str, Any]:
        """
        Analyze topological properties of the point cloud.
        
        Args:
            points: List of 3D points
        
        Returns:
            Dictionary of topological metrics
        """
        self.log("🔬 Topological analysis")
        
        if len(points) < 4:
            return {'error': 'Not enough points for topological analysis'}
        
        points_array = np.array(points)
        
        # Calculate convex hull (if scipy available)
        try:
            from scipy.spatial import ConvexHull
            hull = ConvexHull(points_array)
            
            metrics = {
                'convex_hull_vertices': hull.vertices.tolist(),
                'num_faces': len(hull.simplices),
                'num_vertices': len(hull.vertices),
                'num_edges': len(hull.equations),
                'surface_area': hull.area,
                'volume': hull.volume,
                'euler_characteristic': len(hull.vertices) - len(hull.equations) + len(hull.simplices)
            }
            
            self.log(f"   Convex hull: {metrics['num_vertices']} vertices, "
                    f"{metrics['num_faces']} faces, χ={metrics['euler_characteristic']}")
            
        except ImportError:
            self.log("   Warning: scipy not available for convex hull analysis")
            metrics = {'error': 'scipy not installed'}
        except Exception as e:
            metrics = {'error': str(e)}
        
        # Calculate point cloud density
        centroid = points_array.mean(axis=0)
        distances_from_center = np.linalg.norm(points_array - centroid, axis=1)
        
        metrics['centroid'] = centroid.tolist()
        metrics['mean_distance_from_center'] = float(distances_from_center.mean())
        metrics['std_distance_from_center'] = float(distances_from_center.std())
        metrics['point_cloud_radius'] = float(distances_from_center.max())
        
        return metrics
    
    # ============== SYMMETRY GROUP DETECTION ==============
    
    def detect_symmetry_groups(self, points: List[np.ndarray]) -> Dict[str, Any]:
        """
        Detect symmetry groups in the point configuration.
        
        Args:
            points: List of 3D points
        
        Returns:
            Dictionary describing detected symmetry groups
        """
        self.log("🔍 Symmetry group detection")
        
        if len(points) < 4:
            return {'error': 'Not enough points'}
        
        points_array = np.array(points)
        symmetries = {
            'reflection_planes': [],
            'rotation_axes': [],
            'inversion_center': None
        }
        
        centroid = points_array.mean(axis=0)
        
        # Test for inversion symmetry (point at center)
        inverted = 2 * centroid - points_array
        if self._points_match(points_array, inverted):
            symmetries['inversion_center'] = centroid.tolist()
            self.log("   ✓ Inversion symmetry detected")
        
        # Test for reflection planes (xy, xz, yz)
        planes = [
            ('xy', np.array([0, 0, 1])),
            ('xz', np.array([0, 1, 0])),
            ('yz', np.array([1, 0, 0]))
        ]
        
        for plane_name, normal in planes:
            reflected = self._reflect_points(points_array, centroid, normal)
            if self._points_match(points_array, reflected):
                symmetries['reflection_planes'].append(plane_name)
                self.log(f"   ✓ {plane_name} reflection plane detected")
        
        # Test for rotation axes (2-fold, 3-fold, 4-fold, 5-fold)
        axes = [
            ('x', np.array([1, 0, 0])),
            ('y', np.array([0, 1, 0])),
            ('z', np.array([0, 0, 1])),
            ('body-diagonal', normalize(np.array([1, 1, 1])))
        ]
        
        for axis_name, axis in axes:
            for n in [2, 3, 4, 5, 6]:
                angle = 2 * np.pi / n
                R = rotation_matrix_axis(axis, angle)
                rotated = (points_array - centroid) @ R.T + centroid
                
                if self._points_match(points_array, rotated):
                    symmetries['rotation_axes'].append({
                        'axis': axis_name,
                        'order': n,
                        'angle_deg': 360 / n
                    })
                    self.log(f"   ✓ {n}-fold rotation about {axis_name} detected")
                    break
        
        # Classify symmetry group
        symmetries['classification'] = self._classify_symmetry_group(symmetries)
        
        return symmetries
    
    # ============== FRACTAL DIMENSION ANALYSIS ==============
    
    def fractal_dimension(self, points: List[np.ndarray]) -> Dict[str, float]:
        """
        Calculate fractal dimension using box-counting method.
        
        Args:
            points: List of 3D points
        
        Returns:
            Dictionary with fractal dimension estimates
        """
        self.log("📐 Fractal dimension analysis")
        
        if len(points) < 10:
            return {'error': 'Not enough points'}
        
        points_array = np.array(points)
        
        # Normalize to unit cube
        mins = points_array.min(axis=0)
        maxs = points_array.max(axis=0)
        normalized = (points_array - mins) / (maxs - mins + EPS)
        
        # Box counting at different scales
        scales = [2, 4, 8, 16, 32]
        counts = []
        
        for scale in scales:
            # Create grid
            boxes = set()
            for point in normalized:
                box = tuple((point * scale).astype(int))
                boxes.add(box)
            counts.append(len(boxes))
        
        # Fit log-log relationship
        log_scales = np.log(scales)
        log_counts = np.log(counts)
        
        # Linear regression
        A = np.vstack([log_scales, np.ones(len(log_scales))]).T
        slope, intercept = np.linalg.lstsq(A, log_counts, rcond=None)[0]
        
        self.log(f"   Fractal dimension estimate: {slope:.3f}")
        
        return {
            'fractal_dimension': float(slope),
            'scales': scales,
            'box_counts': counts,
            'fit_quality': float(np.corrcoef(log_scales, log_counts)[0, 1])
        }
    
    # ============== INFORMATION ENTROPY ==============
    
    def information_entropy(self, distances: Dict[float, int],
                           directions: List[np.ndarray]) -> Dict[str, float]:
        """
        Calculate information entropy of distance and direction distributions.
        
        Args:
            distances: Dictionary mapping distance to count
            directions: List of direction vectors
        
        Returns:
            Dictionary with entropy metrics
        """
        self.log("📊 Information entropy analysis")
        
        # Distance entropy
        total_distances = sum(distances.values())
        if total_distances > 0:
            distance_probs = np.array([count / total_distances for count in distances.values()])
            distance_entropy = -np.sum(distance_probs * np.log2(distance_probs + EPS))
        else:
            distance_entropy = 0.0
        
        # Direction entropy (discretize spherical space)
        if len(directions) > 0:
            # Convert to spherical coordinates
            directions_array = np.array(directions)
            theta = np.arctan2(directions_array[:, 1], directions_array[:, 0])
            phi = np.arccos(directions_array[:, 2])
            
            # Discretize into bins
            theta_bins = np.linspace(-np.pi, np.pi, 36)  # 10° resolution
            phi_bins = np.linspace(0, np.pi, 18)
            
            hist, _, _ = np.histogram2d(theta, phi, bins=[theta_bins, phi_bins])
            hist = hist.flatten()
            hist = hist[hist > 0]
            
            total_directions = hist.sum()
            direction_probs = hist / total_directions
            direction_entropy = -np.sum(direction_probs * np.log2(direction_probs + EPS))
        else:
            direction_entropy = 0.0
        
        # Maximum possible entropy
        max_distance_entropy = np.log2(len(distances)) if len(distances) > 0 else 0
        max_direction_entropy = np.log2(len(theta_bins) * len(phi_bins))
        
        self.log(f"   Distance entropy: {distance_entropy:.3f} / {max_distance_entropy:.3f}")
        self.log(f"   Direction entropy: {direction_entropy:.3f} / {max_direction_entropy:.3f}")
        
        return {
            'distance_entropy': float(distance_entropy),
            'distance_entropy_normalized': float(distance_entropy / max_distance_entropy) if max_distance_entropy > 0 else 0,
            'direction_entropy': float(direction_entropy),
            'direction_entropy_normalized': float(direction_entropy / max_direction_entropy) if max_direction_entropy > 0 else 0,
            'total_entropy': float(distance_entropy + direction_entropy)
        }
    
    # ============== FOURIER ANALYSIS ==============
    
    def fourier_analysis(self, angle_spectrum: Dict[float, int]) -> Dict[str, Any]:
        """
        Perform Fourier analysis on angle spectrum to detect periodicities.
        
        Args:
            angle_spectrum: Dictionary mapping angle to count
        
        Returns:
            Dictionary with Fourier analysis results
        """
        self.log("🌊 Fourier analysis of angle spectrum")
        
        if len(angle_spectrum) < 10:
            return {'error': 'Not enough data'}
        
        # Create uniform sampling
        angles = sorted(angle_spectrum.keys())
        counts = [angle_spectrum[a] for a in angles]
        
        # Interpolate to uniform grid
        angle_grid = np.linspace(0, 180, 1800)  # 0.1° resolution
        count_grid = np.interp(angle_grid, angles, counts)
        
        # Compute FFT
        fft = np.fft.fft(count_grid)
        freqs = np.fft.fftfreq(len(count_grid), d=0.1)
        
        # Get power spectrum
        power = np.abs(fft) ** 2
        
        # Find dominant frequencies
        positive_freqs = freqs[:len(freqs)//2]
        positive_power = power[:len(power)//2]
        
        # Get top 5 frequencies
        top_indices = np.argsort(positive_power)[-6:-1][::-1]  # Skip DC component
        
        dominant_frequencies = []
        for idx in top_indices:
            freq = positive_freqs[idx]
            period = 1.0 / freq if freq > EPS else np.inf
            power_val = positive_power[idx]
            
            dominant_frequencies.append({
                'frequency': float(freq),
                'period_degrees': float(period),
                'power': float(power_val)
            })
        
        self.log(f"   Top periodicities detected:")
        for i, df in enumerate(dominant_frequencies[:3], 1):
            self.log(f"      {i}. Period: {df['period_degrees']:.1f}° (power: {df['power']:.1e})")
        
        return {
            'dominant_frequencies': dominant_frequencies,
            'total_power': float(power.sum()),
            'spectral_centroid': float(np.sum(positive_freqs * positive_power) / np.sum(positive_power))
        }
    
    # ============== COMPREHENSIVE DISCOVERY RUN ==============
    
    def comprehensive_discovery(self, side: float = 2.0,
                                angle: float = 60,
                                axis: str = 'z') -> DiscoveryResult:
        """
        Run all advanced analysis techniques on a configuration.
        
        Args:
            side: Cube side length
            angle: Rotation angle in degrees
            axis: Rotation axis
        
        Returns:
            DiscoveryResult object with all findings
        """
        self.log("=" * 70)
        self.log(f"🚀 COMPREHENSIVE DISCOVERY: {angle}° rotation, {axis}-axis")
        self.log("=" * 70)
        
        # Create configuration
        if axis == 'z':
            R = rotation_matrix_z(np.radians(angle))
        elif axis == 'x':
            R = rotation_matrix_axis(np.array([1, 0, 0]), np.radians(angle))
        elif axis == 'y':
            R = rotation_matrix_axis(np.array([0, 1, 0]), np.radians(angle))
        else:
            R = rotation_matrix_axis(normalize(np.array([1, 1, 1])), np.radians(angle))
        
        cube_a = Cube(center=np.zeros(3), side=side, R=np.eye(3))
        cube_b = Cube(center=np.zeros(3), side=side, R=R)
        
        # Get all points
        points = self._get_all_intersection_points(cube_a, cube_b)
        unique_pts = unique_points(points)
        
        # Standard analysis
        distances = analyze_distances(unique_pts, max_pairs=10000)
        directions = analyze_directions(unique_pts, max_pairs=5000)
        phi_candidates = scan_for_phi(distances)
        
        # Advanced analyses
        discoveries = []
        
        # 1. Topological analysis
        topo = self.topological_analysis(unique_pts)
        if 'error' not in topo:
            discoveries.append({
                'type': 'topology',
                'description': 'Topological properties of point cloud',
                'data': topo
            })
        
        # 2. Symmetry detection
        symmetries = self.detect_symmetry_groups(unique_pts)
        if 'error' not in symmetries:
            discoveries.append({
                'type': 'symmetry',
                'description': f"Symmetry group: {symmetries.get('classification', 'Unknown')}",
                'data': symmetries
            })
        
        # 3. Fractal dimension
        fractal = self.fractal_dimension(unique_pts)
        if 'error' not in fractal:
            discoveries.append({
                'type': 'fractal',
                'description': f"Fractal dimension: {fractal['fractal_dimension']:.3f}",
                'data': fractal
            })
        
        # 4. Information entropy
        entropy = self.information_entropy(distances, directions)
        discoveries.append({
            'type': 'entropy',
            'description': f"Information content (entropy): {entropy['total_entropy']:.2f} bits",
            'data': entropy
        })
        
        # Calculate overall metrics
        metrics = {
            'unique_points': len(unique_pts),
            'distance_diversity': len(distances),
            'direction_diversity': len(directions),
            'phi_candidates': len(phi_candidates),
            'symmetry_score': len(symmetries.get('rotation_axes', [])) + len(symmetries.get('reflection_planes', [])),
            'entropy_score': entropy['total_entropy'],
            'fractal_dimension': fractal.get('fractal_dimension', 0.0)
        }
        
        # Generate recommendations
        recommendations = self._generate_recommendations(metrics, discoveries)
        
        # Generate potential applications
        applications = self._generate_applications(metrics, discoveries, phi_candidates)
        
        self.log("=" * 70)
        self.log("✅ DISCOVERY COMPLETE")
        self.log("=" * 70)
        
        return DiscoveryResult(
            configuration={
                'side': side,
                'angle': angle,
                'axis': axis
            },
            discoveries=discoveries,
            metrics=metrics,
            recommendations=recommendations,
            potential_applications=applications
        )
    
    # ============== HELPER METHODS ==============
    
    def _get_all_intersection_points(self, cube_a: Cube, cube_b: Cube) -> List[np.ndarray]:
        """Get all intersection points between two cubes"""
        points = []
        points.extend(cube_a.vertices())
        points.extend(cube_b.vertices())
        points.extend(edge_face_intersections(cube_a.edges(), cube_b.faces()))
        points.extend(edge_face_intersections(cube_b.edges(), cube_a.faces()))
        points.extend(edge_edge_intersections(cube_a.edges(), cube_b.edges()))
        return points
    
    def _calculate_interestingness(self, n_points: int, n_distances: int,
                                   n_directions: int, n_phi: int) -> float:
        """Calculate an interestingness score for a configuration"""
        # Higher scores for: many unique points, high diversity, phi candidates
        score = (
            n_points * 0.3 +
            n_distances * 0.2 +
            n_directions * 0.2 +
            n_phi * 10.0  # Phi is highly interesting!
        )
        return score
    
    def _points_match(self, points1: np.ndarray, points2: np.ndarray, tol: float = 1e-6) -> bool:
        """Check if two sets of points match (order-independent)"""
        if len(points1) != len(points2):
            return False
        
        # For each point in points1, find closest in points2
        for p1 in points1:
            distances = np.linalg.norm(points2 - p1, axis=1)
            if distances.min() > tol:
                return False
        
        return True
    
    def _reflect_points(self, points: np.ndarray, center: np.ndarray,
                       normal: np.ndarray) -> np.ndarray:
        """Reflect points across a plane defined by center and normal"""
        normal = normalize(normal)
        centered = points - center
        reflected = centered - 2 * np.outer(centered @ normal, normal)
        return reflected + center
    
    def _classify_symmetry_group(self, symmetries: Dict) -> str:
        """Classify the symmetry group based on detected symmetries"""
        n_reflections = len(symmetries.get('reflection_planes', []))
        n_rotations = len(symmetries.get('rotation_axes', []))
        has_inversion = symmetries.get('inversion_center') is not None
        
        # Simple classification
        if n_reflections >= 3 and n_rotations >= 4:
            return "Cubic (Oh)"
        elif n_rotations >= 3:
            return "High symmetry (multiple rotation axes)"
        elif n_reflections >= 2:
            return "Dihedral (multiple reflection planes)"
        elif n_rotations == 1 or n_reflections == 1:
            return "Low symmetry"
        else:
            return "Asymmetric (C1)"
    
    def _generate_recommendations(self, metrics: Dict, discoveries: List) -> List[str]:
        """Generate recommendations based on analysis results"""
        recs = []
        
        if metrics['phi_candidates'] > 0:
            recs.append("🌟 Golden ratio detected! Explore neighboring angles for phi optimization")
        
        if metrics['symmetry_score'] >= 5:
            recs.append("🔷 High symmetry detected - investigate for crystal structure applications")
        
        if metrics['fractal_dimension'] > 2.5:
            recs.append("📐 High fractal dimension suggests complex space-filling properties")
        
        if metrics['entropy_score'] > 10:
            recs.append("📊 High information content - rich geometric structure detected")
        
        if metrics['distance_diversity'] > 50:
            recs.append("📏 Exceptional distance diversity - potential for multi-scale applications")
        
        return recs
    
    def _generate_applications(self, metrics: Dict, discoveries: List,
                              phi_candidates: List) -> List[str]:
        """Generate potential real-world applications"""
        apps = []
        
        if len(phi_candidates) > 0:
            apps.extend([
                "🏗️ Architecture: Bio-inspired structural designs using golden ratio proportions",
                "🔬 Materials Science: Self-similar lattice structures for metamaterials",
                "📡 Antenna Design: Logarithmic spiral arrays with phi-based spacing",
                "🎨 Art & Design: Sacred geometry patterns for aesthetic optimization"
            ])
        
        if metrics.get('symmetry_score', 0) >= 5:
            apps.extend([
                "💎 Crystallography: Novel crystal lattice prediction and design",
                "⚛️ Molecular Chemistry: Symmetry-based molecule configuration",
                "🌐 Photonic Crystals: Bandgap engineering through symmetry control"
            ])
        
        if metrics.get('fractal_dimension', 0) > 2.5:
            apps.extend([
                "🌳 Biological Systems: Modeling vascular networks and lung structures",
                "📶 Signal Processing: Fractal antenna design for multi-band operation",
                "🧮 Data Compression: Fractal-based encoding schemes"
            ])
        
        if metrics.get('distance_diversity', 0) > 50:
            apps.extend([
                "🎯 Sensor Networks: Optimal node placement in 3D space",
                "🔊 Acoustics: Multi-frequency resonator cavity design",
                "⚡ Quantum Computing: Qubit arrangement for reduced decoherence"
            ])
        
        return list(set(apps))  # Remove duplicates


# ============== MAIN EXECUTION ==============

def main():
    """Main execution for advanced discovery"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Advanced Geometric Discovery Engine')
    parser.add_argument('--mode', choices=['sweep', 'multi-axis', 'comprehensive', 'all'],
                       default='comprehensive', help='Analysis mode')
    parser.add_argument('--angle', type=float, default=60, help='Rotation angle in degrees')
    parser.add_argument('--side', type=float, default=2.0, help='Cube side length')
    parser.add_argument('--axis', choices=['x', 'y', 'z', 'body'], default='z',
                       help='Rotation axis')
    parser.add_argument('--output', type=str, help='Output JSON file')
    parser.add_argument('--quiet', action='store_true', help='Suppress verbose output')
    
    args = parser.parse_args()
    
    engine = AdvancedDiscoveryEngine(verbose=not args.quiet)
    
    if args.mode == 'sweep':
        results = engine.fine_angle_sweep(side=args.side, axis=args.axis)
        output_data = {'mode': 'sweep', 'results': results}
    
    elif args.mode == 'multi-axis':
        results = engine.multi_axis_exploration(side=args.side, angle=args.angle)
        output_data = {'mode': 'multi-axis', 'results': results}
    
    elif args.mode == 'comprehensive':
        result = engine.comprehensive_discovery(
            side=args.side, angle=args.angle, axis=args.axis
        )
        output_data = asdict(result)
    
    elif args.mode == 'all':
        # Run everything!
        print("\n🚀 RUNNING ALL DISCOVERY MODES\n")
        
        # 1. Comprehensive on current config
        comp = engine.comprehensive_discovery(side=args.side, angle=args.angle, axis=args.axis)
        
        # 2. Multi-axis exploration
        multi = engine.multi_axis_exploration(side=args.side, angle=args.angle, num_axes=10)
        
        # 3. Fine sweep around current angle
        sweep = engine.fine_angle_sweep(
            side=args.side,
            start=max(0, args.angle - 10),
            end=min(180, args.angle + 10),
            step=1.0,
            axis=args.axis
        )
        
        output_data = {
            'mode': 'all',
            'comprehensive': asdict(comp),
            'multi_axis': multi,
            'sweep': sweep
        }
    
    # Save output
    if args.output:
        output_path = Path(args.output)
        with open(output_path, 'w') as f:
            json.dump(output_data, f, indent=2, default=str)
        print(f"\n💾 Results saved to: {output_path}")
    else:
        print("\n" + "=" * 70)
        print("RESULTS:")
        print("=" * 70)
        print(json.dumps(output_data, indent=2, default=str))


if __name__ == '__main__':
    main()
