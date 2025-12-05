# Automated Geometric Discovery System

## 🚀 Overview

A **fully automated** system for discovering optimal geometric configurations and "life-changing tech specs" through systematic parameter space exploration, machine learning pattern discovery, and comprehensive validation.

## 🎯 What It Does

This system automatically:
1. **Validates** all components with comprehensive automated tests
2. **Explores** parameter space systematically (grid search, parallel processing)
3. **Discovers** patterns using machine learning (clustering, anomaly detection, PCA)
4. **Generates** actionable tech specs with confidence scores and applications

## 📁 System Components

### Core Analysis Engine
- **`orion_octave_test.py`** - Geometric analysis engine (edge intersections, golden ratio detection, symmetry analysis)

### Automation Framework
- **`automated_discovery.py`** - Master orchestrator for full discovery pipeline
- **`auto_explorer.py`** - Automated parameter space exploration with parallel processing
- **`ml_discovery.py`** - Machine learning pattern discovery (DBSCAN, Isolation Forest, PCA)
- **`comprehensive_tests.py`** - Automated testing suite (unit, integration, property-based, ground truth)

### Web Interface
- **`app.py`** - Flask web application with REST API
- **`templates/index.html`** - Interactive dashboard UI
- **`static/`** - CSS and JavaScript for frontend

### Analysis Tools
- **`visualize.py`** - Standalone visualization tool
- **`gap_analysis.py`** - System capability gap analysis

## 🔥 Quick Start - Fully Automated Discovery

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Run Comprehensive Tests (Optional but Recommended)
```bash
python3 comprehensive_tests.py
```

### 3. Run Full Automated Discovery
```bash
python3 automated_discovery.py
```

This will:
- ✅ Validate system with 40+ automated tests
- 🔍 Explore 27 parameter configurations in parallel
- 🤖 Apply ML to discover patterns and anomalies
- 📊 Generate tech specs with confidence scores
- 💾 Save comprehensive reports to `discovery_output/`

**Expected runtime:** 5-15 minutes depending on hardware

## 📊 Output Structure

```
discovery_output/
└── YYYYMMDD_HHMMSS/              # Session directory
    ├── FINAL_DISCOVERY_REPORT.json
    ├── DISCOVERY_SUMMARY.txt      # Human-readable summary
    ├── exploration_results/
    │   ├── exploration_report.json
    │   ├── ml_discovery_report.json
    │   └── result_s*.json         # Individual configuration results
    └── ...
```

## 🎨 Interactive Web Dashboard (Alternative)

For real-time interactive analysis:

```bash
python3 app.py
```

Then open `http://localhost:5000` in your browser.

## 🧪 Individual Components

### Parameter Space Explorer
```bash
python3 auto_explorer.py
```
Systematically explores combinations of:
- Side lengths: [1.0, 2.0, 3.0]
- Angles: [15°, 30°, 36°, 45°, 60°, 72°, 90°, 108°, 120°]

### ML Pattern Discovery
```bash
# Run after exploration
python3 ml_discovery.py
```
Discovers:
- Natural clusters in parameter space
- Anomalous configurations worth investigating
- Strong feature correlations
- Principal components of variation

### Comprehensive Testing
```bash
python3 comprehensive_tests.py
```
Runs 40+ tests including:
- Unit tests for geometric primitives
- Integration tests for full pipeline
- Property-based tests (determinism, scaling, symmetry)
- Ground truth validation (45°, 60°, 90° configurations)
- Regression tests to prevent breaking changes

## 🔬 Discovered Tech Specs

The system generates tech specs with:
- **Name:** Discovery type
- **Confidence:** 0.0-1.0 score
- **Category:** Geometric Optimization, ML Discovery, Synthesis
- **Description:** What was discovered
- **Evidence:** Quantitative metrics supporting the discovery
- **Applications:** Potential real-world uses

### Example Applications from Discoveries

**Golden Ratio Peaks:**
- Optimal antenna array configuration
- Crystal lattice design with phi-based properties
- Architectural space-filling patterns

**Icosahedral Symmetry:**
- Viral capsid structure modeling
- Fullerene and carbon structure design
- Geodesic dome construction parameters

**High Symmetry Configurations:**
- Photonic crystal optimization
- Metamaterial unit cell design
- Periodic structure engineering

## 🛠️ Configuration

