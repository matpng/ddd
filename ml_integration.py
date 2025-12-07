#!/usr/bin/env python3
"""
ML Integration Module
Connects machine learning discovery to the main application
"""

import logging
import json
from pathlib import Path
from typing import Dict, List, Any, Optional
import threading
import time

from ml_discovery import MLPatternDiscovery
from discovery_manager import DiscoveryManager

logger = logging.getLogger(__name__)


class MLIntegration:
    """
    Integrates ML pattern discovery with the autonomous system.
    """
    
    def __init__(self, discovery_manager: DiscoveryManager):
        self.discovery_manager = discovery_manager
        self.ml_engine = MLPatternDiscovery()
        self.last_analysis = None
        self.is_running = False
        self._lock = threading.Lock()
    
    def analyze_discoveries(self, min_discoveries: int = 10) -> Optional[Dict[str, Any]]:
        """
        Analyze recent discoveries using ML techniques.
        
        Args:
            min_discoveries: Minimum number of discoveries needed for analysis
            
        Returns:
            Analysis results or None if insufficient data
        """
        try:
            # Get recent discoveries
            discoveries = self.discovery_manager.get_all(limit=1000)
            
            if discoveries['total'] < min_discoveries:
                logger.warning(f"Insufficient discoveries for ML analysis: {discoveries['total']} < {min_discoveries}")
                return None
            
            logger.info(f"Running ML analysis on {discoveries['total']} discoveries...")
            
            # Convert discoveries to format expected by ML engine
            results = self._convert_discoveries_to_results(discoveries['discoveries'])
            
            if not results:
                logger.warning("No valid results for ML analysis")
                return None
            
            # Extract features and run analyses
            features, metadata = self.ml_engine._extract_features(results)
            
            # Run clustering
            self.ml_engine._cluster_analysis(features, metadata, results)
            
            # Run anomaly detection
            self.ml_engine._anomaly_detection(features, metadata, results)
            
            # Run dimensionality reduction
            self.ml_engine._dimensionality_reduction(features, metadata, results)
            
            # Run correlation analysis
            self.ml_engine._correlation_analysis(features, metadata)
            
            # Generate report
            report = self.ml_engine._generate_ml_report()
            
            # Store analysis results
            with self._lock:
                self.last_analysis = {
                    'timestamp': time.time(),
                    'discoveries_analyzed': len(results),
                    'patterns_found': len(self.ml_engine.patterns),
                    'report': report
                }
            
            logger.info(f"ML analysis complete: found {len(self.ml_engine.patterns)} patterns")
            
            return self.last_analysis
            
        except Exception as e:
            logger.error(f"Error in ML analysis: {e}", exc_info=True)
            return None
    
    def get_last_analysis(self) -> Optional[Dict[str, Any]]:
        """Get the most recent ML analysis results."""
        with self._lock:
            return self.last_analysis
    
    def get_patterns(self) -> List[Dict[str, Any]]:
        """Get discovered patterns from ML analysis."""
        patterns = []
        for pattern in self.ml_engine.patterns:
            patterns.append({
                'type': pattern.pattern_type,
                'confidence': pattern.confidence,
                'description': pattern.description,
                'feature_importance': pattern.feature_importance,
                'examples': pattern.examples,
                'significance': pattern.potential_significance
            })
        return patterns
    
    def start_background_analysis(self, interval: int = 3600):
        """
        Start background ML analysis thread.
        
        Args:
            interval: Analysis interval in seconds (default: 1 hour)
        """
        if self.is_running:
            logger.warning("ML background analysis already running")
            return
        
        self.is_running = True
        thread = threading.Thread(target=self._background_analysis_loop, args=(interval,), daemon=True)
        thread.start()
        logger.info(f"Started ML background analysis (interval: {interval}s)")
    
    def stop_background_analysis(self):
        """Stop background ML analysis."""
        self.is_running = False
        logger.info("Stopped ML background analysis")
    
    def _background_analysis_loop(self, interval: int):
        """Background loop for periodic ML analysis."""
        while self.is_running:
            try:
                self.analyze_discoveries()
                
                # Sleep in chunks to allow for quick shutdown
                for _ in range(interval):
                    if not self.is_running:
                        break
                    time.sleep(1)
                    
            except Exception as e:
                logger.error(f"Error in ML background loop: {e}")
                time.sleep(60)  # Wait a minute before retrying
    
    def _convert_discoveries_to_results(self, discoveries: List[Dict]) -> List[Dict]:
        """
        Convert discovery manager format to ML engine format.
        
        Args:
            discoveries: List of discoveries from discovery manager
            
        Returns:
            List of results in format expected by ML engine
        """
        results = []
        
        for disc in discoveries:
            try:
                # Get full discovery data
                full_disc = self.discovery_manager.get_by_id(disc['id'])
                if not full_disc or 'data' not in full_disc:
                    continue
                
                data = full_disc['data']
                
                # Extract or create required fields
                summary = data.get('summary', {})
                full_results = data.get('full_results', {})
                
                # Build result in expected format
                result = {
                    'configuration': {
                        'side_length': summary.get('cube_size', 2.0),
                        'rotation_angle_degrees': data.get('angle', 0)
                    },
                    'point_counts': {
                        'unique_points': summary.get('unique_points', 0),
                        'edge_face_intersections': summary.get('edge_face_intersections', 0),
                        'edge_edge_intersections': summary.get('edge_edge_intersections', 0)
                    },
                    'golden_ratio': {
                        'candidate_count': summary.get('golden_ratio_candidates', 0)
                    },
                    'directions': {
                        'unique_count': summary.get('unique_directions', 0)
                    },
                    'angles': {
                        'total_measured': summary.get('total_angle_pairs', 0)
                    },
                    'special_angles': summary.get('special_angles', {}),
                    'distances': {
                        'unique_count': summary.get('unique_distances', 0),
                        'min': summary.get('min_distance', 0),
                        'max': summary.get('max_distance', 0),
                        'mean': summary.get('distance_mean', 0),
                        'std': summary.get('distance_std', 0)
                    }
                }
                
                results.append(result)
                
            except Exception as e:
                logger.error(f"Error converting discovery {disc.get('id', 'unknown')}: {e}")
                continue
        
        return results
    
    def export_patterns_to_json(self, filepath: str):
        """Export discovered patterns to JSON file."""
        try:
            patterns = self.get_patterns()
            with open(filepath, 'w') as f:
                json.dump({
                    'timestamp': self.last_analysis.get('timestamp') if self.last_analysis else None,
                    'total_patterns': len(patterns),
                    'patterns': patterns
                }, f, indent=2)
            logger.info(f"Patterns exported to {filepath}")
        except Exception as e:
            logger.error(f"Error exporting patterns: {e}")


# Global ML integration instance (initialized with discovery manager in app.py)
ml_integration = None


def initialize_ml_integration(discovery_manager: DiscoveryManager) -> MLIntegration:
    """Initialize global ML integration instance."""
    global ml_integration
    ml_integration = MLIntegration(discovery_manager)
    return ml_integration
