#!/usr/bin/env python3
"""
Orion Octave Cubes - Web Application
A Flask-based web interface for interactive geometric analysis
"""

from flask import Flask, render_template, request, jsonify, send_file
import json
import io
import base64
import os
import logging
from pathlib import Path
from collections import OrderedDict
from datetime import datetime
from typing import Dict, Any
import numpy as np
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
import re

# Import our modules
from orion_octave_test import main as run_analysis
from config import Config
from discovery_manager import DiscoveryManager
from daemon_monitor import daemon_monitor
from ml_integration import initialize_ml_integration
from security_middleware import (
    initialize_security,
    rate_limit,
    validate_request
)
from prometheus_metrics import (
    setup_metrics,
    start_metrics_updater,
    metrics as prometheus_metrics
)
import threading
import time

# Setup logging
logging.basicConfig(
    level=getattr(logging, Config.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Suppress matplotlib font manager debug logs
logging.getLogger('matplotlib.font_manager').setLevel(logging.WARNING)

app = Flask(__name__)
app.config.from_object(Config)

# Initialize security middleware
initialize_security(app)

# Initialize Prometheus metrics
setup_metrics(app)

# Store analysis results with size limit
class LRUCache:
    """Simple LRU cache with size limit."""
    def __init__(self, max_size=100):
        self.cache = OrderedDict()
        self.max_size = max_size
    
    def get(self, key):
        if key not in self.cache:
            return None
        self.cache.move_to_end(key)
        return self.cache[key]
    
    def set(self, key, value):
        if key in self.cache:
            self.cache.move_to_end(key)
        self.cache[key] = value
        if len(self.cache) > self.max_size:
            self.cache.popitem(last=False)
    
    def __contains__(self, key):
        return key in self.cache
    
    def __getitem__(self, key):
        return self.get(key)
    
    def __setitem__(self, key, value):
        self.set(key, value)

analysis_cache = LRUCache(max_size=Config.CACHE_MAX_SIZE) if Config.CACHE_ENABLED else {}

# Initialize discovery manager
discovery_manager = DiscoveryManager()

# Initialize ML integration
ml_integration = initialize_ml_integration(discovery_manager)

# Autonomous daemon status
daemon_status = {
    'running': False,
    'discoveries_today': 0,
    'last_discovery': None,
    'total_discoveries': 0,
    'started_at': None
}


# ============================================================================
# DAEMON STARTUP FUNCTIONS (must be defined before calling)
# ============================================================================

def run_autonomous_daemon():
    """Background daemon that continuously runs autonomous discoveries."""
    global daemon_status
    
    try:
        daemon_monitor.start()
        daemon_status['running'] = True
        daemon_status['started_at'] = datetime.utcnow().isoformat()
        logger.info("Starting autonomous discovery daemon...")
        
        discovery_interval = int(os.environ.get('DISCOVERY_INTERVAL', '3600'))  # Default 1 hour
        warmup_delay = int(os.environ.get('DAEMON_WARMUP_DELAY', '60'))  # Default 60s warmup
        
        # Warmup delay to let app fully initialize
        logger.info(f"Daemon warmup: waiting {warmup_delay}s before first discovery...")
        time.sleep(warmup_delay)
        logger.info("Daemon warmup complete. Starting discovery cycles...")
        
        cycle_count = 0
        
        while daemon_status['running']:
            try:
                cycle_count += 1
                logger.info(f"Starting discovery cycle {cycle_count}...")
                
                # Rotate through different discovery modes
                mode = cycle_count % 4
                
                if mode == 0:
                    # Mode 1: Standard angle sweep (original)
                    _run_angle_sweep_discovery()
                elif mode == 1:
                    # Mode 2: Fine-grained sweep around golden ratio angles
                    _run_golden_ratio_discovery()
                elif mode == 2:
                    # Mode 3: Special symmetry angles
                    _run_symmetry_discovery()
                elif mode == 3:
                    # Mode 4: Parameter variation (different cube sizes)
                    _run_parameter_sweep_discovery()
                
                logger.info(f"Autonomous discovery cycle {cycle_count} complete. Sleeping for {discovery_interval}s...")
                
                # Sleep in chunks to allow for graceful shutdown
                for _ in range(discovery_interval):
                    if not daemon_status['running']:
                        break
                    time.sleep(1)
                    
            except Exception as e:
                logger.error(f"Error in discovery cycle {cycle_count}: {e}", exc_info=True)
                # Wait before retrying
                time.sleep(60)
    
    except Exception as e:
        logger.error(f"Fatal error in autonomous daemon: {e}", exc_info=True)
        daemon_status['running'] = False
    
    finally:
        logger.info("Autonomous discovery daemon stopped.")


def _run_angle_sweep_discovery():
    """Standard angle sweep discovery mode."""
    logger.info("Mode 1: Running standard angle sweep...")
    angles_to_test = [15, 30, 45, 60, 75, 90, 105, 120, 135, 150, 165]
    
    for angle in angles_to_test:
        if not daemon_status['running']:
            break
        _discover_angle(angle, 'autonomous_angle_sweep')


def _run_golden_ratio_discovery():
    """Fine-grained sweep around golden ratio angles."""
    logger.info("Mode 2: Running golden ratio angle discovery...")
    # Golden angle ≈ 137.5°, Fibonacci angles
    golden_angles = [
        30.0, 31.7, 33.7, 36.0,  # Pentagon region
        51.8, 58.3, 63.4,         # Golden spiral region
        137.5, 138.0, 138.5,      # Golden angle
        222.5, 223.0, 223.5       # Complementary golden angle
    ]
    
    for angle in golden_angles:
        if not daemon_status['running']:
            break
        _discover_angle(angle, 'golden_ratio_sweep')


def _run_symmetry_discovery():
    """Test angles corresponding to high-symmetry crystal systems."""
    logger.info("Mode 3: Running crystal symmetry discovery...")
    # Crystallographic special angles
    symmetry_angles = [
        54.74,   # Tetrahedral angle (diamond)
        70.53,   # Rhombohedral 
        109.47,  # Tetrahedral sp3 (methane)
        120.0,   # Trigonal/hexagonal
        144.0,   # Pentagon diagonal
        168.0    # Near-linear
    ]
    
    for angle in symmetry_angles:
        if not daemon_status['running']:
            break
        _discover_angle(angle, 'symmetry_sweep')


def _run_parameter_sweep_discovery():
    """Vary cube size ratios for scaling discoveries."""
    logger.info("Mode 4: Running parameter sweep discovery...")
    # Different cube size ratios
    configs = [
        (1.5, 45),   # Smaller cube, classic angle
        (2.5, 60),   # Larger cube, hexagonal
        (1.8, 72),   # Golden ratio size, pentagonal
        (2.2, 36),   # Varied size, icosahedral
    ]
    
    for size, angle in configs:
        if not daemon_status['running']:
            break
        _discover_with_params(size, angle, 'parameter_sweep')


def _generate_discovery_title(discovery: Dict[str, Any]) -> str:
    """Generate a descriptive title for a discovery."""
    disc_type = discovery.get('type', 'unknown')
    data = discovery.get('data', {})
    summary = data.get('summary', {})
    angle = data.get('angle', 0)
    
    # Extract key metrics
    unique_points = summary.get('unique_points', 0)
    golden_ratio = summary.get('golden_ratio_candidates', 0)
    special_angles = summary.get('special_angles', {})
    
    # Determine dominant characteristic
    title_parts = []
    
    if golden_ratio > 3:
        title_parts.append("Golden Ratio Rich")
    
    # Check for dominant special angles
    dominant_angles = []
    for ang, data_val in special_angles.items():
        # Convert angle key to string if it's a float
        ang_str = str(float(ang)) if isinstance(ang, (int, float)) else str(ang)
        count = data_val.get('count', 0) if isinstance(data_val, dict) else data_val
        if count > 50:
            if ang_str in ['36.0', '72.0']:
                dominant_angles.append("Pentagonal")
            elif ang_str == '60.0':
                dominant_angles.append("Hexagonal")
            elif ang_str == '90.0':
                dominant_angles.append("Cubic")
    
    if dominant_angles:
        title_parts.append(f"{'/'.join(set(dominant_angles))} Symmetry")
    
    # Complexity indicator
    if unique_points > 40:
        title_parts.append("High-Complexity")
    elif unique_points > 25:
        title_parts.append("Medium-Complexity")
    
    # Angle description
    if angle:
        title_parts.append(f"{angle}° Rotation")
    
    # Discovery type
    type_names = {
        'autonomous_angle_sweep': 'Angle Sweep',
        'golden_ratio_sweep': 'Golden Ratio',
        'symmetry_sweep': 'Symmetry',
        'parameter_sweep': 'Parameter',
        'multi_axis': 'Multi-Axis'
    }
    type_name = type_names.get(disc_type, disc_type.replace('_', ' ').title())
    
    if title_parts:
        return f"{' '.join(title_parts)} - {type_name} Discovery"
    else:
        return f"{type_name} Discovery at {angle}°"


def _convert_markdown_to_pdf(markdown_text: str, discovery_id: str) -> bytes:
    """Convert markdown research paper to PDF format."""
    from io import BytesIO
    
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter,
                           rightMargin=72, leftMargin=72,
                           topMargin=72, bottomMargin=18)
    
    # Container for PDF elements
    story = []
    
    # Styles
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=18,
        textColor=colors.HexColor('#2E86AB'),
        spaceAfter=30,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=colors.HexColor('#2E86AB'),
        spaceAfter=12,
        spaceBefore=12,
        fontName='Helvetica-Bold'
    )
    
    subheading_style = ParagraphStyle(
        'CustomSubHeading',
        parent=styles['Heading3'],
        fontSize=12,
        textColor=colors.HexColor('#555555'),
        spaceAfter=10,
        spaceBefore=10,
        fontName='Helvetica-Bold'
    )
    
    body_style = ParagraphStyle(
        'CustomBody',
        parent=styles['BodyText'],
        fontSize=10,
        alignment=TA_JUSTIFY,
        spaceAfter=12
    )
    
    # Parse markdown and convert to PDF elements
    lines = markdown_text.split('\n')
    i = 0
    
    while i < len(lines):
        line = lines[i].strip()
        
        if not line:
            i += 1
            continue
        
        # Title (# )
        if line.startswith('# '):
            text = line[2:].strip()
            story.append(Paragraph(text, title_style))
            story.append(Spacer(1, 0.2*inch))
        
        # Heading 2 (## )
        elif line.startswith('## '):
            text = line[3:].strip()
            story.append(Spacer(1, 0.1*inch))
            story.append(Paragraph(text, heading_style))
        
        # Heading 3 (### )
        elif line.startswith('### '):
            text = line[4:].strip()
            story.append(Paragraph(text, subheading_style))
        
        # Horizontal rule
        elif line.startswith('---'):
            story.append(Spacer(1, 0.1*inch))
            from reportlab.platypus import HRFlowable
            story.append(HRFlowable(width="100%", thickness=1, color=colors.grey))
            story.append(Spacer(1, 0.1*inch))
        
        # Table
        elif line.startswith('|') and i + 1 < len(lines) and lines[i + 1].strip().startswith('|'):
            table_data = []
            while i < len(lines) and lines[i].strip().startswith('|'):
                row = [cell.strip() for cell in lines[i].split('|')[1:-1]]
                # Skip separator row
                if not all(set(cell.replace('-', '').strip()) == set() or cell.strip() == '' for cell in row):
                    table_data.append(row)
                i += 1
            
            if table_data:
                t = Table(table_data)
                t.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2E86AB')),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 10),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                    ('GRID', (0, 0), (-1, -1), 1, colors.grey)
                ]))
                story.append(t)
                story.append(Spacer(1, 0.2*inch))
            continue
        
        # Bold text
        elif line.startswith('**') and line.endswith('**'):
            text = line[2:-2]
            p = Paragraph(f"<b>{text}</b>", body_style)
            story.append(p)
        
        # List item
        elif line.startswith('- '):
            text = line[2:].strip()
            p = Paragraph(f"• {text}", body_style)
            story.append(p)
        
        # Numbered list
        elif re.match(r'^\d+\.', line):
            text = line.split('.', 1)[1].strip()
            p = Paragraph(f"{line.split('.')[0]}. {text}", body_style)
            story.append(p)
        
        # Regular paragraph
        else:
            # Clean up markdown formatting
            text = line.replace('**', '<b>').replace('**', '</b>')
            text = text.replace('`', '<font name="Courier">')
            text = text.replace('`', '</font>')
            p = Paragraph(text, body_style)
            story.append(p)
        
        i += 1
    
    # Build PDF
    doc.build(story)
    
    pdf_data = buffer.getvalue()
    buffer.close()
    return pdf_data


