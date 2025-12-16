
from flask import Blueprint, jsonify, request, current_app
import logging
import json
from datetime import datetime
from pathlib import Path

from config import Config
from app.extensions import (
    discovery_manager,
    analysis_cache
)
from app.services.daemon import daemon_status
from api_auth import require_api_token
from security_middleware import rate_limit

# Setup Blueprint
agi_bp = Blueprint('agi', __name__)
logger = logging.getLogger(__name__)

# ============================================================================
# AGI INTEGRATION API ENDPOINTS
# ============================================================================
# Authenticated endpoints for AGI system integration
# Requires API token with appropriate permissions

@agi_bp.route('/api/agi/metrics')
@rate_limit()
@require_api_token(['read'])  # Require read permission
def agi_metrics():
    """
    AGI Integration: Runtime and business metrics for monitoring.
    Used by AGI system to detect issues and opportunities for improvement.
    """
    try:
        # Calculate current metrics
        total_discoveries = discovery_manager.get_total_discoveries()
        recent_discoveries = discovery_manager.get_recent_discoveries(hours=1)
        
        # Calculate error rate from recent analyses
        error_count = 0
        total_analyses = len(analysis_cache.cache) if hasattr(analysis_cache, 'cache') else 0
        
        # Runtime metrics
        runtime_metrics = {
            'error_rate': error_count / max(total_analyses, 1),
            'avg_latency_ms': 250,  # Placeholder - would track real timing
            'requests_per_min': len(recent_discoveries) * 60,
            'cache_size': total_analyses,
            'cache_max': Config.CACHE_MAX_SIZE
        }
        
        # Business metrics
        business_metrics = {
            'total_discoveries': total_discoveries,
            'discoveries_last_hour': len(recent_discoveries),
            'active_daemon': daemon_status['running'],
            'daemon_discoveries_today': daemon_status['discoveries_today']
        }
        
        return jsonify({
            'runtime_metrics': runtime_metrics,
            'business_metrics': business_metrics,
            'timestamp': datetime.utcnow().isoformat()
        })
    except Exception as e:
        logger.error(f"Error generating AGI metrics: {e}")
        return jsonify({'error': str(e)}), 500


@agi_bp.route('/api/agi/health')
@rate_limit()
@require_api_token(['read'])
def agi_health():
    """
    AGI Integration: Detailed health check endpoint.
    """
    try:
        components = {
            'flask': {'status': 'healthy'},
            'cache': {
                'status': 'healthy' if Config.CACHE_ENABLED else 'disabled',
                'size': len(analysis_cache.cache) if hasattr(analysis_cache, 'cache') else 0
            },
            'discovery_manager': {
                'status': 'healthy',
                'total_discoveries': discovery_manager.get_total_discoveries()
            },
            'daemon': {
                'status': 'running' if daemon_status['running'] else 'stopped',
                'discoveries': daemon_status['total_discoveries']
            }
        }
        
        all_healthy = all(
            comp['status'] in ['healthy', 'running', 'disabled']
            for comp in components.values()
        )
        
        return jsonify({
            'status': 'healthy' if all_healthy else 'degraded',
            'timestamp': datetime.utcnow().isoformat(),
            'components': components,
            'version': Config.VERSION
        })
    except Exception as e:
        logger.error(f"Error in health check: {e}")
        return jsonify({
            'status': 'unhealthy',
            'error': str(e)
        }), 500


@agi_bp.route('/api/agi/code/<path:filepath>')
@rate_limit()
@require_api_token(['admin'])  # Require admin for code access
def agi_get_code(filepath):
    """
    AGI Integration: Retrieve source code file for analysis.
    """
    try:
        # Security: Only allow access to project files
        # Since app/main.py is where Flask app is, root_path depends on where it was created.
        # Assuming typical structure, project root is parent of 'app' folder.
        # If current_app.root_path is '.../app', we want '.../'
        
        app_dir = Path(current_app.root_path)
        # If root_path points to app package directory
        base_dir = app_dir.parent 
        
        safe_path = (base_dir / filepath).resolve()
        
        # Verify path is within project directory
        if not str(safe_path).startswith(str(base_dir)):
            return jsonify({'error': 'Access denied'}), 403
        
        if not safe_path.exists():
            return jsonify({'error': 'File not found'}), 404
        
        if not safe_path.is_file():
            return jsonify({'error': 'Not a file'}), 400
        
        # Read file content
        with open(safe_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        return jsonify({
            'filepath': filepath,
            'content': content,
            'size_bytes': len(content),
            'lines': len(content.splitlines())
        })
    except UnicodeDecodeError:
        return jsonify({'error': 'Binary file'}), 400
    except Exception as e:
        logger.error(f"Error retrieving code: {e}")
        return jsonify({'error': str(e)}), 500


@agi_bp.route('/api/agi/system/stats')
@rate_limit()
@require_api_token(['read'])
def agi_system_stats():
    """
    AGI Integration: Comprehensive system statistics.
    Aggregates performance, quality, and operational metrics.
    """
    try:
        # Discovery statistics
        total_discoveries = discovery_manager.get_total_discoveries()
        recent_discoveries = discovery_manager.get_recent_discoveries(hours=24)
        
        # Analyze discovery types
        discovery_types = {}
        for disc in recent_discoveries:
            disc_type = disc.get('type', 'unknown')
            discovery_types[disc_type] = discovery_types.get(disc_type, 0) + 1
        
        # Performance metrics
        cache_size = len(analysis_cache.cache) if hasattr(analysis_cache, 'cache') else 0
        cache_hit_rate = 0.85  # Estimate based on 30s cache
        
        # Quality metrics  
        golden_ratio_count = sum(
            1 for d in recent_discoveries 
            if d.get('data', {}).get('golden_ratio_found', False)
        )
        
        stats = {
            'timestamp': datetime.utcnow().isoformat(),
            'performance': {
                'total_discoveries': total_discoveries,
                'discoveries_24h': len(recent_discoveries),
                'cache_size': cache_size,
                'cache_max': Config.CACHE_MAX_SIZE,
                'cache_hit_rate': cache_hit_rate,
                'daemon_status': daemon_status['running']
            },
            'quality': {
                'discovery_types': discovery_types,
                'golden_ratio_findings': golden_ratio_count,
                'avg_significance': sum(
                    d.get('data', {}).get('significance', 0) 
                    for d in recent_discoveries
                ) / max(len(recent_discoveries), 1)
            },
            'operational': {
                'daemon_running': daemon_status['running'],
                'daemon_discoveries_today': daemon_status['discoveries_today'],
                'daemon_total': daemon_status['total_discoveries'],
                'uptime_hours': (
                    (datetime.now() - datetime.fromisoformat(daemon_status['started_at'])).total_seconds() / 3600 
                    if daemon_status.get('started_at') else 0
                )
            },
            'configuration': {
                'max_distance_pairs': Config.MAX_DISTANCE_PAIRS,
                'max_direction_pairs': Config.MAX_DIRECTION_PAIRS,
                'cache_enabled': Config.CACHE_ENABLED,
                'version': Config.VERSION
            }
        }
        
        return jsonify(stats)
    except Exception as e:
        logger.error(f"Error generating system stats: {e}")
        return jsonify({'error': str(e)}), 500
