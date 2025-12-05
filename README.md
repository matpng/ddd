# Orion Octave Cubes – Geometry Test Harness

A sophisticated computational geometry tool for analyzing interference patterns between rotated cubes, with a focus on detecting golden ratio relationships, icosahedral symmetries, and Platonic solid signatures.

## ✨ Features

- **🌐 Interactive Web Dashboard** - Modern UI for real-time geometric analysis
- **📊 Advanced Visualizations** - 3D plots, distance spectra, angle distributions
- **✨ Golden Ratio Detection** - Automatic identification of φ relationships
- **⬡ Symmetry Analysis** - Icosahedral and Platonic solid pattern recognition
- **🔬 High-Precision Calculations** - Configurable sampling for accuracy vs. speed
- **💾 Data Export** - Download results as JSON and plots as PNG
- **⚡ Batch Processing** - CLI tools for automated analysis

## 🚀 Quick Start - Web Application

```bash
# Install dependencies
pip install -r requirements.txt

# Start the web application
./start_app.sh
# OR
python3 app.py
```

Then open your browser to: **http://localhost:5000**

## 🎯 Overview

This script performs deep geometric analysis of two interpenetrating cubes:
- **Cube A**: Axis-aligned reference cube
- **Cube B**: Rotated cube (default: 30° around z-axis)

The analysis computes all intersection points (vertices, edge-face, edge-edge) to create an "interference lattice" and then analyzes this point set for:

- **Distance spectrum** – Looking for golden ratio (φ) relationships
- **Direction spectrum** – Detecting icosahedral and Platonic symmetries  
- **Angle distributions** – Finding special angles (36°, 60°, 72°, 90°, 120°)
- **Geometric patterns** – Signatures of higher-dimensional polytopes

## 🖥️ Usage Options

### 1. Web Application (Recommended)

The interactive dashboard provides the easiest way to explore the geometry:

```bash
./start_app.sh
```

Features:
- Real-time parameter adjustment
- Interactive visualizations
- Golden ratio and symmetry detection
- One-click result export
- Special angle highlighting

### 2. Command-Line Interface

For batch processing or scripting:

```bash
# Run with default parameters (2.0 side length, 30° rotation)
python3 orion_octave_test.py

# Run with custom cube size and rotation angle
python orion_octave_test.py --side 3.0 --angle 45

# Save results to JSON file
python orion_octave_test.py --output results.json

# Quiet mode (minimal output)
python orion_octave_test.py --quiet

# Full analysis with more samples
python orion_octave_test.py --max-distance-pairs 50000 --max-direction-pairs 20000
```

### Command-Line Options

| Option | Default | Description |
|--------|---------|-------------|
| `--side` | 2.0 | Edge length of both cubes |
| `--angle` | 30.0 | Rotation angle in degrees for cube B (around z-axis) |
| `--max-distance-pairs` | 20000 | Maximum point pairs to sample for distance analysis |
| `--max-direction-pairs` | 8000 | Maximum point pairs to sample for direction analysis |
| `--output`, `-o` | None | Save results to JSON file |
| `--quiet`, `-q` | False | Suppress detailed console output |

## 📊 What It Analyzes

### 1. **Intersection Detection**
- Computes all 8 vertices for each cube
- Finds edge-face intersection points (edges of A through faces of B, and vice versa)
- Finds edge-edge intersection points (where edges cross)
- Deduplicates points to create unique interference lattice

### 2. **Distance Analysis**
- Computes pairwise distances between all unique points
- Buckets distances to identify primary distance levels
- Scans for golden ratio relationships (where a/b ≈ φ ≈ 1.618)
- Provides statistical summary (min, max, mean, median, std dev)

### 3. **Direction Analysis**  
- Extracts normalized direction vectors between point pairs
- Canonicalizes directions (treats ±v as equivalent)
- Identifies unique directional axes in the interference pattern

### 4. **Angle Distribution**
- Computes angles between all direction pairs
- Detects special symmetry angles:
  - **36° & 72°**: Pentagon/Icosahedron/Dodecahedron signatures
  - **60° & 120°**: Hexagon/Octahedron signatures
  - **90°**: Cube/Octahedron signatures

### 5. **Icosahedral Symmetry Check**
- Tests for known icosahedral direction vectors
- Reports closest match and angular deviation
- Quality rating: Strong (<5°), Moderate (<15°), Weak (>15°)

## 📈 Sample Output