def _generate_research_paper(discovery: Dict[str, Any]) -> str:
    """Generate a research paper in Markdown format for a discovery."""
    
    # Extract metadata
    disc_id = discovery.get('id', 'unknown')
    disc_type = discovery.get('type', 'unknown')
    timestamp = discovery.get('timestamp', '')
    data = discovery.get('data', {})
    summary = data.get('summary', {})
    
    # Paper content
    paper = f"""# Geometric Analysis of Orion Octave Cube Configuration
## Discovery Report: {disc_id}

**Discovery Type:** {disc_type}  
**Analysis Date:** {timestamp}  
**Generated:** {datetime.utcnow().isoformat()}

---

## Abstract

This report presents a computational geometric analysis of cube rotation configurations, 
exploring the emergence of special geometric relationships and symmetries. The analysis 
focuses on point distributions, distance patterns, angular relationships, and potential 
golden ratio occurrences in three-dimensional space.

## 1. Introduction

The Orion Octave Cube system analyzes the geometric properties that emerge when rotating 
cube B around the z-axis relative to a fixed cube A. This study investigates:

- Unique point distributions in 3D space
- Distance relationships between vertices
- Angular symmetries and special angles
- Golden ratio candidates
- Geometric invariants

## 2. Methodology

**Parameters:**
- Cube Side Length: {data.get('side', 2.0)}
- Rotation Angle: {data.get('angle', 'N/A')}°
- Sample Size (Distances): {data.get('max_distance_pairs', 'N/A')}
- Sample Size (Directions): {data.get('max_direction_pairs', 'N/A')}

**Analysis Techniques:**
- Vertex enumeration and transformation
- Pairwise distance calculation
- Direction vector analysis
- Angular relationship detection
- Golden ratio proximity testing

## 3. Results

### 3.1 Point Distribution
- **Unique Points:** {summary.get('unique_points', 'N/A')}
- **Spatial Configuration:** 3D coordinate system with rotation-induced symmetry

### 3.2 Distance Analysis
- **Unique Distances:** {summary.get('unique_distances', 'N/A')}
- **Maximum Distance:** {summary.get('max_distance', 0):.6f if isinstance(summary.get('max_distance'), (int, float)) else 'N/A'}
- **Minimum Distance:** {summary.get('min_distance', 0):.6f if isinstance(summary.get('min_distance'), (int, float)) else 'N/A'}
- **Mean Distance:** {summary.get('distance_mean', 0):.6f if isinstance(summary.get('distance_mean'), (int, float)) else 'N/A'}

### 3.3 Angular Relationships
"""
    
    # Add special angles if available
    special_angles = summary.get('special_angles', {})
    if special_angles:
        paper += "\n**Special Angles Detected:**\n\n"
        paper += "| Angle | Geometric Significance | Occurrences |\n"
        paper += "|-------|----------------------|-------------|\n"
        
        angle_descriptions = {
            '36.0': 'Pentagon/Icosahedron',
            '60.0': 'Hexagon/Octahedron',
            '72.0': 'Pentagon/Dodecahedron',
            '90.0': 'Cube/Octahedron',
            '120.0': 'Hexagon'
        }
        
        for angle, angle_data in sorted(special_angles.items(), key=lambda x: float(x[0])):
            angle_str = str(float(angle)) if isinstance(angle, (int, float)) else str(angle)
            count = angle_data.get('count', 0) if isinstance(angle_data, dict) else angle_data
            description = angle_data.get('description', angle_descriptions.get(angle_str, 'Custom angle')) if isinstance(angle_data, dict) else angle_descriptions.get(angle_str, 'Custom angle')
            paper += f"| {angle_str}° | {description} | {count} |\n"
    
    # Golden ratio analysis
    paper += f"""

### 3.4 Golden Ratio Analysis
- **Candidates Found:** {summary.get('golden_ratio_candidates', 'N/A')}

The golden ratio (φ ≈ 1.618034) appears in numerous natural and geometric contexts. 
This analysis searches for distance and angle ratios that approximate φ within a 
tolerance of 0.001.

## 4. Discussion

### 4.1 Geometric Significance
The detected special angles correspond to fundamental polyhedra:
- **36° and 72°**: Associated with pentagonal symmetry (dodecahedron, icosahedron)
- **60° and 120°**: Hexagonal symmetry (hexagon tessellations)
- **90°**: Cubic and octahedral symmetry

### 4.2 Symmetry Analysis
The rotation of cube B induces a discrete rotational symmetry group. The special 
angles detected align with known Platonic and Archimedean solid symmetries.

### 4.3 Implications
These findings suggest:
1. Rotational configurations produce predictable geometric patterns
2. Special angles emerge naturally from cubic geometry
3. Distance distributions follow mathematical regularities
4. Potential connections to crystallographic space groups

### 4.4 Practical Applications

**Materials Science & Crystallography:**
- Crystal lattice structure analysis and prediction
- Understanding molecular packing in protein crystals
- Design of metamaterials with specific optical/electromagnetic properties
- Quasicrystal formation and aperiodic tilings

**Engineering & Architecture:**
- Structural optimization for load distribution
- Space-efficient packing in 3D manufacturing
- Geodesic dome and tensegrity structure design
- Minimal surface architectures

**Computer Graphics & Visualization:**
- Procedural geometry generation
- Symmetry-based texture mapping
- 3D modeling and animation rigging
- Virtual reality environment construction

**Physics & Chemistry:**
- Molecular orbital symmetry analysis
- Phonon dispersion in solid-state physics
- Electron density distributions
- Quantum mechanical system modeling

**Mathematics & Computer Science:**
- Graph theory and network optimization
- Computational geometry algorithms
- Group theory and symmetry operations
- Discrete optimization problems

## 5. Conclusions

This computational analysis reveals structured geometric relationships in rotated 
cube configurations. The presence of special angles and golden ratio candidates 
indicates deep mathematical structure underlying simple geometric transformations.

### Future Work
- Extended parameter sweeps across rotation ranges
- Multi-axis rotation analysis
- Comparison with known geometric theorems
- Application to crystallography and materials science

## 6. Data Availability

Full discovery data available as JSON:
- Discovery ID: `{disc_id}`
- Download endpoint: `/api/discoveries/download/{disc_id}`

## 7. Computational Details

**Software:** Orion Octave Cube Analysis System  
**Language:** Python 3.11+  
**Libraries:** NumPy, SciPy, Matplotlib, Scikit-learn

---

**Citation:**
```
Orion Octave Cube Discovery {disc_id} ({timestamp[:10]})
Geometric Analysis Report
Generated via autonomous discovery system
```

**License:** Research and Educational Use

---

*This paper was automatically generated from computational discovery data.*
"""
    
    return paper


