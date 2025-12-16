from flask import Blueprint, jsonify, request, send_file
import json
import io
import logging
from config import Config
from app.extensions import analysis_cache
from app.services.plotting import (
    create_3d_plot,
    create_distance_plot,
    create_angle_plot,
    create_summary_plot
)
from orion_octave_test import main as run_analysis
from security_middleware import rate_limit, validate_request

# Configure logger
logger = logging.getLogger(__name__)

analysis_bp = Blueprint('analysis', __name__)

@analysis_bp.route('/api/analyze', methods=['POST'])
@rate_limit('analyze')
@validate_request(max_payload_kb=50)
def analyze():
    """Run geometric analysis with provided parameters."""
    try:
        # Parse JSON with error handling
        try:
            data = request.get_json()
        except Exception as json_error:
            return jsonify({
                'error': 'Invalid JSON format',
                'success': False
            }), 400
        
        if data is None:
            return jsonify({
                'error': 'Empty request body or invalid content type',
                'success': False
            }), 400
        
        # Extract and validate parameter types
        try:
            side = float(data.get('side', Config.DEFAULT_SIDE))
            angle = float(data.get('angle', Config.DEFAULT_ANGLE))
            max_distance_pairs = int(data.get('max_distance_pairs', Config.DEFAULT_DISTANCE_PAIRS))
            max_direction_pairs = int(data.get('max_direction_pairs', Config.DEFAULT_DIRECTION_PAIRS))
        except (ValueError, TypeError) as e:
            return jsonify({
                'error': f'Invalid parameter type: {str(e)}',
                'success': False
            }), 400
        
        # Validate input ranges with config-based limits
        if not (Config.MIN_SIDE_LENGTH < side <= Config.MAX_SIDE_LENGTH):
            return jsonify({
                'error': f'Side length must be between {Config.MIN_SIDE_LENGTH} and {Config.MAX_SIDE_LENGTH}',
                'success': False
            }), 400
        if not (Config.MIN_ANGLE <= angle <= Config.MAX_ANGLE):
            return jsonify({
                'error': f'Angle must be between {Config.MIN_ANGLE} and {Config.MAX_ANGLE} degrees',
                'success': False
            }), 400
        if max_distance_pairs <= 0 or max_distance_pairs > Config.MAX_DISTANCE_PAIRS:
            return jsonify({
                'error': f'max_distance_pairs must be between 1 and {Config.MAX_DISTANCE_PAIRS}',
                'success': False
            }), 400
        if max_direction_pairs <= 0 or max_direction_pairs > Config.MAX_DIRECTION_PAIRS:
            return jsonify({
                'error': f'max_direction_pairs must be between 1 and {Config.MAX_DIRECTION_PAIRS}',
                'success': False
            }), 400
        
        # Generate cache key
        cache_key = f"{side}_{angle}_{max_distance_pairs}_{max_direction_pairs}"
        
        # Check cache if enabled
        if Config.CACHE_ENABLED and cache_key in analysis_cache:
            logger.info(f"Cache hit for {cache_key}")
            results = analysis_cache[cache_key]
            cached = True
        else:
            # Run analysis
            logger.info(f"Running analysis: side={side}, angle={angle}")
            results = run_analysis(
                side=side,
                angle=angle,
                max_distance_pairs=max_distance_pairs,
                max_direction_pairs=max_direction_pairs,
                verbose=False
            )
            
            # Store in cache if enabled
            if Config.CACHE_ENABLED:
                analysis_cache[cache_key] = results
            cached = False
        
        # Return comprehensive summary
        return jsonify({
            'success': True,
            'cache_key': cache_key,
            'cached': cached,
            'summary': {
                'configuration': results['configuration'],
                'point_counts': results['point_counts'],
                'distance_stats': results['distances']['statistics'],
                'golden_ratio': results['golden_ratio'],
                'direction_count': results['directions']['unique_count'],
                'angle_count': results['angles']['distinct_count'],
                'special_angles': results['special_angles'],
                'icosahedral_check': results['icosahedral_check']
            }
        })
        
    except ValueError as e:
        logger.error(f'ValueError: {str(e)}')
        return jsonify({
            'error': f'Invalid input value: {str(e)}',
            'success': False
        }), 400
    except KeyError as e:
        logger.error(f'KeyError: {str(e)}')
        return jsonify({
            'error': f'Missing required data: {str(e)}',
            'success': False
        }), 400
    except Exception as e:
        logger.error(f'Unexpected error: {str(e)}', exc_info=True)
        return jsonify({
            'error': 'Internal server error',
            'success': False,
            'details': str(e) if Config.DEBUG else None
        }), 500


@analysis_bp.route('/api/plot/<plot_type>/<cache_key>')
def generate_plot(plot_type, cache_key):
    """Generate plots on demand."""
    try:
        if cache_key not in analysis_cache:
            return jsonify({'error': 'Analysis not found. Please run analysis first.'}), 404
        
        results = analysis_cache[cache_key]
        
        if plot_type == '3d':
            img = create_3d_plot(results)
        elif plot_type == 'distances':
            img = create_distance_plot(results)
        elif plot_type == 'angles':
            img = create_angle_plot(results)
        elif plot_type == 'summary':
            img = create_summary_plot(results)
        else:
            return jsonify({'error': f'Invalid plot type: {plot_type}. Valid types: 3d, distances, angles, summary'}), 400
        
        return send_file(img, mimetype='image/png')
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@analysis_bp.route('/api/download/<cache_key>')
@rate_limit('download')
def download_results(cache_key):
    """Download results as JSON."""
    try:
        if cache_key not in analysis_cache:
            return jsonify({'error': 'Analysis not found'}), 404
        
        results = analysis_cache[cache_key]
        
        # Create JSON file in memory
        json_str = json.dumps(results, indent=2)
        json_bytes = io.BytesIO(json_str.encode('utf-8'))
        
        config = results['configuration']
        filename = f"orion_octave_{config['rotation_angle_degrees']}deg.json"
        
        return send_file(
            json_bytes,
            mimetype='application/json',
            as_attachment=True,
            download_name=filename
        )
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
