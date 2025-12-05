#!/usr/bin/env python3
"""
Orion Octave Cubes – Geometry Test Harness

This script:
1. Builds two cubes: one axis-aligned, one rotated by 30° about the z-axis.
2. Computes:
   - All cube vertices
   - All edge–face intersections (edges of cube A with faces of cube B, and vice versa)
   - Edge-edge intersections
3. Deduplicates all points (the "interference lattice" P).
4. Analyzes:
   - Distance spectrum (for golden-ratio candidates)
   - Direction spectrum (for icosahedral-style directions)
   - Angle distributions
5. Provides hooks for further tests (Platonic/Archimedean/Catalan detection).

Requirements:
- Python 3.8+
- numpy
- (optional) scipy.spatial for ConvexHull if you later add polyhedron detection

Run:
    python orion_octave_test.py
"""

import math
import sys
import json
import argparse
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import List, Tuple, Iterable, Set, Dict, Optional, Any
import itertools
from collections import defaultdict

import numpy as np


# ---------- Constants ----------

EPS = 1e-9
PHI = (1 + math.sqrt(5)) / 2.0  # Golden ratio


# ---------- Basic numeric helpers ----------

def almost_equal(a: float, b: float, tol: float = EPS) -> bool:
    """Check if two floats are approximately equal within tolerance."""
    return abs(a - b) <= tol


def normalize(v: np.ndarray) -> np.ndarray:
    """Normalize a vector to unit length, returning zero vector if magnitude is too small."""
    n = np.linalg.norm(v)
    if n < EPS:
        return np.zeros_like(v)
    return v / n


def round_tuple(x: Iterable[float], ndigits: int = 9) -> Tuple[float, ...]:
    """Round all elements in an iterable to a fixed precision for hashing."""
    return tuple(round(float(t), ndigits) for t in x)


def rotation_matrix_z(theta: float) -> np.ndarray:
    """Create a rotation matrix for rotation about the z-axis."""
    c, s = math.cos(theta), math.sin(theta)
    return np.array([[c, -s, 0.0],
                     [s,  c, 0.0],
                     [0.0, 0.0, 1.0]])


def rotation_matrix_axis(axis: np.ndarray, theta: float) -> np.ndarray:
    """
    Create a rotation matrix for rotation about an arbitrary axis using Rodrigues' formula.
    
    Args:
        axis: Unit vector representing the rotation axis
        theta: Rotation angle in radians
    """
    axis = normalize(axis)
    c = math.cos(theta)
    s = math.sin(theta)
    t = 1 - c
    x, y, z = axis
    
    return np.array([
        [t*x*x + c,    t*x*y - s*z,  t*x*z + s*y],
        [t*x*y + s*z,  t*y*y + c,    t*y*z - s*x],
        [t*x*z - s*y,  t*y*z + s*x,  t*z*z + c]
    ])


# ---------- Geometry primitives ----------

@dataclass
class Face:
    """Represents a square face in 3D space."""
    center: np.ndarray      # (3,) - center point
    normal: np.ndarray      # (3,) - unit normal vector
    u: np.ndarray           # (3,) - orthonormal basis vector along one edge
    v: np.ndarray           # (3,) - orthonormal basis vector along the other edge
    half_size: float        # half edge length
    
    def vertices(self) -> List[np.ndarray]:
        """Return the 4 corner vertices of the face."""
        h = self.half_size
        corners = [
            self.center + h * self.u + h * self.v,
            self.center + h * self.u - h * self.v,
            self.center - h * self.u - h * self.v,
            self.center - h * self.u + h * self.v,
        ]
        return corners


@dataclass
class Edge:
    """Represents a line segment in 3D space."""
    p0: np.ndarray  # (3,) - start point
    p1: np.ndarray  # (3,) - end point
    
    def length(self) -> float:
        """Return the length of the edge."""
        return np.linalg.norm(self.p1 - self.p0)
    
    def direction(self) -> np.ndarray:
        """Return the normalized direction vector."""
        return normalize(self.p1 - self.p0)
    
    def midpoint(self) -> np.ndarray:
        """Return the midpoint of the edge."""
        return (self.p0 + self.p1) / 2.0