def _discover_angle(angle, discovery_type):
    """Helper function to discover a single angle configuration."""
    start_time = time.time()
    try:
        daemon_monitor.heartbeat()
        
        results = run_analysis(
            side=2.0,
            angle=angle,
            max_distance_pairs=10000,
            max_direction_pairs=5000,
            verbose=False
        )
        
        # Enhanced analysis
        summary = {
            'unique_points': results['point_counts']['unique_points'],
            'golden_ratio_candidates': results['golden_ratio']['candidate_count'],
            'unique_distances': results['distances']['distinct_count'],
            'special_angles': results['special_angles'],
            'max_distance': results['distances']['statistics']['max'],
            'min_distance': results['distances']['statistics']['min'],
            'distance_mean': results['distances']['statistics']['mean'],
            'total_angle_pairs': sum(data.get('count', 0) for data in results['special_angles'].values()) if results['special_angles'] else 0,
            'edge_face_intersections': results['point_counts']['edge_face_intersections'],
            'edge_edge_intersections': results['point_counts']['edge_edge_intersections']
        }
        
        # Check for exceptional patterns
        if results['golden_ratio']['candidate_count'] > 2:
            summary['exceptional'] = 'Multiple golden ratio candidates'
        if results['point_counts']['unique_points'] > 40:
            summary['exceptional'] = 'High complexity lattice'
        # Check for strong icosahedral symmetry
        for angle_key, angle_data in results['special_angles'].items():
            if isinstance(angle_data, dict) and angle_data.get('count', 0) > 100:
                if str(float(angle_key)) in ['36.0', '72.0']:
                    summary['exceptional'] = 'Strong icosahedral symmetry'
                    break
        
        discovery_data = {
            'angle': angle,
            'summary': summary,
            'full_results': results
        }
        
        # Generate descriptive title - do it before saving
        temp_discovery = {'type': discovery_type, 'data': discovery_data}
        title = _generate_discovery_title(temp_discovery)
        discovery_data['title'] = title
        
        discovery_id = discovery_manager.save_discovery(discovery_data, discovery_type)
        
        daemon_status['last_discovery'] = datetime.utcnow().isoformat()
        daemon_status['discoveries_today'] += 1
        daemon_status['total_discoveries'] += 1
        
        # Record success in monitor
        duration = time.time() - start_time
        daemon_monitor.record_discovery(discovery_id, duration, success=True)
        daemon_monitor.update_resources()
        
        # Record in Prometheus metrics
        prometheus_metrics.record_discovery(duration)
        
        exceptional = summary.get('exceptional', '')
        log_msg = f"Saved discovery: {discovery_id} (angle={angle}°"
        if exceptional:
            log_msg += f", {exceptional}"
        log_msg += ")"
        logger.info(log_msg)
        
    except Exception as e:
        duration = time.time() - start_time
        daemon_monitor.record_error(str(e), 'discovery_error')
        logger.error(f"Error in discovery for angle {angle}: {e}")


