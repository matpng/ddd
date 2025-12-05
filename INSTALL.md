# Orion Octave Cubes - Installation & Usage Guide

## 🚀 Quick Start

### Installation

```bash
# Navigate to the project directory
cd /workspaces/ddd

# Install dependencies
pip install -r requirements.txt
```

### Running the Web Application

```bash
# Start the Flask development server
python3 app.py
```

The application will be available at: **http://localhost:5000**

## 📱 Web Application Features

### Interactive Dashboard
- **Real-time Analysis**: Run geometric calculations with custom parameters
- **Visual Analytics**: Interactive plots and 3D visualizations
- **Golden Ratio Detection**: Automatic detection of φ relationships
- **Symmetry Analysis**: Identify icosahedral and Platonic solid patterns
- **Export Results**: Download JSON data and PNG plots

### How to Use the Dashboard

1. **Configure Parameters**
   - Set cube side length (0.1 - 100 units)
   - Choose rotation angle (0 - 360 degrees)
   - Adjust sampling rates for precision vs. speed

2. **Run Analysis**
   - Click "Run Analysis" button
   - Wait for calculations to complete (5-30 seconds)

3. **Explore Results**
   - View summary statistics cards
   - Check special angle detections
   - Browse visualization tabs:
     - 3D Lattice: Interference point cloud
     - Distance Spectrum: Distance distribution
     - Angle Distribution: Direction angle analysis
     - Summary Report: Complete overview

4. **Export Data**
   - Download JSON results for further analysis
   - Save all plots as PNG images

## 🖥️ Command-Line Interface

For batch processing or scripting:

```bash
# Basic analysis
python3 orion_octave_test.py

# Custom parameters
python3 orion_octave_test.py --side 3.0 --angle 45

# Save results to JSON
python3 orion_octave_test.py --output results.json

# Quiet mode (no console output)
python3 orion_octave_test.py --quiet --angle 60 -o results_60deg.json

# High-precision analysis
python3 orion_octave_test.py \
  --max-distance-pairs 50000 \
  --max-direction-pairs 20000 \
  -o high_res_results.json
```

### CLI Options

| Option | Default | Description |
|--------|---------|-------------|
| `--side` | 2.0 | Edge length of cubes |
| `--angle` | 30.0 | Rotation angle (degrees) |
| `--max-distance-pairs` | 20000 | Distance analysis sample size |
| `--max-direction-pairs` | 8000 | Direction analysis sample size |
| `--output`, `-o` | None | Save results to JSON file |
| `--quiet`, `-q` | False | Suppress console output |

## 📊 Visualization Tools

### Standalone Visualization

```bash
# View results interactively
python3 visualize.py results.json

# Save specific plots
python3 visualize.py results.json --3d points_3d.png
python3 visualize.py results.json --distances distances.png
python3 visualize.py results.json --angles angles.png
python3 visualize.py results.json --summary summary.png

# Save all plots
python3 visualize.py results.json --all output_prefix
```

### Batch Analysis

```bash
# Analyze multiple angles at once
./batch_analyze.sh

# Custom output directory
./batch_analyze.sh my_results/
```

## 🧪 Recommended Test Cases

### Interesting Angles to Explore

1. **30° (Default)** - Classic interference pattern
2. **45°** - Octahedral symmetry emphasis
3. **60°** - Hexagonal patterns
4. **72°** - Pentagon/icosahedral signatures
5. **36°** - Strong golden ratio candidates

### Example Workflow

```bash
# Test multiple angles and compare
python3 orion_octave_test.py --angle 30 -o results_30.json
python3 orion_octave_test.py --angle 45 -o results_45.json
python3 orion_octave_test.py --angle 72 -o results_72.json

# Generate visualizations
python3 visualize.py results_30.json --summary summary_30.png
python3 visualize.py results_45.json --summary summary_45.png
python3 visualize.py results_72.json --summary summary_72.png
```

## 🔬 Understanding the Results

### Key Metrics

**Point Counts**
- Total unique points in interference lattice
- Breakdown: vertices, edge-face, edge-edge intersections

**Distance Statistics**
- Min, max, mean, median, standard deviation
- Distribution spectrum showing distance frequencies

**Golden Ratio Detection**
- Searches for distance pairs where a/b ≈ φ (1.618...)
- Indicates icosahedral/dodecahedral geometry presence

**Direction Analysis**
- Unique normalized direction vectors
- Angle distribution between directions

**Special Angles**
- 36° & 72° → Pentagon/Icosahedron/Dodecahedron
- 60° & 120° → Hexagon/Octahedron
- 90° → Cube/Octahedron

**Icosahedral Match**
- Tests for known icosahedral direction vectors
- Quality ratings: Strong (<5°), Moderate (<15°), Weak (>15°)

## 🛠️ Troubleshooting

### Common Issues

**Port already in use**
```bash
# Change the port in app.py or kill existing process
lsof -ti:5000 | xargs kill -9
```

**Import errors**
```bash
# Reinstall dependencies
pip install --force-reinstall -r requirements.txt
```

**Out of memory**
```bash
# Reduce sample sizes
python3 orion_octave_test.py \
  --max-distance-pairs 5000 \
  --max-direction-pairs 2000
```

**Plots not displaying**
- Check matplotlib backend in app.py (should be 'Agg')
- Clear browser cache and refresh
- Check browser console for JavaScript errors

## 📈 Performance Tips

1. **Start Small**: Use default parameters first
2. **Incremental Precision**: Gradually increase sample sizes
3. **Batch Processing**: Use `batch_analyze.sh` for multiple runs
4. **Web vs. CLI**: CLI is faster for batch work, web UI for exploration

## 🔐 Production Deployment

For production use:

1. **Use a production WSGI server**
   ```bash
   pip install gunicorn
   gunicorn -w 4 -b 0.0.0.0:8000 app:app
   ```

2. **Enable HTTPS** with nginx or similar reverse proxy

3. **Add authentication** if exposing publicly

4. **Use Redis** for caching instead of in-memory dictionary

5. **Database** for persistent result storage

## 📚 API Reference

### POST /api/analyze
Run geometric analysis

**Request Body:**
```json
{
  "side": 2.0,
  "angle": 30.0,
  "max_distance_pairs": 20000,
  "max_direction_pairs": 8000
}
```

**Response:**
```json
{
  "success": true,
  "cache_key": "2.0_30.0_20000_8000",
  "summary": { ... }
}
```

### GET /api/plot/{plot_type}/{cache_key}
Generate plot image

**Plot Types:** `3d`, `distances`, `angles`, `summary`

**Returns:** PNG image

### GET /api/download/{cache_key}
Download results as JSON

**Returns:** JSON file

## 🎓 Educational Use

This tool is excellent for:
- Computational geometry courses
- Sacred geometry exploration
- Platonic solid research
- Golden ratio studies
- 3D visualization projects
- Mathematical art generation

## 📞 Support

For issues or questions:
- Check the console output for detailed error messages
- Review the analysis TODO comments in the code
- Examine the JSON output for raw data

## 🚀 Next Steps

Explore the code extensions mentioned in the main README:
- Face-face intersections
- Convex hull polyhedron detection
- Coxeter group comparisons
- 4D polytope projections
- Advanced visualization options

---

**Happy Exploring!** 🎯✨
