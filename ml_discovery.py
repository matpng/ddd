#!/usr/bin/env python3
"""
Machine Learning Pattern Discovery Module
Uses unsupervised learning to identify novel patterns and anomalies in geometric data.
"""

import json
import numpy as np
from pathlib import Path
from typing import List, Dict, Any, Tuple
from dataclasses import dataclass, asdict
from sklearn.cluster import DBSCAN, KMeans
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import IsolationForest
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


@dataclass
class Pattern:
    """Discovered pattern from ML analysis"""
    pattern_type: str
    confidence: float
    feature_importance: Dict[str, float]
    description: str
    examples: List[Dict[str, Any]]
    potential_significance: str


class MLPatternDiscovery:
    """Machine learning-based pattern discovery"""
    
    def __init__(self):
        self.scaler = StandardScaler()
        self.patterns: List[Pattern] = []
    
    def analyze_exploration_results(self, results_dir: str = 'exploration_results'):
        """Analyze exploration results using ML techniques"""
        
        results_path = Path(results_dir)
        
        # Load all results
        results = []
        for json_file in results_path.glob('result_*.json'):
            with open(json_file, 'r') as f:
                results.append(json.load(f))
        
        if not results:
            logger.warning("No results found to analyze")
            return []
        
        logger.info(f"Loaded {len(results)} results for ML analysis")
        
        # Extract features
        features, metadata = self._extract_features(results)
        
        # Normalize features
        features_scaled = self.scaler.fit_transform(features)
        
        # Run ML analyses
        self._cluster_analysis(features_scaled, metadata, results)
        self._anomaly_detection(features_scaled, metadata, results)
        self._dimensionality_reduction(features_scaled, metadata, results)
        self._correlation_analysis(features, metadata)
        
        # Generate report
        report = self._generate_ml_report()
        
        # Save report
        report_file = results_path / 'ml_discovery_report.json'
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"ML analysis complete! Report saved to: {report_file}")
        
        return report
    
    def _extract_features(self, results: List[Dict]) -> Tuple[np.ndarray, List[Dict]]:
        """Extract numerical features from results"""
        
        features = []
        metadata = []
        
        for result in results:
            feature_vector = [
                result['configuration']['side_length'],
                result['configuration']['rotation_angle_degrees'],
                result['point_counts']['unique_points'],
                result['point_counts']['edge_face_intersections'],
                result['point_counts']['edge_edge_intersections'],
                result['golden_ratio']['candidate_count'],
                result['directions']['unique_count'],
                result['angles']['total_measured'],
                result['special_angles'].get('30°', {}).get('count', 0),
                result['special_angles'].get('36°', {}).get('count', 0),
                result['special_angles'].get('45°', {}).get('count', 0),
                result['special_angles'].get('60°', {}).get('count', 0),
                result['special_angles'].get('72°', {}).get('count', 0),
                result['special_angles'].get('90°', {}).get('count', 0),
            ]
            
            # Add distance metrics if available
            if result['distances']['unique_count'] > 0:
                feature_vector.extend([
                    result['distances']['unique_count'],
                    result['distances']['min'],
                    result['distances']['max'],
                    result['distances']['mean'],
                    result['distances']['std']
                ])
            else:
                feature_vector.extend([0, 0, 0, 0, 0])
            
            features.append(feature_vector)
            
            metadata.append({
                'side': result['configuration']['side_length'],
                'angle': result['configuration']['rotation_angle_degrees']
            })
        
        return np.array(features), metadata
    
    def _cluster_analysis(self, features: np.ndarray, metadata: List[Dict], 
                         results: List[Dict]):
        """Identify natural clusters in the parameter space"""
        
        logger.info("Running cluster analysis...")
        
        # DBSCAN for density-based clustering
        dbscan = DBSCAN(eps=0.5, min_samples=2)
        cluster_labels = dbscan.fit_predict(features)
        
        n_clusters = len(set(cluster_labels)) - (1 if -1 in cluster_labels else 0)
        n_noise = list(cluster_labels).count(-1)
        
        logger.info(f"Found {n_clusters} clusters, {n_noise} outliers")
        
        # Analyze each cluster
        for cluster_id in set(cluster_labels):
            if cluster_id == -1:  # Skip noise
                continue
            
            cluster_mask = cluster_labels == cluster_id
            cluster_results = [r for r, mask in zip(results, cluster_mask) if mask]
            cluster_metadata = [m for m, mask in zip(metadata, cluster_mask) if mask]
            
            # Characterize cluster
            avg_phi = np.mean([r['golden_ratio']['candidate_count'] for r in cluster_results])
            avg_points = np.mean([r['point_counts']['unique_points'] for r in cluster_results])
            
            if avg_phi > 5 or avg_points > 100:  # Significant cluster
                self.patterns.append(Pattern(
                    pattern_type=f"Cluster {cluster_id}",
                    confidence=0.85,
                    feature_importance={
                        'avg_golden_ratio_candidates': avg_phi,
                        'avg_unique_points': avg_points,
                        'cluster_size': len(cluster_results)
                    },
                    description=f"Natural grouping of {len(cluster_results)} configurations "
                               f"with similar geometric properties",
                    examples=cluster_metadata[:3],
                    potential_significance="Configurations in this cluster share fundamental "
                                          "geometric relationships that may indicate optimal "
                                          "parameter regimes"
                ))
    
    def _anomaly_detection(self, features: np.ndarray, metadata: List[Dict],
                          results: List[Dict]):
        """Detect anomalous configurations"""
        
        logger.info("Running anomaly detection...")
        
        # Isolation Forest for anomaly detection
        iso_forest = IsolationForest(contamination=0.1, random_state=42)
        anomaly_labels = iso_forest.fit_predict(features)
        
        anomaly_scores = iso_forest.score_samples(features)
        
        # Find most anomalous configurations
        anomaly_indices = np.where(anomaly_labels == -1)[0]
        
        if len(anomaly_indices) > 0:
            # Sort by anomaly score (most negative = most anomalous)
            sorted_anomalies = sorted(
                [(i, anomaly_scores[i]) for i in anomaly_indices],
                key=lambda x: x[1]
            )
            
            for i, score in sorted_anomalies[:5]:  # Top 5 anomalies
                result = results[i]
                
                self.patterns.append(Pattern(
                    pattern_type="Anomalous Configuration",
                    confidence=0.90,
                    feature_importance={
                        'anomaly_score': float(score),
                        'phi_candidates': result['golden_ratio']['candidate_count'],
                        'unique_points': result['point_counts']['unique_points']
                    },
                    description=f"Highly unusual geometric configuration detected",
                    examples=[metadata[i]],
                    potential_significance="This configuration exhibits properties significantly "
                                          "different from the norm, potentially indicating a "
                                          "unique geometric regime worth investigating"
                ))
    
    def _dimensionality_reduction(self, features: np.ndarray, metadata: List[Dict],
                                 results: List[Dict]):
        """Reduce dimensionality to find key feature combinations"""
        
        logger.info("Running dimensionality reduction (PCA)...")
        
        # PCA to identify principal components
        pca = PCA(n_components=min(5, features.shape[1]))
        principal_components = pca.fit_transform(features)
        
        # Analyze explained variance
        explained_variance = pca.explained_variance_ratio_
        
        logger.info(f"Top 3 components explain {sum(explained_variance[:3])*100:.1f}% of variance")
        
        # Find configurations that score high on principal components
        for i, component in enumerate(principal_components.T[:3]):  # Top 3 components
            # Find extreme values on this component
            top_idx = np.argmax(component)
            bottom_idx = np.argmin(component)
            
            if explained_variance[i] > 0.15:  # Only if component is significant
                self.patterns.append(Pattern(
                    pattern_type=f"Principal Component {i+1} Extremes",
                    confidence=0.75,
                    feature_importance={
                        'variance_explained': float(explained_variance[i]),
                        'top_score': float(component[top_idx]),
                        'bottom_score': float(component[bottom_idx])
                    },
                    description=f"Configurations at extremes of principal component {i+1} "
                               f"(explains {explained_variance[i]*100:.1f}% of variance)",
                    examples=[metadata[top_idx], metadata[bottom_idx]],
                    potential_significance=f"These configurations represent opposite extremes "
                                          f"along a major axis of variation in the parameter space"
                ))
    
    def _correlation_analysis(self, features: np.ndarray, metadata: List[Dict]):
        """Find strong correlations between features"""
        
        logger.info("Running correlation analysis...")
        
        feature_names = [
            'side_length', 'angle', 'unique_points', 'edge_face_int', 'edge_edge_int',
            'phi_candidates', 'directions', 'total_angles',
            'angle_30', 'angle_36', 'angle_45', 'angle_60', 'angle_72', 'angle_90',
            'dist_count', 'dist_min', 'dist_max', 'dist_mean', 'dist_std'
        ]
        
        # Compute correlation matrix
        corr_matrix = np.corrcoef(features.T)
        
        # Find strong correlations (excluding diagonal)
        strong_correlations = []
        n_features = len(feature_names)
        
        for i in range(n_features):
            for j in range(i+1, n_features):
                corr = corr_matrix[i, j]
                if abs(corr) > 0.7:  # Strong correlation threshold
                    strong_correlations.append({
                        'feature1': feature_names[i],
                        'feature2': feature_names[j],
                        'correlation': float(corr)
                    })
        
        if strong_correlations:
            # Sort by absolute correlation
            strong_correlations.sort(key=lambda x: abs(x['correlation']), reverse=True)
            
            for corr_data in strong_correlations[:3]:  # Top 3
                self.patterns.append(Pattern(
                    pattern_type="Strong Feature Correlation",
                    confidence=0.80,
                    feature_importance={
                        'correlation_coefficient': corr_data['correlation'],
                        'feature1': corr_data['feature1'],
                        'feature2': corr_data['feature2']
                    },
                    description=f"Strong {'positive' if corr_data['correlation'] > 0 else 'negative'} "
                               f"correlation ({abs(corr_data['correlation']):.2f}) between "
                               f"{corr_data['feature1']} and {corr_data['feature2']}",
                    examples=[],
                    potential_significance="This correlation suggests a fundamental relationship "
                                          "between these geometric properties that could guide "
                                          "optimization strategies"
                ))
    
    def _generate_ml_report(self) -> Dict[str, Any]:
        """Generate ML discovery report"""
        
        # Sort patterns by confidence
        self.patterns.sort(key=lambda x: x.confidence, reverse=True)
        
        report = {
            'ml_analysis_summary': {
                'total_patterns_discovered': len(self.patterns),
                'high_confidence_patterns': len([p for p in self.patterns if p.confidence > 0.85]),
                'analysis_methods': [
                    'DBSCAN Clustering',
                    'Isolation Forest Anomaly Detection',
                    'PCA Dimensionality Reduction',
                    'Correlation Analysis'
                ]
            },
            'discovered_patterns': [asdict(p) for p in self.patterns],
            'recommendations': self._generate_recommendations()
        }
        
        return report
    
    def _generate_recommendations(self) -> List[str]:
        """Generate actionable recommendations from patterns"""
        
        recommendations = [
            "Investigate anomalous configurations in detail - they may reveal novel geometric regimes",
            "Focus optimization efforts on identified cluster centers for robust solutions",
            "Leverage strong feature correlations to reduce parameter search space",
            "Explore configurations at principal component extremes for maximal diversity",
            "Validate high-confidence patterns with analytical geometric proofs"
        ]
        
        return recommendations


def main():
    """Run ML pattern discovery"""
    
    print("="*80)
    print("MACHINE LEARNING PATTERN DISCOVERY")
    print("="*80)
    
    ml_discovery = MLPatternDiscovery()
    report = ml_discovery.analyze_exploration_results()
    
    if report:
        print(f"\n{report['ml_analysis_summary']['total_patterns_discovered']} patterns discovered")
        print(f"{report['ml_analysis_summary']['high_confidence_patterns']} high-confidence patterns")
        
        print("\n" + "="*80)
        print("TOP DISCOVERED PATTERNS")
        print("="*80)
        
        for i, pattern in enumerate(ml_discovery.patterns[:5], 1):
            print(f"\n{i}. {pattern.pattern_type}")
            print(f"   Confidence: {pattern.confidence:.2f}")
            print(f"   {pattern.description}")
            print(f"   Significance: {pattern.potential_significance}")
        
        print("\n" + "="*80)
        print("RECOMMENDATIONS")
        print("="*80)
        
        for i, rec in enumerate(report['recommendations'], 1):
            print(f"{i}. {rec}")
    else:
        print("\nNo exploration results found. Run auto_explorer.py first.")
    
    print("\n" + "="*80)


if __name__ == '__main__':
    main()