def _discover_with_params(size, angle, discovery_type):
    """Helper function to discover with varied parameters."""
    try:
        results = run_analysis(
            side=size,
            angle=angle,
            max_distance_pairs=10000,
            max_direction_pairs=5000,
            verbose=False
        )
        
        summary = {
            'cube_size': size,
            'angle': angle,
            'unique_points': results['point_counts']['unique_points'],
            'golden_ratio_candidates': results['golden_ratio']['candidate_count'],
            'unique_distances': results['distances']['distinct_count'],
            'special_angles': results['special_angles'],
            'scaling_factor': size / 2.0,  # Relative to standard size
            'max_distance': results['distances']['statistics']['max'],
            'min_distance': results['distances']['statistics']['min'],
            'distance_mean': results['distances']['statistics']['mean'],
            'edge_face_intersections': results['point_counts']['edge_face_intersections'],
            'edge_edge_intersections': results['point_counts']['edge_edge_intersections']
        }
        
        discovery_data = {
            'angle': angle,
            'size': size,
            'summary': summary,
            'full_results': results
        }
        
        # Generate descriptive title
        temp_discovery = {'type': discovery_type, 'data': discovery_data}
        title = _generate_discovery_title(temp_discovery)
        discovery_data['title'] = title
        
        discovery_id = discovery_manager.save_discovery(discovery_data, discovery_type)
        
        daemon_status['last_discovery'] = datetime.utcnow().isoformat()
        daemon_status['discoveries_today'] += 1
        daemon_status['total_discoveries'] += 1
        
        logger.info(f"Saved discovery: {discovery_id} (size={size}, angle={angle}°)")
        
    except Exception as e:
        logger.error(f"Error in parameter discovery (size={size}, angle={angle}): {e}")


def start_autonomous_daemon():
    """Start the autonomous daemon in a background thread."""
    try:
        if os.environ.get('ENABLE_AUTONOMOUS', 'true').lower() == 'true':
            logger.info("ENABLE_AUTONOMOUS=true, starting daemon thread...")
            daemon_thread = threading.Thread(target=run_autonomous_daemon, daemon=True)
            daemon_thread.start()
            logger.info("✓ Autonomous daemon thread started successfully")
            
            # Start ML background analysis if enabled
            if os.environ.get('ENABLE_ML_DISCOVERY', 'true').lower() == 'true':
                ml_integration.start_background_analysis(interval=7200)  # Every 2 hours
                logger.info("✓ ML background analysis started")
            
            # Start Prometheus metrics updater
            start_metrics_updater(discovery_manager, daemon_monitor, analysis_cache, interval=30)
            logger.info("✓ Prometheus metrics updater started")
        else:
            logger.info("Autonomous daemon disabled by configuration (ENABLE_AUTONOMOUS=false)")
    except Exception as e:
        logger.error(f"Failed to start autonomous daemon: {e}", exc_info=True)


# Start daemon when module is imported (works with gunicorn)
start_autonomous_daemon()


# ============================================================================
# FLASK ROUTES
# ============================================================================

@app.route('/')
def index():
    """Main dashboard page."""
    return render_template('index.html')


@app.route('/admin')
def admin():
    """Admin panel for system maintenance."""
    return render_template('admin.html')


@app.route('/health')
def health():
    """Lightweight health endpoint for load balancers and platform health checks."""
    # Keep this lightweight: return quickly without heavy computation
    try:
        return jsonify({'success': True, 'status': 'ok'}), 200
    except Exception:
        return jsonify({'success': False}), 500


@app.route('/healthz')
def healthz():
    """Compatibility alias for health checks."""
    return health()


@app.route('/discoveries')
def discoveries():
    """Autonomous discoveries dashboard page."""
    return render_template('discoveries.html')