@dataclass
class Cube:
    """Represents an oriented cube in 3D space."""
    center: np.ndarray     # (3,) - center point
    side: float            # edge length
    R: np.ndarray          # (3,3) rotation matrix

    def vertices(self) -> List[np.ndarray]:
        """Return the 8 vertices as 3D numpy arrays."""
        s = self.side / 2.0
        # Generate all 8 combinations of ±s
        local_vertices = np.array([
            [+s, +s, +s], [+s, +s, -s], [+s, -s, +s], [+s, -s, -s],
            [-s, +s, +s], [-s, +s, -s], [-s, -s, +s], [-s, -s, -s]
        ])
        # Rotate and translate
        return [(self.R @ v) + self.center for v in local_vertices]

    def edges(self) -> List[Edge]:
        """Return the 12 edges as Edge objects."""
        verts = self.vertices()
        # Define the 12 edges of a cube by vertex index pairs
        edge_indices = [
            # Top face (z = +s)
            (0, 1), (0, 2), (0, 4),
            # Bottom face (z = -s)
            (7, 5), (7, 6), (7, 3),
            # Vertical edges
            (1, 3), (1, 5), (2, 3), (2, 6), (4, 5), (4, 6),
        ]
        return [Edge(verts[i], verts[j]) for i, j in edge_indices]

    def faces(self) -> List[Face]:
        """
        Return the 6 faces of the cube using rotated local normals and local u,v basis.
        
        Local cube in its own frame has faces with normals: ±x, ±y, ±z
        For each normal, choose u,v as orthonormal basis spanning the face.
        """
        s = self.side / 2.0
        faces: List[Face] = []

        # Define local face normals and corresponding u,v basis vectors
        face_specs = [
            # (normal, u, v)
            (np.array([+1, 0, 0]), np.array([0, 1, 0]), np.array([0, 0, 1])),  # +x face
            (np.array([-1, 0, 0]), np.array([0, 1, 0]), np.array([0, 0, 1])),  # -x face
            (np.array([0, +1, 0]), np.array([1, 0, 0]), np.array([0, 0, 1])),  # +y face
            (np.array([0, -1, 0]), np.array([1, 0, 0]), np.array([0, 0, 1])),  # -y face
            (np.array([0, 0, +1]), np.array([1, 0, 0]), np.array([0, 1, 0])),  # +z face
            (np.array([0, 0, -1]), np.array([1, 0, 0]), np.array([0, 1, 0])),  # -z face
        ]

        for n_local, u_local, v_local in face_specs:
            # Rotate to world frame
            n_world = normalize(self.R @ n_local)
            u_world = normalize(self.R @ u_local)
            v_world = normalize(self.R @ v_local)

            # Center: move from cube center by normal * half side
            center_world = self.center + n_world * s

            faces.append(Face(
                center=center_world,
                normal=n_world,
                u=u_world,
                v=v_world,
                half_size=s
            ))

        return faces


# ---------- Intersection routines ----------

def intersect_line_plane(p0: np.ndarray, p1: np.ndarray, 
                        plane_point: np.ndarray,
                        plane_normal: np.ndarray) -> Tuple[bool, float, np.ndarray]:
    """
    Intersect parametric line p(t) = p0 + t*(p1-p0) with plane.
    
    Plane defined by: (x - plane_point) · plane_normal = 0
    
    Returns: (hit, t, point)
        hit: True if intersection exists
        t: parameter value (0 ≤ t ≤ 1 for segment)
        point: intersection point
    """
    d = p1 - p0
    denom = np.dot(plane_normal, d)
    
    # Parallel or nearly parallel
    if abs(denom) < EPS:
        return False, 0.0, np.zeros(3)
    
    t = np.dot(plane_normal, (plane_point - p0)) / denom
    p = p0 + t * d
    return True, t, p


def point_in_face(face: Face, p: np.ndarray, tol: float = 1e-6) -> bool:
    """
    Check if point p lies inside the square face.
    
    We assume u and v form an orthonormal basis spanning the face.
    Express r = p - center in (u, v) coordinates.
    Point is inside if |r·u| ≤ half_size and |r·v| ≤ half_size
    and point lies in the face plane.
    """
    r = p - face.center
    
    # Check planarity
    d_plane = np.dot(r, face.normal)
    if abs(d_plane) > tol:
        return False
    
    # Check bounds in local coordinates
    a = np.dot(r, face.u)
    b = np.dot(r, face.v)
    return abs(a) <= face.half_size + tol and abs(b) <= face.half_size + tol