```
======================================================================
Orion Octave Cubes – Geometry Test Harness
======================================================================

Configuration:
  Cube side length: 2.0
  Cube A: axis-aligned
  Cube B: rotated 30.00° about z-axis

----------------------------------------------------------------------
Computing intersections...
----------------------------------------------------------------------
  Edge(A)-Face(B) intersections: 16
  Edge(B)-Face(A) intersections: 16
  Edge(A)-Edge(B) intersections: 16

----------------------------------------------------------------------
Point Set Summary
----------------------------------------------------------------------
  Vertices (A): 8
  Vertices (B): 8
  Edge-Face intersections: 32
  Edge-Edge intersections: 16
  Total raw points: 64
  Unique interference points (P): 32

======================================================================
DISTANCE ANALYSIS
======================================================================

Distinct distance magnitudes (sampled): 32

Golden Ratio (φ ≈ 1.618034) Analysis
----------------------------------------------------------------------
  Found 1 candidate pairs where a/b ≈ φ:
    a=2.368057, b=1.464102, ratio=1.617413 (error: 0.000621)

======================================================================
DIRECTION ANALYSIS
======================================================================

Unique normalized directions (sampled): 161

----------------------------------------------------------------------
Special Angle Detection
----------------------------------------------------------------------
  36.0° (Pentagon/Icosahedron): 126 occurrences
  60.0° (Hexagon/Octahedron): 98 occurrences
  72.0° (Pentagon/Dodecahedron): 93 occurrences
  90.0° (Cube/Octahedron): 320 occurrences
  120.0° (Hexagon): 82 occurrences

----------------------------------------------------------------------
Icosahedral Direction Check
----------------------------------------------------------------------
  Target direction: (-0.866025, 0.5, 0.0)
  Closest match: (0.866025, -0.5, -0.0)
  Dot product: 1.000000
  Angle: 0.05°
  ✓ Strong match found!
```

## 🏗️ Architecture

### Core Classes

- **`Cube`**: Represents an oriented cube with rotation matrix
  - `vertices()` – Returns 8 corner points
  - `edges()` – Returns 12 edges
  - `faces()` – Returns 6 faces with normals and basis vectors

- **`Face`**: Square face with center, normal, and orthonormal basis
  - `vertices()` – Returns 4 corner points

- **`Edge`**: Line segment with start/end points
  - `length()`, `direction()`, `midpoint()` methods

### Key Functions

**Intersection Detection:**
- `intersect_line_plane()` – Line-plane intersection
- `point_in_face()` – Point-in-square containment test
- `edge_face_intersections()` – Edge-face crossing detection
- `edge_edge_intersections()` – Edge-edge crossing detection
- `closest_points_on_lines()` – Minimum distance between lines

**Analysis:**
- `analyze_distances()` – Pairwise distance distribution
- `scan_for_phi()` – Golden ratio detection
- `analyze_directions()` – Direction vector extraction
- `analyze_angles()` – Angle distribution computation
- `unique_points()` – Point deduplication

**Utilities:**
- `rotation_matrix_z()` – Z-axis rotation matrix
- `rotation_matrix_axis()` – Arbitrary axis rotation (Rodrigues formula)
- `normalize()` – Vector normalization
- `save_results()` – JSON export

## 🔬 Scientific Context

This tool is designed to explore:

1. **Golden Ratio in 3D Geometry**: The golden ratio φ appears in many Platonic and Archimedean solids, particularly the icosahedron and dodecahedron.

2. **Icosahedral Symmetry**: The icosahedron has 120 symmetry operations and exhibits five-fold rotational symmetry, related to the golden ratio.

3. **Coxeter Groups**: The H3 Coxeter group (icosahedral symmetry) and H4 group (600-cell) have deep connections to the golden ratio.

4. **Higher Dimensions**: The analysis may reveal projections of 4D polytopes (120-cell, 600-cell) into 3D space.

## 🛠️ Extending the Code

The script includes scaffolding for future enhancements:

- **Face-face intersections**: Computing polygon-polygon intersections
- **Convex hull analysis**: Using scipy.spatial.ConvexHull to detect embedded polyhedra
- **Visualization**: Add matplotlib/plotly 3D visualization of point clouds
- **Coxeter comparison**: Load H3/H4 root systems and compare directions
- **Platonic solid matching**: Template matching against canonical coordinates
- **4D projections**: Project 120-cell and 600-cell vertices to 3D

### Adding a New Analysis