@app.route('/api/analyze', methods=['POST'])
@rate_limit('analyze')
@validate_request(max_payload_kb=50)
def analyze():
    """Run geometric analysis with provided parameters."""
    try:
        # Parse JSON with error handling
        try:
            data = request.get_json()
        except Exception as json_error:
            return jsonify({
                'error': 'Invalid JSON format',
                'success': False
            }), 400
        
        if data is None:
            return jsonify({
                'error': 'Empty request body or invalid content type',
                'success': False
            }), 400
        
        # Extract and validate parameter types
        try:
            side = float(data.get('side', Config.DEFAULT_SIDE))
            angle = float(data.get('angle', Config.DEFAULT_ANGLE))
            max_distance_pairs = int(data.get('max_distance_pairs', Config.DEFAULT_DISTANCE_PAIRS))
            max_direction_pairs = int(data.get('max_direction_pairs', Config.DEFAULT_DIRECTION_PAIRS))
        except (ValueError, TypeError) as e:
            return jsonify({
                'error': f'Invalid parameter type: {str(e)}',
                'success': False
            }), 400
        
        # Validate input ranges with config-based limits
        if not (Config.MIN_SIDE_LENGTH < side <= Config.MAX_SIDE_LENGTH):
            return jsonify({
                'error': f'Side length must be between {Config.MIN_SIDE_LENGTH} and {Config.MAX_SIDE_LENGTH}',
                'success': False
            }), 400
        if not (Config.MIN_ANGLE <= angle <= Config.MAX_ANGLE):
            return jsonify({
                'error': f'Angle must be between {Config.MIN_ANGLE} and {Config.MAX_ANGLE} degrees',
                'success': False
            }), 400
        if max_distance_pairs <= 0 or max_distance_pairs > Config.MAX_DISTANCE_PAIRS:
            return jsonify({
                'error': f'max_distance_pairs must be between 1 and {Config.MAX_DISTANCE_PAIRS}',
                'success': False
            }), 400
        if max_direction_pairs <= 0 or max_direction_pairs > Config.MAX_DIRECTION_PAIRS:
            return jsonify({
                'error': f'max_direction_pairs must be between 1 and {Config.MAX_DIRECTION_PAIRS}',
                'success': False
            }), 400
        
        # Generate cache key
        cache_key = f"{side}_{angle}_{max_distance_pairs}_{max_direction_pairs}"
        
        # Check cache if enabled
        if Config.CACHE_ENABLED and cache_key in analysis_cache:
            logger.info(f"Cache hit for {cache_key}")
            results = analysis_cache[cache_key]
            cached = True
        else:
            # Run analysis
            logger.info(f"Running analysis: side={side}, angle={angle}")
            results = run_analysis(
                side=side,
                angle=angle,
                max_distance_pairs=max_distance_pairs,
                max_direction_pairs=max_direction_pairs,
                verbose=False
            )
            
            # Store in cache if enabled
            if Config.CACHE_ENABLED:
                analysis_cache[cache_key] = results
            cached = False
        
        # Return comprehensive summary
        return jsonify({
            'success': True,
            'cache_key': cache_key,
            'cached': cached,
            'summary': {
                'configuration': results['configuration'],
                'point_counts': results['point_counts'],
                'distance_stats': results['distances']['statistics'],
                'golden_ratio': results['golden_ratio'],
                'direction_count': results['directions']['unique_count'],
                'angle_count': results['angles']['distinct_count'],
                'special_angles': results['special_angles'],
                'icosahedral_check': results['icosahedral_check']
            }
        })
        
    except ValueError as e:
        logger.error(f'ValueError: {str(e)}')
        return jsonify({
            'error': f'Invalid input value: {str(e)}',
            'success': False
        }), 400
    except KeyError as e:
        logger.error(f'KeyError: {str(e)}')
        return jsonify({
            'error': f'Missing required data: {str(e)}',
            'success': False
        }), 400
    except Exception as e:
        logger.error(f'Unexpected error: {str(e)}', exc_info=True)
        return jsonify({
            'error': 'Internal server error',
            'success': False,
            'details': str(e) if Config.DEBUG else None
        }), 500


@app.route('/api/plot/<plot_type>/<cache_key>')
def generate_plot(plot_type, cache_key):
    """Generate plots on demand."""
    try:
        if cache_key not in analysis_cache:
            return jsonify({'error': 'Analysis not found. Please run analysis first.'}), 404
        
        results = analysis_cache[cache_key]
        
        if plot_type == '3d':
            img = create_3d_plot(results)
        elif plot_type == 'distances':
            img = create_distance_plot(results)
        elif plot_type == 'angles':
            img = create_angle_plot(results)
        elif plot_type == 'summary':
            img = create_summary_plot(results)
        else:
            return jsonify({'error': f'Invalid plot type: {plot_type}. Valid types: 3d, distances, angles, summary'}), 400
        
        return send_file(img, mimetype='image/png')
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/download/<cache_key>')
@rate_limit('download')
def download_results(cache_key):
    """Download results as JSON."""
    try:
        if cache_key not in analysis_cache:
            return jsonify({'error': 'Analysis not found'}), 404
        
        results = analysis_cache[cache_key]
        
        # Create JSON file in memory
        json_str = json.dumps(results, indent=2)
        json_bytes = io.BytesIO(json_str.encode('utf-8'))
        
        config = results['configuration']
        filename = f"orion_octave_{config['rotation_angle_degrees']}deg.json"
        
        return send_file(
            json_bytes,
            mimetype='application/json',
            as_attachment=True,
            download_name=filename
        )
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


def create_3d_plot(results):
    """Create 3D scatter plot of interference points."""
    points = np.array(results['points'])
    
    fig = plt.figure(figsize=(10, 8))
    ax = fig.add_subplot(111, projection='3d')
    
    ax.scatter(points[:, 0], points[:, 1], points[:, 2], 
              c='#2E86AB', marker='o', s=50, alpha=0.6, edgecolors='black', linewidth=0.5)
    
    ax.set_xlabel('X', fontsize=11, fontweight='bold')
    ax.set_ylabel('Y', fontsize=11, fontweight='bold')
    ax.set_zlabel('Z', fontsize=11, fontweight='bold')
    
    config = results['configuration']
    ax.set_title(f"Interference Lattice - {config['rotation_angle_degrees']}° Rotation\n"
                f"{results['point_counts']['unique_points']} Unique Points",
                fontsize=12, fontweight='bold', pad=20)
    
    ax.grid(True, alpha=0.3)
    ax.view_init(elev=20, azim=45)
    
    # Equal aspect ratio
    max_range = np.array([points[:, 0].max() - points[:, 0].min(),
                         points[:, 1].max() - points[:, 1].min(),
                         points[:, 2].max() - points[:, 2].min()]).max() / 2.0
    
    mid_x = (points[:, 0].max() + points[:, 0].min()) * 0.5
    mid_y = (points[:, 1].max() + points[:, 1].min()) * 0.5
    mid_z = (points[:, 2].max() + points[:, 2].min()) * 0.5
    
    ax.set_xlim(mid_x - max_range, mid_x + max_range)
    ax.set_ylim(mid_y - max_range, mid_y + max_range)
    ax.set_zlim(mid_z - max_range, mid_z + max_range)
    
    plt.tight_layout()
    
    # Save to bytes
    img = io.BytesIO()
    plt.savefig(img, format='png', dpi=150, bbox_inches='tight')
    img.seek(0)
    plt.close()
    
    return img


def create_distance_plot(results):
    """Create distance spectrum plot."""
    spectrum = results['distances']['spectrum']
    distances = sorted([float(k) for k in spectrum.keys()])
    counts = [spectrum[str(d)] for d in distances]
    
    fig, ax = plt.subplots(figsize=(12, 6))
    
    bars = ax.bar(distances, counts, width=0.05, alpha=0.8, 
                  color='#A23B72', edgecolor='black', linewidth=0.8)
    
    ax.set_xlabel('Distance', fontsize=12, fontweight='bold')
    ax.set_ylabel('Frequency', fontsize=12, fontweight='bold')
    ax.set_title('Distance Spectrum Distribution', fontsize=14, fontweight='bold', pad=15)
    ax.grid(True, alpha=0.3, axis='y', linestyle='--')
    
    # Highlight golden ratio candidates
    if results['golden_ratio']['candidate_count'] > 0:
        for a, b, ratio in results['golden_ratio']['candidates'][:5]:
            ax.axvline(a, color='gold', linestyle='--', linewidth=2, alpha=0.7, label=f'φ: {a:.3f}')
            ax.axvline(b, color='orange', linestyle='--', linewidth=2, alpha=0.7)
        ax.legend(loc='upper right', fontsize=10)
    
    plt.tight_layout()
    
    img = io.BytesIO()
    plt.savefig(img, format='png', dpi=150, bbox_inches='tight')
    img.seek(0)
    plt.close()
    
    return img