Edit `automated_discovery.py` to customize:

```python
config = ExplorationConfig(
    side_lengths=[1.0, 2.0, 3.0, 5.0],  # Add more sizes
    angles=[15, 30, 36, 45, 60, 72, 90, 108, 120, 144],  # Add more angles
    max_distance_pairs=20000,  # Increase for more accuracy
    max_direction_pairs=10000,
    parallel_workers=8  # Increase for faster exploration
)
```

## 📈 ML Methods Used

1. **DBSCAN Clustering** - Identifies natural groupings in parameter space
2. **Isolation Forest** - Detects anomalous configurations
3. **PCA** - Finds principal components of geometric variation
4. **Correlation Analysis** - Discovers relationships between features

## 🧮 Geometric Analysis Features

- ✅ Edge-face intersection detection
- ✅ Edge-edge intersection detection
- ✅ Golden ratio (φ) scanning
- ✅ Direction spectrum analysis
- ✅ Angle distribution analysis
- ✅ Special angle detection (30°, 36°, 45°, 60°, 72°, 90°)
- ✅ Icosahedral symmetry matching
- ✅ Distance spectrum analysis

## 🚦 System Status

**Fully Implemented:**
- ✅ Automated parameter space exploration
- ✅ Machine learning pattern discovery
- ✅ Comprehensive automated testing
- ✅ Golden ratio detection
- ✅ Symmetry analysis
- ✅ Parallel processing
- ✅ Tech spec generation
- ✅ Web dashboard

**Future Enhancements:**
- ⏳ Face-face intersection detection
- ⏳ GPU acceleration
- ⏳ Bayesian optimization
- ⏳ Real-time streaming visualization

## 📚 Architecture

```
User Request
    ↓
automated_discovery.py (Orchestrator)
    ↓
    ├─→ comprehensive_tests.py (Validation)
    ├─→ auto_explorer.py (Exploration)
    │      ├─→ orion_octave_test.py (Analysis)
    │      └─→ Parallel Workers
    ├─→ ml_discovery.py (Pattern Discovery)
    │      ├─→ DBSCAN, Isolation Forest
    │      └─→ PCA, Correlation Analysis
    └─→ Tech Spec Generation
           └─→ Final Reports
```

## 🎓 Understanding Results

### Confidence Scores
- **0.95-1.0:** Very high confidence, multiple converging lines of evidence
- **0.85-0.95:** High confidence, strong statistical/geometric evidence
- **0.75-0.85:** Moderate confidence, interesting pattern worth investigating
- **Below 0.75:** Low confidence, preliminary observation

### Discovery Types
- **Golden Ratio Peak:** Maximum φ occurrences found
- **Perfect Icosahedral Match:** Near-perfect symmetry alignment
- **High Symmetry Configuration:** Exceptional special angle counts
- **Geometric Phase Transition:** Abrupt changes in properties
- **Maximum Interference Density:** Optimal point lattice density
- **Anomalous Configuration:** ML-detected outlier
- **Natural Cluster:** ML-detected grouping

## 🐛 Troubleshooting

**Out of Memory:**
```python
# Reduce max_pairs in config
config = ExplorationConfig(
    max_distance_pairs=5000,  # Reduced
    max_direction_pairs=2500
)
```

**Slow Execution:**
```python
# Increase parallel workers
config = ExplorationConfig(
    parallel_workers=8  # Match your CPU cores
)
```

**Import Errors:**
```bash
pip install --upgrade -r requirements.txt
```

## 📝 Citation

If you use this system for research, please cite:
```
Automated Geometric Discovery System
Version 2.0
https://github.com/yourusername/orion-octave
```

## 📄 License

MIT License - See LICENSE file for details

## 🤝 Contributing

Contributions welcome! Areas of interest:
- Face-face intersection algorithms
- Additional ML methods (symbolic regression, genetic algorithms)
- GPU acceleration
- Additional geometric primitives
- Visualization enhancements

## 📞 Support

For issues, questions, or suggestions:
1. Check the troubleshooting section
2. Review the gap analysis: `python3 gap_analysis.py`
3. Run diagnostic tests: `python3 comprehensive_tests.py`
4. Open an issue on GitHub

---

**Ready to discover life-changing tech specs?**

```bash
python3 automated_discovery.py
```

🚀 **Let the automated discovery begin!**
