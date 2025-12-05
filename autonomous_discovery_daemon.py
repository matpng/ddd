#!/usr/bin/env python3
"""
Autonomous Discovery Daemon
Continuously runs discovery tests, generates reports, and stores findings.
NO pre-populated data - all computations are performed in real-time.
"""

import time
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any
import numpy as np
from concurrent.futures import ProcessPoolExecutor, as_completed
import signal
import sys

from orion_octave_test import main as run_analysis
from advanced_discovery_engine import AdvancedDiscoveryEngine


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('autonomous_discovery.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class AutonomousDiscoveryDaemon:
    """
    Continuously running discovery system that:
    1. Scans parameter space systematically
    2. Performs real computations (no pre-populated data)
    3. Generates discovery reports
    4. Stores results in timestamped files
    """
    
    def __init__(self, output_dir: str = 'autonomous_discoveries'):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        self.discovery_engine = AdvancedDiscoveryEngine(verbose=True)
        self.running = True
        self.discoveries_count = 0
        
        # Set up graceful shutdown
        signal.signal(signal.SIGINT, self._shutdown_handler)
        signal.signal(signal.SIGTERM, self._shutdown_handler)
        
        logger.info("=" * 70)
        logger.info("Autonomous Discovery Daemon Started")
        logger.info("=" * 70)
        logger.info(f"Output directory: {self.output_dir}")
        logger.info("Mode: REAL-TIME COMPUTATION (no pre-populated data)")
        logger.info("Press Ctrl+C to stop")
        logger.info("=" * 70)
    
    def _shutdown_handler(self, signum, frame):
        """Handle graceful shutdown"""
        logger.info("\n" + "=" * 70)
        logger.info("Shutdown signal received. Finishing current task...")
        logger.info("=" * 70)
        self.running = False
    
    def _save_discovery(self, discovery: Dict[str, Any], category: str):
        """Save discovery to timestamped file"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = self.output_dir / f"{category}_{timestamp}.json"
        
        with open(filename, 'w') as f:
            json.dump(discovery, f, indent=2)
        
        logger.info(f"💾 Saved discovery: {filename}")
        self.discoveries_count += 1
    
    def _save_report(self, report: str, category: str):
        """Save markdown report"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = self.output_dir / f"{category}_report_{timestamp}.md"
        
        with open(filename, 'w') as f:
            f.write(report)
        
        logger.info(f"📄 Saved report: {filename}")
    
    # ==================== DISCOVERY MODES ====================
    
    def mode_angle_sweep(self, axis: str = 'z'):
        """
        Sweep through all angles from 0-180° in fine increments.
        Performs REAL computations for each angle.
        """
        logger.info(f"\n{'='*70}")
        logger.info(f"🔍 MODE: Fine Angle Sweep ({axis}-axis)")
        logger.info(f"{'='*70}")
        
        # Perform real computation
        results = self.discovery_engine.fine_angle_sweep(
            side=2.0,
            start=0,
            end=180,
            step=1.0,  # 1-degree increments
            axis=axis
        )
        
        # Analyze results for discoveries
        discoveries = self._analyze_sweep_results(results, axis)
        
        # Save all results
        discovery_data = {
            'timestamp': datetime.now().isoformat(),
            'mode': 'angle_sweep',
            'axis': axis,
            'total_angles': len(results),
            'computation': 'REAL-TIME (not pre-populated)',
            'results': results,
            'discoveries': discoveries
        }
        
        self._save_discovery(discovery_data, f'sweep_{axis}')
        
        # Generate report
        report = self._generate_sweep_report(results, discoveries, axis)
        self._save_report(report, f'sweep_{axis}')
        
        return discoveries
    
    def mode_multi_axis_scan(self):
        """
        Scan multiple rotation axes to discover axis-dependent patterns.
        All computations performed in real-time.
        """
        logger.info(f"\n{'='*70}")
        logger.info(f"🔍 MODE: Multi-Axis Scan")
        logger.info(f"{'='*70}")
        
        axes = ['x', 'y', 'z', 'arbitrary']
        all_results = {}
        
        for axis in axes:
            logger.info(f"\n📐 Scanning {axis}-axis...")
            results = self.discovery_engine.fine_angle_sweep(
                side=2.0,
                start=0,
                end=180,
                step=5.0,  # Coarser for multi-axis
                axis=axis
            )
            all_results[axis] = results
        
        # Cross-axis analysis
        cross_analysis = self._cross_axis_analysis(all_results)
        
        discovery_data = {
            'timestamp': datetime.now().isoformat(),
            'mode': 'multi_axis_scan',
            'axes_scanned': axes,
            'computation': 'REAL-TIME (not pre-populated)',
            'results': all_results,
            'cross_analysis': cross_analysis
        }
        
        self._save_discovery(discovery_data, 'multi_axis')
        
        report = self._generate_multi_axis_report(all_results, cross_analysis)
        self._save_report(report, 'multi_axis')
        
        return cross_analysis
    
    def mode_parameter_exploration(self):
        """
        Explore different cube sizes and angle combinations.
        Real computations for each configuration.
        """
        logger.info(f"\n{'='*70}")
        logger.info(f"🔍 MODE: Parameter Space Exploration")
        logger.info(f"{'='*70}")
        
        # Define parameter grid
        side_lengths = [1.0, 1.5, 2.0, 2.5, 3.0]
        angles = [30, 45, 60, 72, 90, 120, 144, 150]
        
        results = []
        total = len(side_lengths) * len(angles)
        current = 0
        
        for side in side_lengths:
            for angle in angles:
                current += 1
                logger.info(f"[{current}/{total}] Computing: side={side}, angle={angle}°")
                
                # REAL COMPUTATION - no pre-populated data
                result = run_analysis(
                    side=side,
                    angle=angle,
                    max_distance_pairs=20000,
                    max_direction_pairs=8000
                )
                
                results.append({
                    'side': side,
                    'angle': angle,
                    'phi_found': result.get('phi_relationship_found', False),
                    'unique_distances': result.get('num_unique_distances', 0),
                    'unique_directions': result.get('num_unique_directions', 0),
                    'golden_ratio_distances': result.get('golden_ratio_distances', []),
                    'golden_ratio_directions': result.get('golden_ratio_directions', [])
                })
        
        # Analyze patterns
        patterns = self._analyze_parameter_patterns(results)
        
        discovery_data = {
            'timestamp': datetime.now().isoformat(),
            'mode': 'parameter_exploration',
            'total_configurations': total,
            'computation': 'REAL-TIME (not pre-populated)',
            'results': results,
            'patterns': patterns
        }
        
        self._save_discovery(discovery_data, 'param_exploration')
        
        report = self._generate_parameter_report(results, patterns)
        self._save_report(report, 'param_exploration')
        
        return patterns
    
    def mode_critical_angle_analysis(self):
        """
        Deep analysis of specific critical angles.
        High-resolution real-time computation.
        """
        logger.info(f"\n{'='*70}")
        logger.info(f"🔍 MODE: Critical Angle Deep Analysis")
        logger.info(f"{'='*70}")
        
        # Critical angles to analyze
        critical_angles = [30, 45, 54.735, 60, 72, 90, 120, 144]
        
        detailed_results = {}
        
        for angle in critical_angles:
            logger.info(f"\n📊 Deep analysis: {angle}°")
            
            # High-resolution computation
            result = run_analysis(
                side=2.0,
                angle=angle,
                max_distance_pairs=50000,  # High resolution
                max_direction_pairs=25000
            )
            
            detailed_results[angle] = result
        
        # Compare critical angles
        comparison = self._compare_critical_angles(detailed_results)
        
        discovery_data = {
            'timestamp': datetime.now().isoformat(),
            'mode': 'critical_angle_analysis',
            'angles_analyzed': critical_angles,
            'resolution': 'HIGH (50k/25k pairs)',
            'computation': 'REAL-TIME (not pre-populated)',
            'results': detailed_results,
            'comparison': comparison
        }
        
        self._save_discovery(discovery_data, 'critical_angles')
        
        report = self._generate_critical_angle_report(detailed_results, comparison)
        self._save_report(report, 'critical_angles')
        
        return comparison
    
    # ==================== ANALYSIS HELPERS ====================
    
    def _analyze_sweep_results(self, results: Dict, axis: str) -> List[Dict]:
        """Analyze sweep results to find discoveries"""
        discoveries = []
        
        # Find phi occurrences
        phi_angles = [angle for angle, data in results.items() 
                     if data.get('phi_found', False)]
        
        if phi_angles:
            discoveries.append({
                'type': 'phi_occurrence_pattern',
                'axis': axis,
                'angles_with_phi': phi_angles,
                'count': len(phi_angles),
                'description': f'Found {len(phi_angles)} angles with golden ratio on {axis}-axis'
            })
        
        # Find symmetry patterns
        symmetries = self._detect_symmetries(results)
        if symmetries:
            discoveries.append({
                'type': 'symmetry_pattern',
                'axis': axis,
                'symmetries': symmetries,
                'description': f'Detected {len(symmetries)} symmetry patterns'
            })
        
        return discoveries
    
    def _detect_symmetries(self, results: Dict) -> List[Dict]:
        """Detect symmetric patterns in results"""
        symmetries = []
        angles = sorted(results.keys())
        
        # Check for mirror symmetry around 90°
        for angle in angles:
            if angle <= 90:
                mirror = 180 - angle
                if mirror in results:
                    data1 = results[angle]
                    data2 = results[mirror]
                    
                    if abs(data1.get('num_unique_distances', 0) - 
                          data2.get('num_unique_distances', 0)) < 5:
                        symmetries.append({
                            'angle_pair': [angle, mirror],
                            'type': 'mirror_90',
                            'metric': 'unique_distances'
                        })
        
        return symmetries
    
    def _cross_axis_analysis(self, all_results: Dict) -> Dict:
        """Analyze patterns across different rotation axes"""
        analysis = {
            'axis_specific_discoveries': [],
            'common_patterns': [],
            'axis_differences': []
        }
        
        # Find common phi angles across all axes
        phi_by_axis = {}
        for axis, results in all_results.items():
            phi_angles = [angle for angle, data in results.items() 
                         if data.get('phi_found', False)]
            phi_by_axis[axis] = set(phi_angles)
        
        # Common angles
        common_phi = set.intersection(*phi_by_axis.values()) if phi_by_axis else set()
        if common_phi:
            analysis['common_patterns'].append({
                'type': 'universal_phi_angles',
                'angles': sorted(list(common_phi)),
                'description': 'Angles showing phi across all axes'
            })
        
        # Axis-specific
        for axis, phi_set in phi_by_axis.items():
            unique_to_axis = phi_set - set.union(*(s for a, s in phi_by_axis.items() if a != axis))
            if unique_to_axis:
                analysis['axis_specific_discoveries'].append({
                    'axis': axis,
                    'unique_angles': sorted(list(unique_to_axis)),
                    'description': f'Phi angles unique to {axis}-axis'
                })
        
        return analysis
    
    def _analyze_parameter_patterns(self, results: List[Dict]) -> Dict:
        """Analyze patterns in parameter exploration"""
        patterns = {
            'phi_vs_size': [],
            'optimal_configurations': [],
            'scaling_laws': []
        }
        
        # Group by side length
        by_size = {}
        for r in results:
            side = r['side']
            if side not in by_size:
                by_size[side] = []
            by_size[side].append(r)
        
        # Analyze size dependence
        for side, configs in by_size.items():
            phi_count = sum(1 for c in configs if c['phi_found'])
            phi_ratio = phi_count / len(configs) if configs else 0
            
            patterns['phi_vs_size'].append({
                'size': side,
                'phi_occurrence_rate': phi_ratio,
                'total_configs': len(configs)
            })
        
        # Find optimal configurations
        for r in results:
            if r['phi_found'] and len(r['golden_ratio_distances']) > 0:
                patterns['optimal_configurations'].append({
                    'side': r['side'],
                    'angle': r['angle'],
                    'phi_count': len(r['golden_ratio_distances'])
                })
        
        return patterns
    
    def _compare_critical_angles(self, results: Dict) -> Dict:
        """Compare results across critical angles"""
        comparison = {
            'ranking_by_phi': [],
            'ranking_by_complexity': [],
            'special_angles': []
        }
        
        # Rank by phi occurrence
        phi_scores = [(angle, len(data.get('golden_ratio_distances', []))) 
                     for angle, data in results.items()]
        comparison['ranking_by_phi'] = sorted(phi_scores, key=lambda x: x[1], reverse=True)
        
        # Rank by geometric complexity
        complexity_scores = [(angle, data.get('num_unique_distances', 0) + 
                            data.get('num_unique_directions', 0))
                           for angle, data in results.items()]
        comparison['ranking_by_complexity'] = sorted(complexity_scores, key=lambda x: x[1], reverse=True)
        
        return comparison
    
    # ==================== REPORT GENERATION ====================
    
    def _generate_sweep_report(self, results: Dict, discoveries: List, axis: str) -> str:
        """Generate markdown report for angle sweep"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        report = [
            f"# Angle Sweep Discovery Report",
            f"**Axis:** {axis}",
            f"**Generated:** {timestamp}",
            f"**Computation:** REAL-TIME (not pre-populated)",
            "",
            "## Summary",
            f"- Total angles scanned: {len(results)}",
            f"- Discoveries found: {len(discoveries)}",
            "",
            "## Discoveries",
            ""
        ]
        
        for i, disc in enumerate(discoveries, 1):
            report.append(f"### Discovery #{i}: {disc['type']}")
            report.append(f"**Description:** {disc['description']}")
            report.append("")
        
        return "\n".join(report)
    
    def _generate_multi_axis_report(self, results: Dict, cross_analysis: Dict) -> str:
        """Generate multi-axis analysis report"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        report = [
            f"# Multi-Axis Scan Report",
            f"**Generated:** {timestamp}",
            f"**Computation:** REAL-TIME (not pre-populated)",
            "",
            "## Cross-Axis Analysis",
            ""
        ]
        
        if cross_analysis['common_patterns']:
            report.append("### Universal Patterns")
            for pattern in cross_analysis['common_patterns']:
                report.append(f"- {pattern['description']}")
            report.append("")
        
        if cross_analysis['axis_specific_discoveries']:
            report.append("### Axis-Specific Discoveries")
            for disc in cross_analysis['axis_specific_discoveries']:
                report.append(f"- **{disc['axis']}-axis:** {disc['description']}")
            report.append("")
        
        return "\n".join(report)
    
    def _generate_parameter_report(self, results: List, patterns: Dict) -> str:
        """Generate parameter exploration report"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        report = [
            f"# Parameter Space Exploration Report",
            f"**Generated:** {timestamp}",
            f"**Total Configurations:** {len(results)}",
            f"**Computation:** REAL-TIME (not pre-populated)",
            "",
            "## Optimal Configurations",
            ""
        ]
        
        for config in patterns['optimal_configurations'][:10]:  # Top 10
            report.append(f"- Side={config['side']}, Angle={config['angle']}° → {config['phi_count']} phi instances")
        
        return "\n".join(report)
    
    def _generate_critical_angle_report(self, results: Dict, comparison: Dict) -> str:
        """Generate critical angle analysis report"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        report = [
            f"# Critical Angle Analysis Report",
            f"**Generated:** {timestamp}",
            f"**Resolution:** HIGH (50k/25k pairs)",
            f"**Computation:** REAL-TIME (not pre-populated)",
            "",
            "## Ranking by Phi Occurrence",
            ""
        ]
        
        for angle, count in comparison['ranking_by_phi']:
            report.append(f"- {angle}°: {count} phi instances")
        
        report.append("")
        report.append("## Ranking by Geometric Complexity")
        report.append("")
        
        for angle, complexity in comparison['ranking_by_complexity']:
            report.append(f"- {angle}°: complexity score {complexity}")
        
        return "\n".join(report)
    
    # ==================== MAIN LOOP ====================
    
    def run_continuous(self, cycle_delay: int = 3600):
        """
        Run continuous discovery cycles.
        
        Args:
            cycle_delay: Seconds between cycles (default: 1 hour)
        """
        cycle = 1
        
        while self.running:
            try:
                logger.info(f"\n{'#'*70}")
                logger.info(f"### DISCOVERY CYCLE #{cycle}")
                logger.info(f"### Total discoveries so far: {self.discoveries_count}")
                logger.info(f"{'#'*70}\n")
                
                # Run all discovery modes
                self.mode_angle_sweep(axis='z')
                if not self.running: break
                
                self.mode_multi_axis_scan()
                if not self.running: break
                
                self.mode_parameter_exploration()
                if not self.running: break
                
                self.mode_critical_angle_analysis()
                if not self.running: break
                
                cycle += 1
                
                if self.running:
                    logger.info(f"\n{'='*70}")
                    logger.info(f"Cycle #{cycle-1} complete. Waiting {cycle_delay}s...")
                    logger.info(f"Total discoveries: {self.discoveries_count}")
                    logger.info(f"{'='*70}\n")
                    time.sleep(cycle_delay)
                
            except KeyboardInterrupt:
                break
            except Exception as e:
                logger.error(f"Error in discovery cycle: {e}", exc_info=True)
                logger.info("Continuing to next cycle...")
                time.sleep(60)
        
        logger.info(f"\n{'='*70}")
        logger.info(f"Autonomous Discovery Daemon Stopped")
        logger.info(f"Total discoveries made: {self.discoveries_count}")
        logger.info(f"Output directory: {self.output_dir}")
        logger.info(f"{'='*70}\n")
    
    def run_single_cycle(self):
        """Run one complete discovery cycle and exit"""
        logger.info("\n🔬 Running single discovery cycle...\n")
        
        self.mode_angle_sweep(axis='z')
        self.mode_multi_axis_scan()
        self.mode_parameter_exploration()
        self.mode_critical_angle_analysis()
        
        logger.info(f"\n✅ Single cycle complete. Discoveries: {self.discoveries_count}")


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Autonomous Discovery Daemon - Real-time computation and reporting'
    )
    parser.add_argument(
        '--mode',
        choices=['continuous', 'single'],
        default='single',
        help='Run continuously or single cycle (default: single)'
    )
    parser.add_argument(
        '--delay',
        type=int,
        default=3600,
        help='Seconds between cycles in continuous mode (default: 3600)'
    )
    parser.add_argument(
        '--output',
        default='autonomous_discoveries',
        help='Output directory (default: autonomous_discoveries)'
    )
    
    args = parser.parse_args()
    
    daemon = AutonomousDiscoveryDaemon(output_dir=args.output)
    
    if args.mode == 'continuous':
        daemon.run_continuous(cycle_delay=args.delay)
    else:
        daemon.run_single_cycle()


if __name__ == '__main__':
    main()