```python
# Example: Add a new analysis function
def analyze_convex_hull(points: List[np.ndarray]) -> Dict[str, Any]:
    """Compute convex hull and analyze its properties."""
    from scipy.spatial import ConvexHull
    
    hull = ConvexHull(np.array(points))
    return {
        'vertices': hull.vertices.tolist(),
        'faces': hull.simplices.tolist(),
        'volume': float(hull.volume),
        'surface_area': float(hull.area)
    }

# Then add to main():
hull_results = analyze_convex_hull(P)
results['convex_hull'] = hull_results
```

## 📝 Output Format

When using `--output results.json`, the script saves:

```json
{
  "configuration": {
    "side_length": 2.0,
    "rotation_angle_degrees": 30.0,
    "center": [0.0, 0.0, 0.0]
  },
  "point_counts": {
    "vertices_A": 8,
    "vertices_B": 8,
    "edge_face_intersections": 32,
    "edge_edge_intersections": 16,
    "total_raw": 64,
    "unique_points": 32
  },
  "points": [[...], ...],
  "distances": {
    "distinct_count": 32,
    "spectrum": {...},
    "statistics": {
      "min": 0.42265,
      "max": 3.464102,
      "mean": 2.194942,
      "median": 2.171297,
      "std": 0.743385
    }
  },
  "golden_ratio": {
    "phi_value": 1.618034,
    "candidate_count": 1,
    "candidates": [[2.368057, 1.464102, 1.617413]]
  },
  "directions": {...},
  "angles": {...},
  "special_angles": {...},
  "icosahedral_check": {...}
}
```

## 🧪 Testing Different Configurations

```bash
# Explore different rotation angles
python orion_octave_test.py --angle 15 -o results_15deg.json
python orion_octave_test.py --angle 45 -o results_45deg.json
python orion_octave_test.py --angle 60 -o results_60deg.json

# Test with different cube sizes
python orion_octave_test.py --side 1.0 --angle 30 -o results_small.json
python orion_octave_test.py --side 5.0 --angle 30 -o results_large.json

# High-precision analysis
python orion_octave_test.py \
  --max-distance-pairs 100000 \
  --max-direction-pairs 50000 \
  -o results_highres.json
```

## 📚 References

- **Coxeter, H.S.M.** - Regular Polytopes (Dover, 1973)
- **Conway & Sloane** - Sphere Packings, Lattices and Groups
- **Baez, John** - "The Octonions" (on exotic symmetries)
- **Livio, Mario** - The Golden Ratio: The Story of Phi

## 🤝 Contributing

To add new features:

1. Add new analysis functions following existing patterns
2. Update the `main()` function to call your analysis
3. Add results to the `results` dictionary
4. Update documentation in this README

## 📂 Project Structure

```
ddd/
├── app.py                    # Flask web application
├── orion_octave_test.py     # Core analysis engine
├── visualize.py             # Standalone visualization tool
├── batch_analyze.sh         # Batch processing script
├── start_app.sh             # Quick start script
├── requirements.txt         # Python dependencies
├── INSTALL.md              # Detailed installation guide
├── README.md               # This file
├── templates/
│   └── index.html          # Web UI template
└── static/
    ├── css/
    │   └── style.css       # Dashboard styles
    └── js/
        └── app.js          # Frontend JavaScript
```

## 🎓 Example Use Cases

1. **Sacred Geometry Research**: Explore golden ratio manifestations in 3D
2. **Platonic Solid Studies**: Detect icosahedral and dodecahedral patterns
3. **Computational Geometry Education**: Visual learning tool for students
4. **Mathematical Art**: Generate interference patterns for artistic projects
5. **Symmetry Analysis**: Study Coxeter groups and root systems

## 🔧 Technical Details

**Backend:**
- Python 3.8+
- NumPy for numerical computations
- Flask for web framework
- Matplotlib for plotting

**Frontend:**
- Vanilla JavaScript (no frameworks needed)
- Modern CSS with gradients and animations
- Responsive design for mobile/desktop

**Analysis Engine:**
- Edge-face intersection detection
- Edge-edge intersection computation
- Point deduplication with precision control
- Distance and direction spectrum analysis
- Golden ratio scanning algorithm
- Special angle detection system

## 📄 License

This is a research/educational tool. Use freely for academic and personal projects.

## 🙏 Acknowledgments

Inspired by the work of:
- H.S.M. Coxeter on regular polytopes
- Research in icosahedral symmetry and the golden ratio
- Sacred geometry and Platonic solid traditions

---

**Author**: Computational Geometry Research  
**Version**: 2.0  
**Last Updated**: December 2025

**Web Dashboard**: http://localhost:5000 (when running)

For detailed installation and usage instructions, see [INSTALL.md](INSTALL.md)
ddd