def edge_face_intersections(edges: List[Edge], faces: List[Face]) -> List[np.ndarray]:
    """
    Compute all intersection points between edges and faces.
    
    For each edge-face pair, check if the infinite line through the edge
    intersects the face plane, then verify the intersection is within
    both the edge segment and the face boundary.
    """
    points: List[np.ndarray] = []
    for edge in edges:
        p0, p1 = edge.p0, edge.p1
        for face in faces:
            hit, t, p = intersect_line_plane(p0, p1, face.center, face.normal)
            if not hit:
                continue
            
            # Restrict to segment [0, 1]
            if t < -EPS or t > 1.0 + EPS:
                continue
            
            if point_in_face(face, p):
                points.append(p)
    
    return points


def closest_points_on_lines(p1: np.ndarray, d1: np.ndarray,
                            p2: np.ndarray, d2: np.ndarray) -> Tuple[float, float, float]:
    """
    Find the closest points between two infinite lines.
    
    Line 1: p1 + s*d1
    Line 2: p2 + t*d2
    
    Returns: (s, t, distance)
        s, t: parameters for closest points
        distance: minimum distance between the lines
    """
    w0 = p1 - p2
    a = np.dot(d1, d1)
    b = np.dot(d1, d2)
    c = np.dot(d2, d2)
    d = np.dot(d1, w0)
    e = np.dot(d2, w0)
    
    denom = a * c - b * b
    
    # Lines are parallel
    if abs(denom) < EPS:
        return 0.0, 0.0, np.linalg.norm(w0 - d1 * (d / a)) if abs(a) > EPS else np.linalg.norm(w0)
    
    s = (b * e - c * d) / denom
    t = (a * e - b * d) / denom
    
    closest1 = p1 + s * d1
    closest2 = p2 + t * d2
    distance = np.linalg.norm(closest1 - closest2)
    
    return s, t, distance


def edge_edge_intersections(edges1: List[Edge], edges2: List[Edge], 
                           tol: float = 1e-6) -> List[np.ndarray]:
    """
    Compute intersection points between two sets of edges.
    
    For each pair of edges, find the closest points on the infinite lines.
    If the distance is small enough and both parameters are within [0,1],
    the edges intersect.
    """
    points: List[np.ndarray] = []
    
    for e1 in edges1:
        d1 = e1.p1 - e1.p0
        for e2 in edges2:
            d2 = e2.p1 - e2.p0
            
            s, t, dist = closest_points_on_lines(e1.p0, d1, e2.p0, d2)
            
            # Check if closest points are within segments and sufficiently close
            if (0 - EPS <= s <= 1 + EPS and 
                0 - EPS <= t <= 1 + EPS and 
                dist < tol):
                # Use midpoint of the two closest points
                p1 = e1.p0 + s * d1
                p2 = e2.p0 + t * d2
                p = (p1 + p2) / 2.0
                points.append(p)
    
    return points


# ---------- Analysis helpers ----------

def unique_points(points: Iterable[np.ndarray], ndigits: int = 9) -> List[np.ndarray]:
    """
    Remove duplicate points using rounded coordinates for comparison.
    
    Args:
        points: Iterable of 3D points
        ndigits: Number of decimal places for rounding
        
    Returns:
        List of unique points
    """
    seen: Set[Tuple[float, float, float]] = set()
    unique: List[np.ndarray] = []
    
    for p in points:
        key = round_tuple(p, ndigits=ndigits)
        if key not in seen:
            seen.add(key)
            unique.append(np.array(key))
    
    return unique


def analyze_distances(points: List[np.ndarray], 
                     max_pairs: Optional[int] = None) -> Dict[float, int]:
    """
    Compute pairwise distances and bucket them (rounded) to see main distance levels.
    
    Args:
        points: List of 3D points
        max_pairs: Maximum number of pairs to sample (None for all pairs)
        
    Returns:
        Dictionary mapping {rounded_distance: count}
    """
    dist_counts: Dict[float, int] = defaultdict(int)
    combos = itertools.combinations(range(len(points)), 2)
    
    for k, (i, j) in enumerate(combos):
        if max_pairs is not None and k >= max_pairs:
            break
        
        d = np.linalg.norm(points[i] - points[j])
        dr = round(d, 6)
        dist_counts[dr] += 1
    
    return dict(sorted(dist_counts.items()))


