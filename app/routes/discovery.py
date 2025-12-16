
from flask import Blueprint, jsonify, request, render_template, send_file, current_app
import threading
import logging
import json
import io
import os
from datetime import datetime
from pathlib import Path

# App imports
from app.extensions import (
    discovery_manager,
    daemon_monitor,
    analysis_cache
)
from app.services.daemon import (
    daemon_status,
    run_autonomous_daemon,
    _discover_angle,
    _generate_discovery_title,
    generate_research_paper,
    convert_markdown_to_pdf
)

from security_middleware import rate_limit

# Setup Blueprint
discovery_bp = Blueprint('discovery', __name__)
logger = logging.getLogger(__name__)

# ============================================================================
# FLASK ROUTES
# ============================================================================

@discovery_bp.route('/discoveries')
def discoveries():
    """Autonomous discoveries dashboard page."""
    return render_template('discoveries.html')


# ============================================================================
# AUTONOMOUS DISCOVERY API ENDPOINTS
# ============================================================================

@discovery_bp.route('/api/discoveries/status')
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
        
        # Add monitor status with fallback
        try:
            monitor_status = daemon_monitor.get_status()
        except Exception as monitor_error:
            logger.warning(f"Could not get monitor status: {monitor_error}")
            monitor_status = {
                'is_running': False,
                'health_score': 0,
                'heartbeat_healthy': False,
                'uptime_seconds': None,
                'statistics': {
                    'total_discoveries': 0,
                    'total_errors': 0,
                    'success_rate': 0
                }
            }
        
        return jsonify({
            'success': True,
            'status': daemon_status,
            'health': monitor_status
        })
    except Exception as e:
        logger.error(f"Error getting discovery status: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e),
            'status': daemon_status,
            'health': {
                'is_running': False,
                'health_score': 0,
                'heartbeat_healthy': False
            }
        }), 500


@discovery_bp.route('/api/daemon/health')
def daemon_health():
    """Get detailed daemon health information."""
    try:
        # Get monitor health
        health = daemon_monitor.get_status()
        
        # Get discovery stats
        stats = discovery_manager.get_stats()
        
        # Count today's discoveries
        today = datetime.utcnow().strftime('%Y-%m-%d')
        date_counts = stats.get('discoveries_by_date', {})
        discoveries_today = date_counts.get(today, 0)
        
        # Get latest discovery info
        latest = stats.get('latest_discovery')
        last_discovery = latest.get('timestamp') if latest else None
        
        return jsonify({
            'success': True,
            'running': daemon_status.get('running', False),
            'discoveries_today': discoveries_today,
            'total_discoveries': stats.get('total_discoveries', 0),
            'last_discovery': last_discovery,
            'health': health,
            'status': daemon_status
        })
    except Exception as e:
        logger.error(f"Error getting daemon health: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'running': False,
            'discoveries_today': 0,
            'total_discoveries': 0,
            'last_discovery': None,
            'error': str(e)
        }), 500


