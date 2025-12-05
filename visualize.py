#!/usr/bin/env python3
"""
Visualization script for Orion Octave Cubes results.

Requires: matplotlib
Install: pip install matplotlib

Usage:
    python visualize.py results.json
"""

import sys
import json
import argparse
from pathlib import Path

try:
    import matplotlib.pyplot as plt
    from mpl_toolkits.mplot3d import Axes3D
    import numpy as np
except ImportError:
    print("Error: matplotlib is required for visualization")
    print("Install with: pip install matplotlib")
    sys.exit(1)


def load_results(filename: str) -> dict:
    """Load results from JSON file."""
    with open(filename, 'r') as f:
        return json.load(f)


def plot_points_3d(results: dict, save_path: str = None):
    """Create 3D scatter plot of interference points."""
    points = np.array(results['points'])
    
    fig = plt.figure(figsize=(12, 10))
    ax = fig.add_subplot(111, projection='3d')
    
    # Plot points
    ax.scatter(points[:, 0], points[:, 1], points[:, 2], 
              c='blue', marker='o', s=50, alpha=0.6, label='Interference Points')
    
    # Add labels
    ax.set_xlabel('X', fontsize=12)
    ax.set_ylabel('Y', fontsize=12)
    ax.set_zlabel('Z', fontsize=12)
    
    config = results['configuration']
    title = f"Orion Octave Cubes - {config['rotation_angle_degrees']}° Rotation\n"
    title += f"{results['point_counts']['unique_points']} Unique Points"
    ax.set_title(title, fontsize=14, fontweight='bold')
    
    ax.legend()
    ax.grid(True, alpha=0.3)
    
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
    
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f"✓ 3D plot saved to: {save_path}")
    else:
        plt.show()
    
    plt.close()


def plot_distance_spectrum(results: dict, save_path: str = None):
    """Plot distance distribution histogram."""
    spectrum = results['distances']['spectrum']
    distances = [float(k) for k in spectrum.keys()]
    counts = list(spectrum.values())
    
    fig, ax = plt.subplots(figsize=(12, 6))
    
    ax.bar(distances, counts, width=0.05, alpha=0.7, color='steelblue', edgecolor='black')
    
    ax.set_xlabel('Distance', fontsize=12)
    ax.set_ylabel('Frequency', fontsize=12)
    ax.set_title('Distance Spectrum Distribution', fontsize=14, fontweight='bold')
    ax.grid(True, alpha=0.3, axis='y')
    
    # Mark golden ratio candidates if present
    if results['golden_ratio']['candidate_count'] > 0:
        for a, b, ratio in results['golden_ratio']['candidates']:
            ax.axvline(a, color='gold', linestyle='--', linewidth=2, alpha=0.6)
            ax.axvline(b, color='orange', linestyle='--', linewidth=2, alpha=0.6)
    
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f"✓ Distance spectrum saved to: {save_path}")
    else:
        plt.show()
    
    plt.close()


def plot_angle_distribution(results: dict, save_path: str = None):
    """Plot angle distribution."""
    spectrum = results['angles']['spectrum']
    angles = [float(k) for k in spectrum.keys()]
    counts = list(spectrum.values())
    
    fig, ax = plt.subplots(figsize=(14, 6))
    
    ax.scatter(angles, counts, alpha=0.5, color='darkgreen', s=20)
    
    ax.set_xlabel('Angle (degrees)', fontsize=12)
    ax.set_ylabel('Frequency', fontsize=12)
    ax.set_title('Angle Distribution Between Directions', fontsize=14, fontweight='bold')
    ax.grid(True, alpha=0.3)
    
    # Mark special angles
    special_angles = results.get('special_angles', {})
    colors = ['red', 'blue', 'green', 'orange', 'purple']
    
    for i, (angle, data) in enumerate(sorted(special_angles.items(), key=lambda x: float(x[0]))):
        if data['count'] > 0:
            color = colors[i % len(colors)]
            ax.axvline(float(angle), color=color, linestyle='--', linewidth=2, alpha=0.7,
                      label=f"{angle}° ({data['description']})")
    
    if special_angles:
        ax.legend(fontsize=10, loc='upper right')
    
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f"✓ Angle distribution saved to: {save_path}")
    else:
        plt.show()
    
    plt.close()