def scan_for_phi(distances: Dict[float, int], tol: float = 1e-3) -> List[Tuple[float, float, float]]:
    """
    Look for ratios of distances close to the golden ratio φ ≈ 1.618.
    
    Args:
        distances: Dictionary of distance values and their counts
        tol: Tolerance for matching φ
        
    Returns:
        List of (a, b, ratio) tuples where a/b ≈ φ
    """
    values = sorted(distances.keys())
    candidates: List[Tuple[float, float, float]] = []
    
    for i, a in enumerate(values):
        for b in values[:i]:
            if b < EPS:
                continue
            r = a / b
            if abs(r - PHI) < tol:
                candidates.append((a, b, r))
    
    return candidates


def analyze_directions(points: List[np.ndarray], 
                      max_pairs: Optional[int] = None) -> List[np.ndarray]:
    """
    Compute normalized direction vectors between pairs of points.
    
    We only care about unique directions up to sign (±v ~ v).
    
    Args:
        points: List of 3D points
        max_pairs: Maximum number of pairs to sample (None for all pairs)
        
    Returns:
        List of unique normalized direction vectors
    """
    dir_set: Set[Tuple[float, float, float]] = set()
    dirs: List[np.ndarray] = []
    combos = itertools.combinations(range(len(points)), 2)
    
    for k, (i, j) in enumerate(combos):
        if max_pairs is not None and k >= max_pairs:
            break
        
        v = points[j] - points[i]
        if np.linalg.norm(v) < EPS:
            continue
        
        v = normalize(v)
        
        # Canonicalize sign: make first nonzero component positive
        # This treats ±v as the same direction
        for component in v:
            if abs(component) > EPS:
                if component < 0:
                    v = -v
                break
        
        key = round_tuple(v, ndigits=6)
        if key not in dir_set:
            dir_set.add(key)
            dirs.append(np.array(key))
    
    return dirs


def analyze_angles(dirs: List[np.ndarray]) -> Dict[float, int]:
    """
    Compute angles between all pairs of direction vectors.
    
    Args:
        dirs: List of normalized direction vectors
        
    Returns:
        Dictionary mapping {angle_in_degrees: count}
    """
    angle_counts: Dict[float, int] = defaultdict(int)
    
    for i, d1 in enumerate(dirs):
        for d2 in dirs[i+1:]:
            # Compute angle using dot product
            cos_angle = np.clip(np.dot(d1, d2), -1.0, 1.0)
            angle = math.degrees(math.acos(cos_angle))
            angle_rounded = round(angle, 2)
            angle_counts[angle_rounded] += 1
    
    return dict(sorted(angle_counts.items()))


def print_sample(name: str, items: List, n: int = 10) -> None:
    """Print a sample of items from a list."""
    print(f"\n{name} (showing up to {n}):")
    for x in items[:n]:
        print("  ", x)
    if len(items) > n:
        print(f"   ... and {len(items) - n} more")


def print_stats(name: str, values: List[float]) -> None:
    """Print statistical summary of a list of values."""
    if not values:
        print(f"\n{name}: No data")
        return
    
    arr = np.array(values)
    print(f"\n{name}:")
    print(f"  Count: {len(values)}")
    print(f"  Min: {np.min(arr):.6f}")
    print(f"  Max: {np.max(arr):.6f}")
    print(f"  Mean: {np.mean(arr):.6f}")
    print(f"  Median: {np.median(arr):.6f}")
    print(f"  Std Dev: {np.std(arr):.6f}")


def save_results(filename: str, results: Dict[str, Any]) -> None:
    """Save analysis results to JSON file."""
    # Convert numpy arrays to lists for JSON serialization
    def convert(obj):
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        elif isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        return obj
    
    serializable = json.loads(json.dumps(results, default=convert))
    
    with open(filename, 'w') as f:
        json.dump(serializable, f, indent=2)
    
    print(f"\n✓ Results saved to: {filename}")


# ---------- Main pipeline ----------

