
from flask import Blueprint, jsonify, request
import logging
import json

from app.extensions import ml_integration
from security_middleware import rate_limit, validate_request
from prometheus_metrics import metrics as prometheus_metrics

# Setup Blueprint
ml_bp = Blueprint('ml', __name__)
logger = logging.getLogger(__name__)

# ============================================================================
# MACHINE LEARNING API ENDPOINTS
# ============================================================================

@ml_bp.route('/api/ml/analyze', methods=['POST'])
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


@ml_bp.route('/api/ml/patterns')
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


@ml_bp.route('/api/ml/status')
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
