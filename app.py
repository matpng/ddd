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
import numpy as np
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D

# Import our modules
from orion_octave_test import main as run_analysis
from config import Config
from discovery_manager import DiscoveryManager
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

# Autonomous daemon status
daemon_status = {
    'running': False,
    'discoveries_today': 0,
    'last_discovery': None,
    'total_discoveries': 0,
    'started_at': None
}


@app.route('/')
def index():
    """Main dashboard page."""
    return render_template('index.html')


@app.route('/discoveries')
def discoveries():
    """Autonomous discoveries dashboard page."""
    return render_template('discoveries.html')


@app.route('/api/analyze', methods=['POST'])
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
        
        return jsonify({
            'success': True,
            'status': daemon_status
        })
    except Exception as e:
        logger.error(f"Error getting discovery status: {e}")
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
def search_discoveries():
    """Search discoveries."""
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


@app.route('/api/discoveries/download/<discovery_id>')
def download_discovery(discovery_id):
    """Download a discovery as JSON."""
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


# ============================================================================
# AUTONOMOUS DAEMON BACKGROUND THREAD
# ============================================================================

def run_autonomous_daemon():
    """Background thread that runs autonomous discoveries."""
    global daemon_status
    
    logger.info("Starting autonomous discovery daemon...")
    daemon_status['running'] = True
    daemon_status['started_at'] = datetime.utcnow().isoformat()
    
    # Simple discovery loop - runs angle sweep periodically
    discovery_interval = 3600  # 1 hour between discoveries
    
    while daemon_status['running']:
        try:
            logger.info("Running autonomous angle sweep discovery...")
            
            # Run a quick angle sweep (simplified version)
            angles_to_test = [15, 30, 45, 60, 75, 90, 105, 120, 135, 150, 165]
            
            for angle in angles_to_test:
                if not daemon_status['running']:
                    break
                
                try:
                    # Run analysis
                    results = run_analysis(
                        side=2.0,
                        rotation_angle_degrees=angle,
                        max_distance_pairs=10000,
                        max_direction_pairs=5000
                    )
                    
                    # Prepare discovery data
                    discovery_data = {
                        'angle': angle,
                        'summary': {
                            'unique_points': results['point_counts']['unique'],
                            'golden_ratio_present': results['golden_ratio']['present'],
                            'unique_distances': results['distances']['unique_count'],
                            'special_angles': results['special_angles']
                        },
                        'full_results': results
                    }
                    
                    # Save discovery
                    discovery_id = discovery_manager.save_discovery(
                        discovery_data,
                        'autonomous_angle_sweep'
                    )
                    
                    daemon_status['last_discovery'] = datetime.utcnow().isoformat()
                    daemon_status['discoveries_today'] += 1
                    daemon_status['total_discoveries'] += 1
                    
                    logger.info(f"Saved discovery: {discovery_id} (angle={angle}°)")
                    
                except Exception as e:
                    logger.error(f"Error in discovery for angle {angle}: {e}")
            
            logger.info(f"Autonomous discovery cycle complete. Sleeping for {discovery_interval}s...")
            
            # Sleep in small intervals to allow graceful shutdown
            for _ in range(discovery_interval):
                if not daemon_status['running']:
                    break
                time.sleep(1)
                
        except Exception as e:
            logger.error(f"Error in autonomous daemon: {e}", exc_info=True)
            time.sleep(60)  # Wait a minute before retrying
    
    logger.info("Autonomous discovery daemon stopped.")


def start_autonomous_daemon():
    """Start the autonomous daemon in a background thread."""
    if os.environ.get('ENABLE_AUTONOMOUS', 'true').lower() == 'true':
        daemon_thread = threading.Thread(target=run_autonomous_daemon, daemon=True)
        daemon_thread.start()
        logger.info("Autonomous daemon thread started")
    else:
        logger.info("Autonomous daemon disabled by configuration")


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
    
    # Start autonomous discovery daemon
    start_autonomous_daemon()
    
    app.run(debug=Config.DEBUG, host=Config.HOST, port=Config.PORT)
