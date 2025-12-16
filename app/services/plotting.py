"""
Plotting service for generating visualization of analysis results.
"""
import io
import numpy as np
import matplotlib
# Use Agg backend for non-interactive plotting
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D

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
    summary_text += f"\\nICOSAHEDRAL CHECK\\n"
    summary_text += f"━━━━━━━━━━━━━━━━━━━━━━━━━━━\\n"
    summary_text += f"Match Quality: {ico_check.get('match_quality', 'N/A').upper()}\\n"
    if ico_check.get('angle_degrees') is not None:
        summary_text += f"Angular Error: {ico_check['angle_degrees']:.2f}°\\n"
    
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