def create_angle_plot(results):
    """Create angle distribution plot."""
    spectrum = results['angles']['spectrum']
    angles = sorted([float(k) for k in spectrum.keys()])[:500]
    counts = [spectrum[str(a)] for a in angles]
    
    fig, ax = plt.subplots(figsize=(14, 6))
    
    ax.scatter(angles, counts, alpha=0.6, color='#F18F01', s=30, edgecolors='black', linewidth=0.5)
    
    ax.set_xlabel('Angle (degrees)', fontsize=12, fontweight='bold')
    ax.set_ylabel('Frequency', fontsize=12, fontweight='bold')
    ax.set_title('Angle Distribution Between Directions', fontsize=14, fontweight='bold', pad=15)
    ax.grid(True, alpha=0.3, linestyle='--')
    
    # Mark special angles
    special_angles = results.get('special_angles', {})
    colors = ['#E63946', '#457B9D', '#2A9D8F', '#E9C46A', '#9D4EDD']
    
    for i, (angle, data) in enumerate(sorted(special_angles.items(), key=lambda x: float(x[0]))):
        if data['count'] > 0:
            color = colors[i % len(colors)]
            ax.axvline(float(angle), color=color, linestyle='--', linewidth=2.5, alpha=0.8,
                      label=f"{angle}° ({data['description']}): {data['count']}")
    
    if any(data['count'] > 0 for data in special_angles.values()):
        ax.legend(fontsize=10, loc='upper right', framealpha=0.9)
    
    plt.tight_layout()
    
    img = io.BytesIO()
    plt.savefig(img, format='png', dpi=150, bbox_inches='tight')
    img.seek(0)
    plt.close()
    
    return img