@discovery_bp.route('/api/daemon/metrics')
def daemon_metrics():
    """Get daemon performance metrics."""
    try:
        metrics = daemon_monitor.get_metrics()
        return jsonify({
            'success': True,
            'metrics': metrics
        })
    except Exception as e:
        logger.error(f"Error getting daemon metrics: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@discovery_bp.route('/api/discoveries/latest')
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


@discovery_bp.route('/api/discoveries/all')
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


@discovery_bp.route('/api/discoveries/<discovery_id>')
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


@discovery_bp.route('/api/discoveries/stats')
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


@discovery_bp.route('/api/discoveries/search')
@rate_limit('search')
def search_discoveries():
    """Search discoveries with advanced filtering."""
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


@discovery_bp.route('/api/daemon/trigger', methods=['POST'])
@rate_limit('analyze')
def trigger_discovery():
    """Manually trigger a single discovery (for testing/debugging)."""
    try:
        # Get angle from request or use default
        data = request.get_json() or {}
        angle = float(data.get('angle', 45.0))
        
        logger.info(f"Manual discovery trigger requested for angle={angle}°")
        
        # Run discovery in background thread
        def run_manual_discovery():
            try:
                logger.info(f"Running manual discovery at {angle}°...")
                _discover_angle(angle, 'manual_trigger')
                logger.info(f"Manual discovery at {angle}° completed")
            except Exception as e:
                logger.error(f"Manual discovery failed: {e}", exc_info=True)
        
        discovery_thread = threading.Thread(target=run_manual_discovery, daemon=True)
        discovery_thread.start()
        
        return jsonify({
            'success': True,
            'message': f'Discovery triggered for angle {angle}°',
            'note': 'Check /api/discoveries/latest in a few seconds'
        })
    except Exception as e:
        logger.error(f"Error triggering discovery: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


@discovery_bp.route('/api/daemon/start', methods=['POST'])
def start_daemon():
    """Manually start the autonomous daemon (if not running)."""
    global daemon_status
    # Note: daemon_status is imported from service, so it refers to that object.
    # But 'global' here refers to module level variable?
    # No, we imported 'daemon_status' from app.services.daemon.
    # We should use it directly. 
    # But wait, lines 80-87 in origin function used 'global daemon_status'.
    # Here, 'daemon_status' is a name in local scope (imported).
    
    try:
        if daemon_status['running']:
            return jsonify({
                'success': False,
                'error': 'Daemon already running',
                'status': daemon_status
            }), 400
        
        logger.info("Manual daemon start requested...")
        daemon_thread = threading.Thread(target=run_autonomous_daemon, daemon=True)
        daemon_thread.start()
        
        return jsonify({
            'success': True,
            'message': 'Daemon started',
            'note': 'Check /api/daemon/health for status'
        })
    except Exception as e:
        logger.error(f"Error starting daemon: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


@discovery_bp.route('/api/discoveries/regenerate-titles', methods=['POST'])
def regenerate_all_titles():
    """Regenerate titles for all existing discoveries (admin endpoint)."""
    try:
        all_discoveries = discovery_manager.get_all(limit=10000)
        updated_count = 0
        
        for disc_summary in all_discoveries.get('discoveries', []):
            disc = discovery_manager.get_by_id(disc_summary['id'])
            if disc and 'data' in disc:
                # Generate new title
                title = _generate_discovery_title(disc)
                disc['data']['title'] = title
                
                # Re-save the discovery file
                date = disc.get('date', datetime.utcnow().strftime('%Y-%m-%d'))
                date_dir = discovery_manager.base_dir / date
                json_file = date_dir / f"{disc['id']}.json"
                
                if json_file.exists():
                    discovery_manager._save_json(json_file, disc)
                    updated_count += 1
        
        logger.info(f"Regenerated titles for {updated_count} discoveries")
        return jsonify({
            'success': True,
            'updated': updated_count,
            'message': f'Successfully regenerated {updated_count} titles'
        })
    except Exception as e:
        logger.error(f"Error regenerating titles: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


@discovery_bp.route('/api/discoveries/exceptional')
def get_exceptional_discoveries():
    """Get discoveries with exceptional patterns (golden ratio, high complexity, etc.)."""
    try:
        # Get all discoveries
        all_discoveries = discovery_manager.get_all(limit=1000)
        exceptional = []
        
        for disc in all_discoveries.get('discoveries', []):
            disc_data = discovery_manager.get_by_id(disc['id'])
            if disc_data and 'data' in disc_data:
                summary = disc_data['data'].get('summary', {})
                # Check for exceptional markers
                if summary.get('exceptional') or \
                   summary.get('golden_ratio_candidates', 0) > 2 or \
                   summary.get('unique_points', 0) > 40:
                    exceptional.append(disc)
        
        return jsonify({
            'success': True,
            'count': len(exceptional),
            'discoveries': exceptional
        })
    except Exception as e:
        logger.error(f"Error getting exceptional discoveries: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@discovery_bp.route('/api/discoveries/by-type/<discovery_type>')
def get_discoveries_by_type(discovery_type):
    """Get discoveries filtered by type."""
    try:
        all_discoveries = discovery_manager.get_all(limit=1000)
        filtered = [d for d in all_discoveries.get('discoveries', []) 
                   if d.get('type') == discovery_type]
        
        return jsonify({
            'success': True,
            'type': discovery_type,
            'count': len(filtered),
            'discoveries': filtered
        })
    except Exception as e:
        logger.error(f"Error getting discoveries by type: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@discovery_bp.route('/api/discoveries/analysis-summary')
def get_analysis_summary():
    """Get aggregate analysis across all discoveries."""
    try:
        all_discoveries = discovery_manager.get_all(limit=1000)
        
        total_golden_ratio = 0
        max_unique_points = 0
        discovery_types = {}
        angle_distribution = {}
        
        for disc in all_discoveries.get('discoveries', []):
            disc_data = discovery_manager.get_by_id(disc['id'])
            if disc_data and 'data' in disc_data:
                summary = disc_data['data'].get('summary', {})
                
                # Aggregate metrics
                total_golden_ratio += summary.get('golden_ratio_candidates', 0)
                max_unique_points = max(max_unique_points, summary.get('unique_points', 0))
                
                # Count by type
                dtype = disc.get('type', 'unknown')
                discovery_types[dtype] = discovery_types.get(dtype, 0) + 1
                
                # Angle distribution
                angle = disc_data['data'].get('angle')
                if angle:
                    angle_key = str(int(angle))
                    angle_distribution[angle_key] = angle_distribution.get(angle_key, 0) + 1
        
        return jsonify({
            'success': True,
            'summary': {
                'total_discoveries': all_discoveries.get('total', 0),
                'total_golden_ratio_candidates': total_golden_ratio,
                'max_unique_points_found': max_unique_points,
                'discovery_types': discovery_types,
                'angle_distribution': angle_distribution,
                'most_tested_angle': max(angle_distribution.items(), key=lambda x: x[1])[0] if angle_distribution else None
            }
        })
    except Exception as e:
        logger.error(f"Error getting analysis summary: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@discovery_bp.route('/api/discoveries/download/<discovery_id>')
def download_discovery(discovery_id):
    """Download a discovery as JSON (no rate limit for downloads)."""
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


@discovery_bp.route('/api/discoveries/<discovery_id>/paper')
def get_discovery_paper(discovery_id):
    """Generate and download research paper for a discovery (PDF format)."""
    try:
        logger.info(f"Fetching discovery for PDF: {discovery_id}")
        discovery = discovery_manager.get_by_id(discovery_id)
        
        if not discovery:
            logger.error(f"Discovery not found: {discovery_id}")
            return jsonify({'error': 'Discovery not found'}), 404
        
        logger.info(f"Generating PDF for discovery: {discovery_id}")
        # Generate research paper markdown
        paper_markdown = generate_research_paper(discovery)
        
        # Convert to PDF
        pdf_bytes = convert_markdown_to_pdf(paper_markdown, discovery_id)
        
        pdf_buffer = io.BytesIO(pdf_bytes)
        pdf_buffer.seek(0)
        
        filename = f"research_paper_{discovery_id}.pdf"
        
        return send_file(
            pdf_buffer,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=filename
        )
    except Exception as e:
        logger.error(f"Error generating PDF paper for {discovery_id}: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@discovery_bp.route('/api/discoveries/<discovery_id>/paper/markdown')
def get_discovery_paper_markdown(discovery_id):
    """Generate and download research paper for a discovery (Markdown format)."""
    try:
        discovery = discovery_manager.get_by_id(discovery_id)
        if not discovery:
            return jsonify({'error': 'Discovery not found'}), 404
        
        # Generate research paper
        paper = generate_research_paper(discovery)
        paper_bytes = io.BytesIO(paper.encode('utf-8'))
        
        filename = f"research_paper_{discovery_id}.md"
        
        return send_file(
            paper_bytes,
            mimetype='text/markdown',
            as_attachment=True,
            download_name=filename
        )
    except Exception as e:
        logger.error(f"Error generating markdown paper for {discovery_id}: {e}")
        return jsonify({'error': str(e)}), 500
