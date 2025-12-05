#!/usr/bin/env python3
"""
Automated Parameter Space Explorer
Systematically explores parameter combinations to discover optimal configurations
and emergent patterns.
"""

import json
import numpy as np
from pathlib import Path
from typing import List, Dict, Any, Tuple
from dataclasses import dataclass, asdict
from concurrent.futures import ProcessPoolExecutor, as_completed
import itertools
from datetime import datetime
import logging

from orion_octave_test import main as run_analysis

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


@dataclass
class ExplorationConfig:
    """Configuration for parameter space exploration"""
    side_lengths: List[float]
    angles: List[float]
    max_distance_pairs: int = 10000
    max_direction_pairs: int = 5000
    parallel_workers: int = 4


@dataclass
class DiscoveryResult:
    """Significant discovery from parameter exploration"""
    discovery_type: str
    significance_score: float
    parameters: Dict[str, Any]
    evidence: Dict[str, Any]
    description: str


class ParameterSpaceExplorer:
    """Automated exploration of parameter space"""
    
    def __init__(self, config: ExplorationConfig):
        self.config = config
        self.results: List[Dict[str, Any]] = []
        self.discoveries: List[DiscoveryResult] = []
    
    def explore_grid_search(self, output_dir: str = 'exploration_results'):
        """Systematic grid search across parameter space"""
        
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)
        
        # Generate all combinations
        param_combinations = list(itertools.product(
            self.config.side_lengths,
            self.config.angles
        ))
        
        total = len(param_combinations)
        logger.info(f"Exploring {total} parameter combinations...")
        
        # Parallel execution
        with ProcessPoolExecutor(max_workers=self.config.parallel_workers) as executor:
            futures = {}
            
            for side, angle in param_combinations:
                future = executor.submit(
                    self._analyze_configuration,
                    side, angle
                )
                futures[future] = (side, angle)
            
            completed = 0
            for future in as_completed(futures):
                side, angle = futures[future]
                try:
                    result = future.result()
                    self.results.append(result)
                    
                    # Save individual result
                    filename = output_path / f"result_s{side}_a{angle}.json"
                    with open(filename, 'w') as f:
                        json.dump(result, f, indent=2)
                    
                    completed += 1
                    logger.info(f"Progress: {completed}/{total} - side={side}, angle={angle}")
                    
                except Exception as e:
                    logger.error(f"Failed for side={side}, angle={angle}: {e}")
        
        # Analyze results
        self._analyze_results()
        
        # Generate comprehensive report
        report = self._generate_exploration_report()
        
        # Save report
        report_file = output_path / 'exploration_report.json'
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"Exploration complete! Report saved to: {report_file}")
        
        return report
    
    def _analyze_configuration(self, side: float, angle: float) -> Dict[str, Any]:
        """Analyze a single configuration"""
        
        result = run_analysis(
            side=side,
            angle=angle,
            max_distance_pairs=self.config.max_distance_pairs,
            max_direction_pairs=self.config.max_direction_pairs,
            verbose=False
        )
        
        # Add metadata
        result['exploration_metadata'] = {
            'timestamp': datetime.now().isoformat(),
            'side': side,
            'angle': angle
        }
        
        return result
    
    def _analyze_results(self):
        """Analyze collected results for patterns and discoveries"""
        
        logger.info("Analyzing results for significant patterns...")
        
        # Find configurations with golden ratio
        self._find_golden_ratio_peaks()
        
        # Find optimal icosahedral matches
        self._find_icosahedral_matches()
        
        # Find unusual symmetry patterns
        self._find_symmetry_anomalies()
        
        # Find geometric transitions
        self._find_phase_transitions()
        
        # Find point density patterns
        self._find_density_patterns()
    
    def _find_golden_ratio_peaks(self):
        """Identify configurations with strong golden ratio presence"""
        
        phi_configs = []
        
        for result in self.results:
            phi_count = result['golden_ratio']['candidate_count']
            if phi_count > 0:
                side = result['configuration']['side_length']
                angle = result['configuration']['rotation_angle_degrees']
                
                phi_configs.append({
                    'side': side,
                    'angle': angle,
                    'count': phi_count,
                    'candidates': result['golden_ratio']['candidates']
                })
        
        if phi_configs:
            # Find peak
            peak = max(phi_configs, key=lambda x: x['count'])
            
            self.discoveries.append(DiscoveryResult(
                discovery_type="Golden Ratio Peak",
                significance_score=0.95,
                parameters={'side': peak['side'], 'angle': peak['angle']},
                evidence={'phi_candidates': peak['count']},
                description=f"Maximum golden ratio candidates ({peak['count']}) found at "
                           f"side={peak['side']}, angle={peak['angle']}°"
            ))
    
    def _find_icosahedral_matches(self):
        """Identify strong icosahedral symmetry matches"""
        
        strong_matches = []
        
        for result in self.results:
            ico = result['icosahedral_check']
            if ico['match_quality'] == 'strong':
                side = result['configuration']['side_length']
                angle = result['configuration']['rotation_angle_degrees']
                
                strong_matches.append({
                    'side': side,
                    'angle': angle,
                    'angle_error': ico['angle_degrees']
                })
        
        if strong_matches:
            # Find best match
            best = min(strong_matches, key=lambda x: x['angle_error'])
            
            self.discoveries.append(DiscoveryResult(
                discovery_type="Perfect Icosahedral Match",
                significance_score=0.98,
                parameters={'side': best['side'], 'angle': best['angle']},
                evidence={'angular_error': best['angle_error']},
                description=f"Near-perfect icosahedral symmetry (error={best['angle_error']:.3f}°) "
                           f"at side={best['side']}, angle={best['angle']}°"
            ))
    
    def _find_symmetry_anomalies(self):
        """Find unusual symmetry patterns"""
        
        for result in self.results:
            special_angles = result['special_angles']
            side = result['configuration']['side_length']
            angle = result['configuration']['rotation_angle_degrees']
            
            # Check for unexpected symmetries
            total_special = sum(data['count'] for data in special_angles.values())
            
            if total_special > 500:  # Threshold for high symmetry
                self.discoveries.append(DiscoveryResult(
                    discovery_type="High Symmetry Configuration",
                    significance_score=0.85,
                    parameters={'side': side, 'angle': angle},
                    evidence={'total_special_angles': total_special, 'distribution': special_angles},
                    description=f"Exceptional symmetry ({total_special} special angle occurrences) "
                               f"at side={side}, angle={angle}°"
                ))
    
    def _find_phase_transitions(self):
        """Identify abrupt changes in geometric properties"""
        
        if len(self.results) < 2:
            return
        
        # Sort by angle (assuming constant side for now)
        sorted_results = sorted(
            self.results,
            key=lambda x: x['configuration']['rotation_angle_degrees']
        )
        
        # Look for abrupt changes in point count
        for i in range(1, len(sorted_results)):
            prev = sorted_results[i-1]
            curr = sorted_results[i]
            
            prev_points = prev['point_counts']['unique_points']
            curr_points = curr['point_counts']['unique_points']
            
            change_ratio = abs(curr_points - prev_points) / prev_points if prev_points > 0 else 0
            
            if change_ratio > 0.5:  # 50% change
                self.discoveries.append(DiscoveryResult(
                    discovery_type="Geometric Phase Transition",
                    significance_score=0.90,
                    parameters={
                        'angle_before': prev['configuration']['rotation_angle_degrees'],
                        'angle_after': curr['configuration']['rotation_angle_degrees']
                    },
                    evidence={
                        'points_before': prev_points,
                        'points_after': curr_points,
                        'change_ratio': change_ratio
                    },
                    description=f"Abrupt {change_ratio*100:.1f}% change in interference points "
                               f"between {prev['configuration']['rotation_angle_degrees']}° and "
                               f"{curr['configuration']['rotation_angle_degrees']}°"
                ))
    
    def _find_density_patterns(self):
        """Identify optimal point density configurations"""
        
        if not self.results:
            return
        
        # Find configuration with most points
        max_points_result = max(self.results, key=lambda x: x['point_counts']['unique_points'])
        
        self.discoveries.append(DiscoveryResult(
            discovery_type="Maximum Interference Density",
            significance_score=0.80,
            parameters={
                'side': max_points_result['configuration']['side_length'],
                'angle': max_points_result['configuration']['rotation_angle_degrees']
            },
            evidence={'unique_points': max_points_result['point_counts']['unique_points']},
            description=f"Maximum interference lattice density "
                       f"({max_points_result['point_counts']['unique_points']} points) achieved"
        ))
    
    def _generate_exploration_report(self) -> Dict[str, Any]:
        """Generate comprehensive exploration report"""
        
        # Sort discoveries by significance
        self.discoveries.sort(key=lambda x: x.significance_score, reverse=True)
        
        report = {
            'exploration_summary': {
                'timestamp': datetime.now().isoformat(),
                'total_configurations': len(self.results),
                'parameter_space': {
                    'side_lengths': self.config.side_lengths,
                    'angles': self.config.angles
                },
                'discoveries_found': len(self.discoveries)
            },
            'key_discoveries': [asdict(d) for d in self.discoveries],
            'statistical_summary': self._compute_statistics(),
            'optimal_configurations': self._identify_optimal_configs(),
            'tech_specs': self._generate_tech_specs()
        }
        
        return report
    
    def _compute_statistics(self) -> Dict[str, Any]:
        """Compute statistical summary across all results"""
        
        if not self.results:
            return {}
        
        phi_counts = [r['golden_ratio']['candidate_count'] for r in self.results]
        point_counts = [r['point_counts']['unique_points'] for r in self.results]
        direction_counts = [r['directions']['unique_count'] for r in self.results]
        
        return {
            'golden_ratio_statistics': {
                'mean_candidates': np.mean(phi_counts),
                'max_candidates': np.max(phi_counts),
                'configurations_with_phi': sum(1 for c in phi_counts if c > 0),
                'percentage_with_phi': sum(1 for c in phi_counts if c > 0) / len(phi_counts) * 100
            },
            'point_density_statistics': {
                'mean_points': np.mean(point_counts),
                'std_points': np.std(point_counts),
                'min_points': np.min(point_counts),
                'max_points': np.max(point_counts)
            },
            'direction_statistics': {
                'mean_directions': np.mean(direction_counts),
                'std_directions': np.std(direction_counts)
            }
        }
    
    def _identify_optimal_configs(self) -> Dict[str, Any]:
        """Identify optimal configurations for different objectives"""
        
        if not self.results:
            return {}
        
        # Best for golden ratio
        best_phi = max(self.results, key=lambda x: x['golden_ratio']['candidate_count'])
        
        # Best for icosahedral match
        best_ico = min(
            [r for r in self.results if r['icosahedral_check']['angle_degrees'] is not None],
            key=lambda x: x['icosahedral_check']['angle_degrees'],
            default=None
        )
        
        # Best for point density
        best_density = max(self.results, key=lambda x: x['point_counts']['unique_points'])
        
        return {
            'for_golden_ratio': {
                'side': best_phi['configuration']['side_length'],
                'angle': best_phi['configuration']['rotation_angle_degrees'],
                'candidates': best_phi['golden_ratio']['candidate_count']
            },
            'for_icosahedral_symmetry': {
                'side': best_ico['configuration']['side_length'] if best_ico else None,
                'angle': best_ico['configuration']['rotation_angle_degrees'] if best_ico else None,
                'error': best_ico['icosahedral_check']['angle_degrees'] if best_ico else None
            } if best_ico else None,
            'for_maximum_density': {
                'side': best_density['configuration']['side_length'],
                'angle': best_density['configuration']['rotation_angle_degrees'],
                'points': best_density['point_counts']['unique_points']
            }
        }
    
    def _generate_tech_specs(self) -> List[Dict[str, Any]]:
        """Generate potential tech specs from discoveries"""
        
        tech_specs = []
        
        for discovery in self.discoveries:
            if discovery.significance_score > 0.90:
                tech_spec = {
                    'name': discovery.discovery_type,
                    'confidence': discovery.significance_score,
                    'category': 'Geometric Optimization',
                    'parameters': discovery.parameters,
                    'potential_applications': self._suggest_applications(discovery),
                    'description': discovery.description,
                    'evidence': discovery.evidence
                }
                tech_specs.append(tech_spec)
        
        return tech_specs
    
    def _suggest_applications(self, discovery: DiscoveryResult) -> List[str]:
        """Suggest potential applications for a discovery"""
        
        applications = []
        
        if discovery.discovery_type == "Golden Ratio Peak":
            applications = [
                "Optimal antenna array configuration",
                "Crystal lattice design with phi-based properties",
                "Architectural space-filling patterns",
                "Natural resonance frequency structures"
            ]
        elif discovery.discovery_type == "Perfect Icosahedral Match":
            applications = [
                "Viral capsid structure modeling",
                "Fullerene and carbon structure design",
                "Spherical antenna array optimization",
                "Geodesic dome construction parameters"
            ]
        elif discovery.discovery_type == "High Symmetry Configuration":
            applications = [
                "Crystallographic material design",
                "Photonic crystal optimization",
                "Metamaterial unit cell design",
                "Periodic structure engineering"
            ]
        elif discovery.discovery_type == "Maximum Interference Density":
            applications = [
                "Maximal point lattice generation",
                "Dense packing problem solutions",
                "Sensor array placement optimization",
                "Sampling point distribution"
            ]
        
        return applications