def create_summary_report(results: dict, save_path: str = None):
    """Create a multi-panel summary visualization."""
    fig = plt.figure(figsize=(16, 10))
    
    # 1. 3D scatter plot
    ax1 = fig.add_subplot(221, projection='3d')
    points = np.array(results['points'])
    ax1.scatter(points[:, 0], points[:, 1], points[:, 2], 
               c='blue', marker='o', s=30, alpha=0.6)
    ax1.set_title('3D Interference Lattice', fontweight='bold')
    ax1.set_xlabel('X')
    ax1.set_ylabel('Y')
    ax1.set_zlabel('Z')
    
    # 2. Distance spectrum
    ax2 = fig.add_subplot(222)
    spectrum = results['distances']['spectrum']
    distances = [float(k) for k in spectrum.keys()]
    counts = list(spectrum.values())
    ax2.bar(distances, counts, width=0.05, alpha=0.7, color='steelblue')
    ax2.set_title('Distance Spectrum', fontweight='bold')
    ax2.set_xlabel('Distance')
    ax2.set_ylabel('Frequency')
    ax2.grid(True, alpha=0.3, axis='y')
    
    # 3. Angle distribution (scatter)
    ax3 = fig.add_subplot(223)
    angle_spectrum = results['angles']['spectrum']
    angles = [float(k) for k in list(angle_spectrum.keys())[:200]]
    angle_counts = list(angle_spectrum.values())[:200]
    ax3.scatter(angles, angle_counts, alpha=0.5, color='darkgreen', s=20)
    ax3.set_title('Angle Distribution', fontweight='bold')
    ax3.set_xlabel('Angle (degrees)')
    ax3.set_ylabel('Frequency')
    ax3.grid(True, alpha=0.3)
    
    # 4. Summary statistics (text)
    ax4 = fig.add_subplot(224)
    ax4.axis('off')
    
    config = results['configuration']
    counts = results['point_counts']
    stats = results['distances']['statistics']
    
    summary_text = f"""
CONFIGURATION
━━━━━━━━━━━━━━━━━━━━━━━━━━━
Cube Side: {config['side_length']}
Rotation: {config['rotation_angle_degrees']}°

POINT COUNTS
━━━━━━━━━━━━━━━━━━━━━━━━━━━
Vertices A: {counts['vertices_A']}
Vertices B: {counts['vertices_B']}
Edge-Face: {counts['edge_face_intersections']}
Edge-Edge: {counts['edge_edge_intersections']}
Total Unique: {counts['unique_points']}

DISTANCE STATISTICS
━━━━━━━━━━━━━━━━━━━━━━━━━━━
Min: {stats['min']:.4f}
Max: {stats['max']:.4f}
Mean: {stats['mean']:.4f}
Median: {stats['median']:.4f}
Std Dev: {stats['std']:.4f}

GOLDEN RATIO
━━━━━━━━━━━━━━━━━━━━━━━━━━━
φ ≈ {results['golden_ratio']['phi_value']:.6f}
Candidates: {results['golden_ratio']['candidate_count']}

SPECIAL ANGLES
━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
    
    for angle, data in sorted(results.get('special_angles', {}).items(), key=lambda x: float(x[0])):
        if data['count'] > 0:
            summary_text += f"{angle}°: {data['count']} occurrences\n"
    
    ax4.text(0.1, 0.95, summary_text, transform=ax4.transAxes,
            fontsize=10, verticalalignment='top', fontfamily='monospace',
            bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.3))
    
    config = results['configuration']
    fig.suptitle(f"Orion Octave Cubes Analysis - {config['rotation_angle_degrees']}° Rotation", 
                fontsize=16, fontweight='bold')
    
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f"✓ Summary report saved to: {save_path}")
    else:
        plt.show()
    
    plt.close()


def main():
    parser = argparse.ArgumentParser(
        description='Visualize Orion Octave Cubes analysis results',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Show all visualizations interactively
  python visualize.py results.json
  
  # Save specific plots
  python visualize.py results.json --3d points_3d.png
  python visualize.py results.json --distances distances.png
  python visualize.py results.json --angles angles.png
  
  # Save complete summary
  python visualize.py results.json --summary summary.png
  
  # Save all plots
  python visualize.py results.json --all output_prefix
        """
    )
    
    parser.add_argument('input', type=str, help='Input JSON file from orion_octave_test.py')
    parser.add_argument('--3d', type=str, default=None, help='Save 3D plot to file')
    parser.add_argument('--distances', type=str, default=None, help='Save distance plot to file')
    parser.add_argument('--angles', type=str, default=None, help='Save angle plot to file')
    parser.add_argument('--summary', type=str, default=None, help='Save summary report to file')
    parser.add_argument('--all', type=str, default=None, help='Save all plots with this prefix')
    
    args = parser.parse_args()
    
    if not Path(args.input).exists():
        print(f"Error: File not found: {args.input}")
        sys.exit(1)
    
    print(f"Loading results from: {args.input}")
    results = load_results(args.input)
    
    if args.all:
        prefix = args.all
        plot_points_3d(results, f"{prefix}_3d.png")
        plot_distance_spectrum(results, f"{prefix}_distances.png")
        plot_angle_distribution(results, f"{prefix}_angles.png")
        create_summary_report(results, f"{prefix}_summary.png")
    else:
        if args.summary:
            create_summary_report(results, args.summary)
        else:
            if args.__dict__['3d']:
                plot_points_3d(results, args.__dict__['3d'])
            elif not any([args.distances, args.angles]):
                plot_points_3d(results)
            
            if args.distances:
                plot_distance_spectrum(results, args.distances)
            
            if args.angles:
                plot_angle_distribution(results, args.angles)
    
    print("\n✓ Visualization complete!")


if __name__ == '__main__':
    main()