def main(side: float = 2.0, angle: float = 30.0, 
         max_distance_pairs: Optional[int] = 20000,
         max_direction_pairs: Optional[int] = 8000,
         output_file: Optional[str] = None,
         verbose: bool = True) -> Dict[str, Any]:
    """Main execution pipeline for geometric analysis.
    
    Args:
        side: Edge length of the cubes
        angle: Rotation angle in degrees for cube B around z-axis
        max_distance_pairs: Maximum pairs to sample for distance analysis
        max_direction_pairs: Maximum pairs to sample for direction analysis
        output_file: If provided, save results to this JSON file
        verbose: Print detailed output to console
        
    Returns:
        Dictionary containing all analysis results
    """
    if verbose:
        print("=" * 70)
        print("Orion Octave Cubes – Geometry Test Harness")
        print("=" * 70)
    
    # 1. Define base cube (A) and rotated cube (B)
    center = np.zeros(3)

    # Rotation 0° for cube A (identity)
    R_id = np.eye(3)

    # Rotation angle about z-axis for cube B
    theta = math.radians(angle)
    Rz = rotation_matrix_z(theta)

    cubeA = Cube(center=center, side=side, R=R_id)
    cubeB = Cube(center=center, side=side, R=Rz)

    if verbose:
        print(f"\nConfiguration:")
        print(f"  Cube side length: {side}")
        print(f"  Cube A: axis-aligned")
        print(f"  Cube B: rotated {math.degrees(theta):.2f}° about z-axis")

    # 2. Collect vertices
    vertsA = cubeA.vertices()
    vertsB = cubeB.vertices()

    # 3. Compute intersections
    edgesA = cubeA.edges()
    edgesB = cubeB.edges()
    facesA = cubeA.faces()
    facesB = cubeB.faces()

    if verbose:
        print(f"\n{'-'*70}")
        print("Computing intersections...")
        print(f"{'-'*70}")
    
    # Edge-face intersections
    ef_AB = edge_face_intersections(edgesA, facesB)
    ef_BA = edge_face_intersections(edgesB, facesA)
    
    if verbose:
        print(f"  Edge(A)-Face(B) intersections: {len(ef_AB)}")
        print(f"  Edge(B)-Face(A) intersections: {len(ef_BA)}")
    
    # Edge-edge intersections
    ee_AB = edge_edge_intersections(edgesA, edgesB)
    
    if verbose:
        print(f"  Edge(A)-Edge(B) intersections: {len(ee_AB)}")

    # 4. Construct point set P and deduplicate
    all_points = vertsA + vertsB + ef_AB + ef_BA + ee_AB
    P = unique_points(all_points, ndigits=9)
    
    # Initialize results dictionary
    results = {
        'configuration': {
            'side_length': side,
            'rotation_angle_degrees': angle,
            'center': center.tolist()
        },
        'point_counts': {
            'vertices_A': len(vertsA),
            'vertices_B': len(vertsB),
            'edge_face_intersections': len(ef_AB) + len(ef_BA),
            'edge_edge_intersections': len(ee_AB),
            'total_raw': len(all_points),
            'unique_points': len(P)
        },
        'points': [p.tolist() for p in P]
    }

    if verbose:
        print(f"\n{'-'*70}")
        print("Point Set Summary")
        print(f"{'-'*70}")
        print(f"  Vertices (A): {len(vertsA)}")
        print(f"  Vertices (B): {len(vertsB)}")
        print(f"  Edge-Face intersections: {len(ef_AB) + len(ef_BA)}")
        print(f"  Edge-Edge intersections: {len(ee_AB)}")
        print(f"  Total raw points: {len(all_points)}")
        print(f"  Unique interference points (P): {len(P)}")

        print_sample("Sample vertices of Cube A", vertsA, n=8)
        print_sample("Sample vertices of Cube B", vertsB, n=8)
        print_sample("Sample edge-face intersection points", ef_AB + ef_BA, n=10)

    # 5. Distance analysis
    if verbose:
        print(f"\n{'='*70}")
        print("DISTANCE ANALYSIS")
        print(f"{'='*70}")
    
    dist_counts = analyze_distances(P, max_pairs=max_distance_pairs)
    
    if verbose:
        print(f"\nDistinct distance magnitudes (sampled): {len(dist_counts)}")
        print_sample("Distance spectrum (distance: count)", 
                    list(dist_counts.items()), n=15)
    
    # Statistical summary of distances
    all_distances = [d for d, count in dist_counts.items() for _ in range(count)]
    
    if verbose:
        print_stats("Distance Statistics", all_distances[:10000])  # Limit for performance
    
    results['distances'] = {
        'distinct_count': len(dist_counts),
        'spectrum': {str(k): v for k, v in list(dist_counts.items())[:50]},
        'statistics': {
            'min': float(np.min(all_distances[:10000])) if all_distances else 0,
            'max': float(np.max(all_distances[:10000])) if all_distances else 0,
            'mean': float(np.mean(all_distances[:10000])) if all_distances else 0,
            'median': float(np.median(all_distances[:10000])) if all_distances else 0,
            'std': float(np.std(all_distances[:10000])) if all_distances else 0
        }
    }

    # Golden ratio analysis
    phi_candidates = scan_for_phi(dist_counts, tol=1e-3)
    
    results['golden_ratio'] = {
        'phi_value': PHI,
        'candidate_count': len(phi_candidates),
        'candidates': [[float(a), float(b), float(r)] for a, b, r in phi_candidates[:20]]
    }
    
    if verbose:
        print(f"\n{'-'*70}")
        print(f"Golden Ratio (φ ≈ {PHI:.6f}) Analysis")
        print(f"{'-'*70}")
        
        if not phi_candidates:
            print("  No φ-ratio pairs found in sampled distances.")
            print("  (This does NOT mean φ is absent; tolerance or sampling may be insufficient)")
        else:
            print(f"  Found {len(phi_candidates)} candidate pairs where a/b ≈ φ:")
            for a, b, r in phi_candidates[:20]:
                print(f"    a={a:.6f}, b={b:.6f}, ratio={r:.6f} (error: {abs(r-PHI):.6f})")
            if len(phi_candidates) > 20:
                print(f"    ... and {len(phi_candidates) - 20} more")

    # 6. Direction analysis
    if verbose:
        print(f"\n{'='*70}")
        print("DIRECTION ANALYSIS")
        print(f"{'='*70}")
    
    dirs = analyze_directions(P, max_pairs=max_direction_pairs)
    
    results['directions'] = {
        'unique_count': len(dirs),
        'sample': [d.tolist() for d in dirs[:50]]
    }
    
    if verbose:
        print(f"\nUnique normalized directions (sampled): {len(dirs)}")
        print_sample("Sample direction vectors", dirs, n=20)

    # 7. Angle analysis
    if verbose:
        print(f"\n{'-'*70}")
        print("Angle Distribution Between Directions")
        print(f"{'-'*70}")
    
    angle_counts = analyze_angles(dirs)
    
    results['angles'] = {
        'distinct_count': len(angle_counts),
        'spectrum': {str(k): v for k, v in list(angle_counts.items())[:100]}
    }
    
    if verbose:
        print(f"\nDistinct angles: {len(angle_counts)}")
        print_sample("Angle spectrum (degrees: count)", 
                    list(angle_counts.items()), n=20)
    
    # Check for special angles (icosahedral symmetry)
    special_angles = {
        36.0: "Pentagon/Icosahedron",
        60.0: "Hexagon/Octahedron", 
        72.0: "Pentagon/Dodecahedron",
        90.0: "Cube/Octahedron",
        120.0: "Hexagon"
    }
    
    special_angle_results = {}
    for angle, description in sorted(special_angles.items()):
        count = sum(c for a, c in angle_counts.items() if abs(a - angle) < 0.5)
        special_angle_results[angle] = {'description': description, 'count': count}
    
    results['special_angles'] = special_angle_results
    
    if verbose:
        print(f"\n{'-'*70}")
        print("Special Angle Detection")
        print(f"{'-'*70}")
        found_special = False
        for angle, data in sorted(special_angle_results.items()):
            if data['count'] > 0:
                print(f"  {angle}° ({data['description']}): {data['count']} occurrences")
                found_special = True
        if not found_special:
            print("  No special symmetry angles detected in sample")

    # 8. Icosahedral direction check
    target = normalize(np.array([-math.sqrt(3), 1.0, 0.0]))
    closest = None
    closest_dot = -1.0
    
    for d in dirs:
        dot = abs(np.dot(d, target))  # Use abs to account for sign ambiguity
        if dot > closest_dot:
            closest_dot = dot
            closest = d

    ico_angle = math.degrees(math.acos(np.clip(closest_dot, 0.0, 1.0))) if closest is not None else None
    
    results['icosahedral_check'] = {
        'target': target.tolist(),
        'closest_match': closest.tolist() if closest is not None else None,
        'dot_product': float(closest_dot) if closest is not None else None,
        'angle_degrees': float(ico_angle) if ico_angle is not None else None,
        'match_quality': 'strong' if ico_angle and ico_angle < 5.0 else ('moderate' if ico_angle and ico_angle < 15.0 else 'weak')
    }
    
    if verbose:
        print(f"\n{'-'*70}")
        print("Icosahedral Direction Check")
        print(f"{'-'*70}")
        print(f"  Target direction: {round_tuple(target, 6)}")
        if closest is not None:
            print(f"  Closest match: {round_tuple(closest, 6)}")
            print(f"  Dot product: {closest_dot:.6f}")
            print(f"  Angle: {ico_angle:.2f}°")
            if ico_angle < 5.0:
                print("  ✓ Strong match found!")
            elif ico_angle < 15.0:
                print("  ~ Moderate match")
            else:
                print("  ✗ Weak match")
        else:
            print("  No directions computed.")

    # 9. Summary and next steps
    if verbose:
        print(f"\n{'='*70}")
        print("SUMMARY & NEXT STEPS")
        print(f"{'='*70}")
        
        print("\nCompleted Analysis:")
        print("  ✓ Cube vertex generation")
        print("  ✓ Edge-face intersection computation")
        print("  ✓ Edge-edge intersection computation")
        print("  ✓ Point deduplication")
        print("  ✓ Distance spectrum analysis")
        print("  ✓ Golden ratio detection")
        print("  ✓ Direction spectrum analysis")
        print("  ✓ Angle distribution analysis")
        
        print("\nFuture Enhancements:")
        print("  • Implement face-face intersection detection")
        print("  • Add convex hull computation for polyhedron detection")
        print("  • Compare against Coxeter H3/H4 root systems")
        print("  • Load and match canonical Platonic solid coordinates")
        print("  • Implement 4D polytope projection (120-cell, 600-cell)")
        print("  • Add visualization using matplotlib/plotly")
        print("  • Implement Archimedean/Catalan solid detection")
        print("  • Add symmetry group analysis")
        
        print(f"\n{'='*70}\n")
    
    # Save results if requested
    if output_file:
        save_results(output_file, results)
    
    return results


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Orion Octave Cubes – Geometry Test Harness',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic run with defaults
  python orion_octave_test.py
  
  # Custom cube size and rotation
  python orion_octave_test.py --side 3.0 --angle 45
  
  # Save results to JSON
  python orion_octave_test.py --output results.json
  
  # Quiet mode (minimal output)
  python orion_octave_test.py --quiet
  
  # Full analysis with more samples
  python orion_octave_test.py --max-distance-pairs 50000 --max-direction-pairs 20000
        """
    )
    
    parser.add_argument('--side', type=float, default=2.0,
                       help='Edge length of the cubes (default: 2.0)')
    parser.add_argument('--angle', type=float, default=30.0,
                       help='Rotation angle in degrees for cube B (default: 30.0)')
    parser.add_argument('--max-distance-pairs', type=int, default=20000,
                       help='Maximum pairs to sample for distance analysis (default: 20000)')
    parser.add_argument('--max-direction-pairs', type=int, default=8000,
                       help='Maximum pairs to sample for direction analysis (default: 8000)')
    parser.add_argument('--output', '-o', type=str, default=None,
                       help='Save results to JSON file')
    parser.add_argument('--quiet', '-q', action='store_true',
                       help='Suppress detailed console output')
    
    args = parser.parse_args()
    
    main(
        side=args.side,
        angle=args.angle,
        max_distance_pairs=args.max_distance_pairs,
        max_direction_pairs=args.max_direction_pairs,
        output_file=args.output,
        verbose=not args.quiet
    )