def main():
    """Run automated parameter space exploration"""
    
    # Define exploration configuration
    config = ExplorationConfig(
        side_lengths=[1.0, 2.0, 3.0],
        angles=[15, 30, 36, 45, 60, 72, 90, 120],
        max_distance_pairs=10000,
        max_direction_pairs=5000,
        parallel_workers=4
    )
    
    explorer = ParameterSpaceExplorer(config)
    
    print("="*80)
    print("AUTOMATED PARAMETER SPACE EXPLORATION")
    print("="*80)
    print(f"\nSide lengths: {config.side_lengths}")
    print(f"Angles: {config.angles}")
    print(f"Total configurations: {len(config.side_lengths) * len(config.angles)}")
    print(f"Parallel workers: {config.parallel_workers}")
    print("\n" + "="*80)
    
    report = explorer.explore_grid_search()
    
    # Print discoveries
    print("\n" + "="*80)
    print(f"DISCOVERIES ({len(explorer.discoveries)} found)")
    print("="*80)
    
    for i, discovery in enumerate(explorer.discoveries, 1):
        print(f"\n{i}. {discovery.discovery_type}")
        print(f"   Significance: {discovery.significance_score:.2f}")
        print(f"   {discovery.description}")
        print(f"   Parameters: {discovery.parameters}")
    
    print("\n" + "="*80)
    print("OPTIMAL CONFIGURATIONS")
    print("="*80)
    
    for objective, config in report['optimal_configurations'].items():
        if config:
            print(f"\n{objective}:")
            for key, value in config.items():
                print(f"  {key}: {value}")
    
    print("\n" + "="*80)


if __name__ == '__main__':
    main()
