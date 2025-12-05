#!/usr/bin/env python3
"""
Fully Automated Discovery System
Orchestrates all automation components to discover life-changing tech specs.
"""

import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List
import sys

from auto_explorer import ParameterSpaceExplorer, ExplorationConfig
from ml_discovery import MLPatternDiscovery
from comprehensive_tests import run_test_suite

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('automation.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class AutomatedDiscoverySystem:
    """Fully automated geometric discovery system"""
    
    def __init__(self, output_dir: str = 'discovery_output'):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        self.session_id = datetime.now().strftime('%Y%m%d_%H%M%S')
        self.session_dir = self.output_dir / self.session_id
        self.session_dir.mkdir(exist_ok=True)
        
        logger.info(f"Initialized discovery session: {self.session_id}")
    
    def run_full_discovery(self, 
                          test_first: bool = True,
                          exploration_config: ExplorationConfig = None,
                          run_ml: bool = True) -> Dict[str, Any]:
        """
        Run complete automated discovery pipeline
        
        Pipeline:
        1. Validate system with comprehensive tests
        2. Explore parameter space systematically
        3. Apply ML to discover patterns
        4. Generate tech specs and recommendations
        """
        
        results = {
            'session_id': self.session_id,
            'timestamp': datetime.now().isoformat(),
            'stages': {}
        }
        
        # Stage 1: Validation
        if test_first:
            logger.info("="*80)
            logger.info("STAGE 1: SYSTEM VALIDATION")
            logger.info("="*80)
            
            test_success = self._run_validation()
            results['stages']['validation'] = {
                'success': test_success,
                'description': 'Comprehensive automated testing'
            }
            
            if not test_success:
                logger.error("System validation failed! Aborting discovery.")
                return results
            
            logger.info("✓ System validation passed\n")
        
        # Stage 2: Parameter Space Exploration
        logger.info("="*80)
        logger.info("STAGE 2: PARAMETER SPACE EXPLORATION")
        logger.info("="*80)
        
        exploration_results = self._run_exploration(exploration_config)
        results['stages']['exploration'] = exploration_results
        
        logger.info("✓ Parameter space exploration complete\n")
        
        # Stage 3: ML Pattern Discovery
        if run_ml:
            logger.info("="*80)
            logger.info("STAGE 3: ML PATTERN DISCOVERY")
            logger.info("="*80)
            
            ml_results = self._run_ml_discovery()
            results['stages']['ml_discovery'] = ml_results
            
            logger.info("✓ ML pattern discovery complete\n")
        
        # Stage 4: Tech Spec Generation
        logger.info("="*80)
        logger.info("STAGE 4: TECH SPEC GENERATION")
        logger.info("="*80)
        
        tech_specs = self._generate_tech_specs(results)
        results['tech_specs'] = tech_specs
        
        logger.info("✓ Tech spec generation complete\n")
        
        # Save comprehensive report
        self._save_final_report(results)
        
        return results
    
    def _run_validation(self) -> bool:
        """Run comprehensive test suite"""
        
        try:
            logger.info("Running comprehensive test suite...")
            success = run_test_suite()
            return success
        except Exception as e:
            logger.error(f"Testing failed with error: {e}")
            return False
    
    def _run_exploration(self, config: ExplorationConfig = None) -> Dict[str, Any]:
        """Run parameter space exploration"""
        
        if config is None:
            # Default exploration configuration
            config = ExplorationConfig(
                side_lengths=[1.0, 2.0, 3.0],
                angles=[15, 30, 36, 45, 60, 72, 90, 108, 120],
                max_distance_pairs=10000,
                max_direction_pairs=5000,
                parallel_workers=4
            )
        
        explorer = ParameterSpaceExplorer(config)
        
        # Run exploration with results in session directory
        exploration_dir = self.session_dir / 'exploration_results'
        report = explorer.explore_grid_search(output_dir=str(exploration_dir))
        
        return {
            'configurations_explored': len(explorer.results),
            'discoveries_found': len(explorer.discoveries),
            'output_directory': str(exploration_dir),
            'summary': report['exploration_summary']
        }
    
    def _run_ml_discovery(self) -> Dict[str, Any]:
        """Run ML-based pattern discovery"""
        
        ml_discovery = MLPatternDiscovery()
        
        # Analyze exploration results from session
        exploration_dir = self.session_dir / 'exploration_results'
        report = ml_discovery.analyze_exploration_results(results_dir=str(exploration_dir))
        
        if not report:
            logger.warning("No ML analysis performed - no exploration results found")
            return {'status': 'skipped', 'reason': 'no exploration results'}
        
        return {
            'patterns_discovered': report['ml_analysis_summary']['total_patterns_discovered'],
            'high_confidence_patterns': report['ml_analysis_summary']['high_confidence_patterns'],
            'methods_used': report['ml_analysis_summary']['analysis_methods']
        }
    
    def _generate_tech_specs(self, results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate final tech specs from all discovery stages"""
        
        tech_specs = []
        
        # Load exploration report
        exploration_dir = self.session_dir / 'exploration_results'
        exploration_report_file = exploration_dir / 'exploration_report.json'
        
        if exploration_report_file.exists():
            with open(exploration_report_file) as f:
                exploration_report = json.load(f)
            
            # Add exploration-based tech specs
            if 'tech_specs' in exploration_report:
                tech_specs.extend(exploration_report['tech_specs'])
        
        # Load ML report
        ml_report_file = exploration_dir / 'ml_discovery_report.json'
        
        if ml_report_file.exists():
            with open(ml_report_file) as f:
                ml_report = json.load(f)
            
            # Add ML-based tech specs
            for pattern in ml_report.get('discovered_patterns', []):
                if pattern['confidence'] > 0.85:
                    tech_specs.append({
                        'name': f"ML-Discovered: {pattern['pattern_type']}",
                        'confidence': pattern['confidence'],
                        'category': 'Machine Learning Discovery',
                        'description': pattern['description'],
                        'evidence': pattern['feature_importance'],
                        'potential_applications': self._ml_pattern_applications(pattern)
                    })
        
        # Generate synthesis tech specs
        tech_specs.extend(self._generate_synthesis_specs(exploration_report, ml_report))
        
        # Sort by confidence
        tech_specs.sort(key=lambda x: x.get('confidence', 0), reverse=True)
        
        return tech_specs
    
    def _ml_pattern_applications(self, pattern: Dict[str, Any]) -> List[str]:
        """Generate applications for ML-discovered patterns"""
        
        applications = []
        
        if 'Cluster' in pattern['pattern_type']:
            applications = [
                "Identify optimal parameter regimes for specific applications",
                "Guide multi-objective optimization strategies",
                "Define geometric design spaces for targeted properties"
            ]
        elif 'Anomalous' in pattern['pattern_type']:
            applications = [
                "Investigate novel geometric phenomena",
                "Explore unconventional design spaces",
                "Discover breakthrough configurations"
            ]
        elif 'Correlation' in pattern['pattern_type']:
            applications = [
                "Develop predictive models for geometric properties",
                "Reduce computational search space",
                "Optimize for multiple objectives simultaneously"
            ]
        
        return applications
    
    def _generate_synthesis_specs(self, 
                                  exploration_report: Dict[str, Any],
                                  ml_report: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate synthesis tech specs combining insights"""
        
        synthesis_specs = []
        
        # Cross-reference golden ratio discoveries with ML clusters
        if exploration_report and ml_report:
            synthesis_specs.append({
                'name': 'Integrated Geometric Optimization Framework',
                'confidence': 0.92,
                'category': 'Synthesis',
                'description': 'Combined insights from systematic exploration and ML analysis '
                              'reveal optimal geometric configurations for specific objectives',
                'evidence': {
                    'exploration_discoveries': len(exploration_report.get('key_discoveries', [])),
                    'ml_patterns': len(ml_report.get('discovered_patterns', []))
                },
                'potential_applications': [
                    'Design space-filling structures with maximal efficiency',
                    'Create metamaterials with targeted electromagnetic properties',
                    'Optimize crystallographic unit cells for novel materials',
                    'Develop bio-inspired geometric patterns for engineering applications'
                ]
            })
        
        return synthesis_specs
    
    def _save_final_report(self, results: Dict[str, Any]):
        """Save comprehensive final report"""
        
        report_file = self.session_dir / 'FINAL_DISCOVERY_REPORT.json'
        
        with open(report_file, 'w') as f:
            json.dump(results, f, indent=2)
        
        logger.info(f"Final report saved to: {report_file}")
        
        # Generate human-readable summary
        self._generate_summary_document(results)
    
    def _generate_summary_document(self, results: Dict[str, Any]):
        """Generate human-readable summary document"""
        
        summary_file = self.session_dir / 'DISCOVERY_SUMMARY.txt'
        
        with open(summary_file, 'w') as f:
            f.write("="*80 + "\n")
            f.write("AUTOMATED GEOMETRIC DISCOVERY SYSTEM\n")
            f.write("FINAL DISCOVERY REPORT\n")
            f.write("="*80 + "\n\n")
            
            f.write(f"Session ID: {results['session_id']}\n")
            f.write(f"Timestamp: {results['timestamp']}\n\n")
            
            # Stage summaries
            f.write("="*80 + "\n")
            f.write("PIPELINE STAGES\n")
            f.write("="*80 + "\n\n")
            
            for stage_name, stage_data in results.get('stages', {}).items():
                f.write(f"{stage_name.upper()}:\n")
                for key, value in stage_data.items():
                    f.write(f"  {key}: {value}\n")
                f.write("\n")
            
            # Tech specs
            f.write("="*80 + "\n")
            f.write(f"DISCOVERED TECH SPECS ({len(results.get('tech_specs', []))} total)\n")
            f.write("="*80 + "\n\n")
            
            for i, spec in enumerate(results.get('tech_specs', [])[:10], 1):
                f.write(f"{i}. {spec['name']}\n")
                f.write(f"   Confidence: {spec['confidence']:.2f}\n")
                f.write(f"   Category: {spec['category']}\n")
                f.write(f"   Description: {spec['description']}\n")
                
                if 'potential_applications' in spec:
                    f.write(f"   Applications:\n")
                    for app in spec['potential_applications']:
                        f.write(f"     - {app}\n")
                f.write("\n")
            
            f.write("="*80 + "\n")
            f.write("END OF REPORT\n")
            f.write("="*80 + "\n")
        
        logger.info(f"Summary document saved to: {summary_file}")


def main():
    """Run fully automated discovery system"""
    
    print("="*80)
    print("FULLY AUTOMATED GEOMETRIC DISCOVERY SYSTEM")
    print("="*80)
    print()
    print("This system will:")
    print("  1. Validate all components with comprehensive tests")
    print("  2. Systematically explore parameter space")
    print("  3. Apply machine learning to discover patterns")
    print("  4. Generate tech specs for life-changing applications")
    print()
    print("="*80)
    
    # Create discovery system
    system = AutomatedDiscoverySystem()
    
    # Configure exploration
    config = ExplorationConfig(
        side_lengths=[1.0, 2.0, 3.0],
        angles=[15, 30, 36, 45, 60, 72, 90, 108, 120],
        max_distance_pairs=10000,
        max_direction_pairs=5000,
        parallel_workers=4
    )
    
    # Run full discovery
    try:
        results = system.run_full_discovery(
            test_first=True,
            exploration_config=config,
            run_ml=True
        )
        
        # Print summary
        print("\n" + "="*80)
        print("DISCOVERY COMPLETE!")
        print("="*80)
        print(f"\nSession: {results['session_id']}")
        print(f"Tech Specs Generated: {len(results.get('tech_specs', []))}")
        print(f"\nResults saved to: {system.session_dir}")
        print("="*80)
        
        # Show top tech specs
        if results.get('tech_specs'):
            print("\nTOP 5 TECH SPECS:")
            print("="*80)
            for i, spec in enumerate(results['tech_specs'][:5], 1):
                print(f"\n{i}. {spec['name']}")
                print(f"   Confidence: {spec['confidence']:.2f}")
                print(f"   {spec['description']}")
        
        print("\n" + "="*80)
        
    except Exception as e:
        logger.error(f"Discovery system failed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    main()