def create_summary_plot(results):
    """Create comprehensive summary visualization."""
    fig = plt.figure(figsize=(16, 10))
    
    # 1. 3D scatter plot
    ax1 = fig.add_subplot(221, projection='3d')
    points = np.array(results['points'])
    ax1.scatter(points[:, 0], points[:, 1], points[:, 2], 
               c='#2E86AB', marker='o', s=30, alpha=0.6)
    ax1.set_title('3D Interference Lattice', fontweight='bold', fontsize=11)
    ax1.set_xlabel('X', fontsize=9)
    ax1.set_ylabel('Y', fontsize=9)
    ax1.set_zlabel('Z', fontsize=9)
    ax1.view_init(elev=20, azim=45)
    
    # 2. Distance spectrum
    ax2 = fig.add_subplot(222)
    spectrum = results['distances']['spectrum']
    distances = sorted([float(k) for k in spectrum.keys()])
    counts = [spectrum[str(d)] for d in distances]
    ax2.bar(distances, counts, width=0.05, alpha=0.8, color='#A23B72')
    ax2.set_title('Distance Spectrum', fontweight='bold', fontsize=11)
    ax2.set_xlabel('Distance', fontsize=9)
    ax2.set_ylabel('Frequency', fontsize=9)
    ax2.grid(True, alpha=0.3, axis='y')
    
    # 3. Angle distribution
    ax3 = fig.add_subplot(223)
    angle_spectrum = results['angles']['spectrum']
    angles = sorted([float(k) for k in list(angle_spectrum.keys())[:300]])
    angle_counts = [angle_spectrum[str(a)] for a in angles]
    ax3.scatter(angles, angle_counts, alpha=0.5, color='#F18F01', s=20)
    ax3.set_title('Angle Distribution', fontweight='bold', fontsize=11)
    ax3.set_xlabel('Angle (degrees)', fontsize=9)
    ax3.set_ylabel('Frequency', fontsize=9)
    ax3.grid(True, alpha=0.3)
    
    # 4. Summary statistics
    ax4 = fig.add_subplot(224)
    ax4.axis('off')
    
    config = results['configuration']
    counts = results['point_counts']
    stats = results['distances']['statistics']
    
    summary_text = f"""
CONFIGURATION
━━━━━━━━━━━━━━━━━━━━━━━━━━━
Side Length: {config['side_length']}
Rotation Angle: {config['rotation_angle_degrees']}°

POINT COUNTS
━━━━━━━━━━━━━━━━━━━━━━━━━━━
Vertices A: {counts['vertices_A']}
Vertices B: {counts['vertices_B']}
Edge-Face Intersections: {counts['edge_face_intersections']}
Edge-Edge Intersections: {counts['edge_edge_intersections']}
Total Unique Points: {counts['unique_points']}

DISTANCE STATISTICS
━━━━━━━━━━━━━━━━━━━━━━━━━━━
Min: {stats['min']:.4f}
Max: {stats['max']:.4f}
Mean: {stats['mean']:.4f}
Median: {stats['median']:.4f}
Std Dev: {stats['std']:.4f}

GOLDEN RATIO ANALYSIS
━━━━━━━━━━━━━━━━━━━━━━━━━━━
φ ≈ {results['golden_ratio']['phi_value']:.6f}
Candidate Pairs: {results['golden_ratio']['candidate_count']}

SPECIAL ANGLES
━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
    
    for angle, data in sorted(results.get('special_angles', {}).items(), key=lambda x: float(x[0])):
        if data['count'] > 0:
            summary_text += f"{angle}°: {data['count']} occurrences\n"
    
    ico_check = results.get('icosahedral_check', {})
    summary_text += f"\nICOSAHEDRAL CHECK\n"
    summary_text += f"━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
    summary_text += f"Match Quality: {ico_check.get('match_quality', 'N/A').upper()}\n"
    if ico_check.get('angle_degrees') is not None:
        summary_text += f"Angular Error: {ico_check['angle_degrees']:.2f}°\n"
    
    ax4.text(0.05, 0.95, summary_text, transform=ax4.transAxes,
            fontsize=9, verticalalignment='top', fontfamily='monospace',
            bbox=dict(boxstyle='round', facecolor='#F4F1DE', alpha=0.8))
    
    fig.suptitle(f"Orion Octave Cubes - Complete Analysis Summary", 
                fontsize=16, fontweight='bold', y=0.98)
    
    plt.tight_layout(rect=[0, 0, 1, 0.96])
    
    img = io.BytesIO()
    plt.savefig(img, format='png', dpi=150, bbox_inches='tight')
    img.seek(0)
    plt.close()
    
    return img


# ============================================================================
# AUTONOMOUS DISCOVERY API ENDPOINTS
# ============================================================================

@app.route('/api/discoveries/status')
def discovery_status():
    """Get autonomous daemon status."""
    try:
        stats = discovery_manager.get_stats()
        daemon_status['total_discoveries'] = stats.get('total_discoveries', 0)
        
        # Count today's discoveries
        today = datetime.utcnow().strftime('%Y-%m-%d')
        date_counts = stats.get('discoveries_by_date', {})
        daemon_status['discoveries_today'] = date_counts.get(today, 0)
        
        # Get latest discovery info
        latest = stats.get('latest_discovery')
        if latest:
            daemon_status['last_discovery'] = latest.get('timestamp')
        
        # Add monitor status with fallback
        try:
            monitor_status = daemon_monitor.get_status()
        except Exception as monitor_error:
            logger.warning(f"Could not get monitor status: {monitor_error}")
            monitor_status = {
                'is_running': False,
                'health_score': 0,
                'heartbeat_healthy': False,
                'uptime_seconds': None,
                'statistics': {
                    'total_discoveries': 0,
                    'total_errors': 0,
                    'success_rate': 0
                }
            }
        
        return jsonify({
            'success': True,
            'status': daemon_status,
            'health': monitor_status
        })
    except Exception as e:
        logger.error(f"Error getting discovery status: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e),
            'status': daemon_status,
            'health': {
                'is_running': False,
                'health_score': 0,
                'heartbeat_healthy': False
            }
        }), 500


@app.route('/api/daemon/health')
def daemon_health():
    """Get detailed daemon health information."""
    try:
        health = daemon_monitor.get_status()
        return jsonify({
            'success': True,
            'health': health
        })
    except Exception as e:
        logger.error(f"Error getting daemon health: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/daemon/metrics')
def daemon_metrics():
    """Get daemon performance metrics."""
    try:
        metrics = daemon_monitor.get_metrics()
        return jsonify({
            'success': True,
            'metrics': metrics
        })
    except Exception as e:
        logger.error(f"Error getting daemon metrics: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/discoveries/latest')
def get_latest_discoveries():
    """Get latest discoveries."""
    try:
        count = int(request.args.get('count', 10))
        discoveries = discovery_manager.get_latest(count)
        return jsonify({
            'success': True,
            'count': len(discoveries),
            'discoveries': discoveries
        })
    except Exception as e:
        logger.error(f"Error getting latest discoveries: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/discoveries/all')
def get_all_discoveries():
    """Get all discoveries with pagination."""
    try:
        limit = int(request.args.get('limit', 50))
        offset = int(request.args.get('offset', 0))
        result = discovery_manager.get_all(limit, offset)
        return jsonify({
            'success': True,
            **result
        })
    except Exception as e:
        logger.error(f"Error getting all discoveries: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/discoveries/<discovery_id>')
def get_discovery(discovery_id):
    """Get a specific discovery by ID."""
    try:
        discovery = discovery_manager.get_by_id(discovery_id)
        if discovery:
            return jsonify({
                'success': True,
                'discovery': discovery
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Discovery not found'
            }), 404
    except Exception as e:
        logger.error(f"Error getting discovery {discovery_id}: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/discoveries/stats')
def get_discovery_stats():
    """Get discovery statistics."""
    try:
        stats = discovery_manager.get_stats()
        return jsonify({
            'success': True,
            'stats': stats
        })
    except Exception as e:
        logger.error(f"Error getting discovery stats: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/discoveries/search')
@rate_limit('search')
def search_discoveries():
    """Search discoveries with advanced filtering."""
    try:
        query = request.args.get('q', '')
        discovery_type = request.args.get('type', '')
        date = request.args.get('date', '')
        
        results = discovery_manager.search(query, discovery_type, date)
        return jsonify({
            'success': True,
            'count': len(results),
            'discoveries': results
        })
    except Exception as e:
        logger.error(f"Error searching discoveries: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/daemon/trigger', methods=['POST'])
@rate_limit('analyze')
def trigger_discovery():
    """Manually trigger a single discovery (for testing/debugging)."""
    try:
        # Get angle from request or use default
        data = request.get_json() or {}
        angle = float(data.get('angle', 45.0))
        
        logger.info(f"Manual discovery trigger requested for angle={angle}°")
        
        # Run discovery in background thread
        def run_manual_discovery():
            try:
                logger.info(f"Running manual discovery at {angle}°...")
                _discover_angle(angle, 'manual_trigger')
                logger.info(f"Manual discovery at {angle}° completed")
            except Exception as e:
                logger.error(f"Manual discovery failed: {e}", exc_info=True)
        
        discovery_thread = threading.Thread(target=run_manual_discovery, daemon=True)
        discovery_thread.start()
        
        return jsonify({
            'success': True,
            'message': f'Discovery triggered for angle {angle}°',
            'note': 'Check /api/discoveries/latest in a few seconds'
        })
    except Exception as e:
        logger.error(f"Error triggering discovery: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/daemon/start', methods=['POST'])
def start_daemon():
    """Manually start the autonomous daemon (if not running)."""
    global daemon_status
    
    try:
        if daemon_status['running']:
            return jsonify({
                'success': False,
                'error': 'Daemon already running',
                'status': daemon_status
            }), 400
        
        logger.info("Manual daemon start requested...")
        daemon_thread = threading.Thread(target=run_autonomous_daemon, daemon=True)
        daemon_thread.start()
        
        return jsonify({
            'success': True,
            'message': 'Daemon started',
            'note': 'Check /api/daemon/health for status'
        })
    except Exception as e:
        logger.error(f"Error starting daemon: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/discoveries/regenerate-titles', methods=['POST'])
def regenerate_all_titles():
    """Regenerate titles for all existing discoveries (admin endpoint)."""
    try:
        all_discoveries = discovery_manager.get_all(limit=10000)
        updated_count = 0
        
        for disc_summary in all_discoveries.get('discoveries', []):
            disc = discovery_manager.get_by_id(disc_summary['id'])
            if disc and 'data' in disc:
                # Generate new title
                title = _generate_discovery_title(disc)
                disc['data']['title'] = title
                
                # Re-save the discovery file
                date = disc.get('date', datetime.utcnow().strftime('%Y-%m-%d'))
                date_dir = discovery_manager.base_dir / date
                json_file = date_dir / f"{disc['id']}.json"
                
                if json_file.exists():
                    discovery_manager._save_json(json_file, disc)
                    updated_count += 1
        
        logger.info(f"Regenerated titles for {updated_count} discoveries")
        return jsonify({
            'success': True,
            'updated': updated_count,
            'message': f'Successfully regenerated {updated_count} titles'
        })
    except Exception as e:
        logger.error(f"Error regenerating titles: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/discoveries/exceptional')
def get_exceptional_discoveries():
    """Get discoveries with exceptional patterns (golden ratio, high complexity, etc.)."""
    try:
        # Get all discoveries
        all_discoveries = discovery_manager.get_all(limit=1000)
        exceptional = []
        
        for disc in all_discoveries.get('discoveries', []):
            disc_data = discovery_manager.get_by_id(disc['id'])
            if disc_data and 'data' in disc_data:
                summary = disc_data['data'].get('summary', {})
                # Check for exceptional markers
                if summary.get('exceptional') or \
                   summary.get('golden_ratio_candidates', 0) > 2 or \
                   summary.get('unique_points', 0) > 40:
                    exceptional.append(disc)
        
        return jsonify({
            'success': True,
            'count': len(exceptional),
            'discoveries': exceptional
        })
    except Exception as e:
        logger.error(f"Error getting exceptional discoveries: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


# ============================================================================
# MACHINE LEARNING API ENDPOINTS
# ============================================================================

@app.route('/api/ml/analyze', methods=['POST'])
@rate_limit('ml_analyze')
@validate_request(max_payload_kb=10)
def ml_analyze():
    """Run ML pattern analysis on discoveries."""
    try:
        min_discoveries = int(request.args.get('min_discoveries', 10))
        
        logger.info(f"Starting ML analysis (min_discoveries={min_discoveries})")
        result = ml_integration.analyze_discoveries(min_discoveries)
        
        if result is None:
            return jsonify({
                'success': False,
                'error': 'Insufficient discoveries for ML analysis'
            }), 400
        
        # Record ML analysis in metrics
        prometheus_metrics.record_ml_analysis()
        
        return jsonify({
            'success': True,
            'analysis': result
        })
    except Exception as e:
        logger.error(f"Error in ML analysis: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/ml/patterns')
def ml_patterns():
    """Get discovered ML patterns."""
    try:
        patterns = ml_integration.get_patterns()
        return jsonify({
            'success': True,
            'count': len(patterns),
            'patterns': patterns
        })
    except Exception as e:
        logger.error(f"Error getting ML patterns: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/ml/status')
def ml_status():
    """Get ML integration status."""
    try:
        last_analysis = ml_integration.get_last_analysis()
        return jsonify({
            'success': True,
            'is_running': ml_integration.is_running,
            'last_analysis': last_analysis
        })
    except Exception as e:
        logger.error(f"Error getting ML status: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/discoveries/by-type/<discovery_type>')
def get_discoveries_by_type(discovery_type):
    """Get discoveries filtered by type."""
    try:
        all_discoveries = discovery_manager.get_all(limit=1000)
        filtered = [d for d in all_discoveries.get('discoveries', []) 
                   if d.get('type') == discovery_type]
        
        return jsonify({
            'success': True,
            'type': discovery_type,
            'count': len(filtered),
            'discoveries': filtered
        })
    except Exception as e:
        logger.error(f"Error getting discoveries by type: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/discoveries/analysis-summary')
def get_analysis_summary():
    """Get aggregate analysis across all discoveries."""
    try:
        all_discoveries = discovery_manager.get_all(limit=1000)
        
        total_golden_ratio = 0
        max_unique_points = 0
        discovery_types = {}
        angle_distribution = {}
        
        for disc in all_discoveries.get('discoveries', []):
            disc_data = discovery_manager.get_by_id(disc['id'])
            if disc_data and 'data' in disc_data:
                summary = disc_data['data'].get('summary', {})
                
                # Aggregate metrics
                total_golden_ratio += summary.get('golden_ratio_candidates', 0)
                max_unique_points = max(max_unique_points, summary.get('unique_points', 0))
                
                # Count by type
                dtype = disc.get('type', 'unknown')
                discovery_types[dtype] = discovery_types.get(dtype, 0) + 1
                
                # Angle distribution
                angle = disc_data['data'].get('angle')
                if angle:
                    angle_key = str(int(angle))
                    angle_distribution[angle_key] = angle_distribution.get(angle_key, 0) + 1
        
        return jsonify({
            'success': True,
            'summary': {
                'total_discoveries': all_discoveries.get('total', 0),
                'total_golden_ratio_candidates': total_golden_ratio,
                'max_unique_points_found': max_unique_points,
                'discovery_types': discovery_types,
                'angle_distribution': angle_distribution,
                'most_tested_angle': max(angle_distribution.items(), key=lambda x: x[1])[0] if angle_distribution else None
            }
        })
    except Exception as e:
        logger.error(f"Error getting analysis summary: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/discoveries/download/<discovery_id>')
def download_discovery(discovery_id):
    """Download a discovery as JSON (no rate limit for downloads)."""
    try:
        discovery = discovery_manager.get_by_id(discovery_id)
        if not discovery:
            return jsonify({'error': 'Discovery not found'}), 404
        
        # Create JSON file in memory
        json_str = json.dumps(discovery, indent=2, default=str)
        json_bytes = io.BytesIO(json_str.encode('utf-8'))
        
        filename = f"discovery_{discovery_id}.json"
        
        return send_file(
            json_bytes,
            mimetype='application/json',
            as_attachment=True,
            download_name=filename
        )
    except Exception as e:
        logger.error(f"Error downloading discovery {discovery_id}: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/discoveries/<discovery_id>/paper')
def get_discovery_paper(discovery_id):
    """Generate and download research paper for a discovery (PDF format)."""
    try:
        discovery = discovery_manager.get_by_id(discovery_id)
        if not discovery:
            return jsonify({'error': 'Discovery not found'}), 404
        
        # Generate research paper markdown
        paper_markdown = _generate_research_paper(discovery)
        
        # Convert to PDF
        pdf_bytes = _convert_markdown_to_pdf(paper_markdown, discovery_id)
        
        pdf_buffer = io.BytesIO(pdf_bytes)
        pdf_buffer.seek(0)
        
        filename = f"research_paper_{discovery_id}.pdf"
        
        return send_file(
            pdf_buffer,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=filename
        )
    except Exception as e:
        logger.error(f"Error generating PDF paper for {discovery_id}: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@app.route('/api/discoveries/<discovery_id>/paper/markdown')
def get_discovery_paper_markdown(discovery_id):
    """Generate and download research paper for a discovery (Markdown format)."""
    try:
        discovery = discovery_manager.get_by_id(discovery_id)
        if not discovery:
            return jsonify({'error': 'Discovery not found'}), 404
        
        # Generate research paper
        paper = _generate_research_paper(discovery)
        paper_bytes = io.BytesIO(paper.encode('utf-8'))
        
        filename = f"research_paper_{discovery_id}.md"
        
        return send_file(
            paper_bytes,
            mimetype='text/markdown',
            as_attachment=True,
            download_name=filename
        )
    except Exception as e:
        logger.error(f"Error generating markdown paper for {discovery_id}: {e}")
        return jsonify({'error': str(e)}), 500


# ============================================================================
# MAIN APPLICATION ENTRY POINT
# ============================================================================

if __name__ == '__main__':
    print("=" * 70)
    print("Orion Octave Cubes - Web Application")
    print("=" * 70)
    
    if Config.DEBUG:
        print("\n⚠️  WARNING: Running in DEBUG mode")
        print("   For production, set FLASK_DEBUG=false")
    
    print(f"\nStarting Flask server...")
    print(f"  Mode: {'DEBUG' if Config.DEBUG else 'PRODUCTION'}")
    print(f"  Host: {Config.HOST}")
    print(f"  Port: {Config.PORT}")
    print(f"\nAccess the dashboard at: http://localhost:{Config.PORT}")
    print("\nPress Ctrl+C to stop the server")
    print("\nEnvironment Variables:")
    print(f"  FLASK_DEBUG={Config.DEBUG}")
    print(f"  FLASK_HOST={Config.HOST}")
    print(f"  FLASK_PORT={Config.PORT}")
    print("=" * 70)
    
    # Daemon already started at module import time
    
    app.run(debug=Config.DEBUG, host=Config.HOST, port=Config.PORT)
