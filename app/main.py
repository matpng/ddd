#!/usr/bin/env python3
"""
Orion Octave Cubes - Web Application
A Flask-based web interface for interactive geometric analysis
"""

from flask import Flask, render_template, request, jsonify, send_file
import logging
import os
import threading
import time

# Import our modules
from config import Config
from api_auth import require_api_token  # Enable API authentication
from security_middleware import initialize_security, rate_limit, validate_request
from prometheus_metrics import (
    setup_metrics,
    start_metrics_updater,
    metrics as prometheus_metrics
)
from app.extensions import (
    analysis_cache,
    discovery_manager,
    ml_integration,
    daemon_monitor
)
from app.services.daemon import start_autonomous_daemon

# Setup logging
logging.basicConfig(
    level=getattr(logging, Config.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Suppress matplotlib font manager debug logs
logging.getLogger('matplotlib.font_manager').setLevel(logging.WARNING)

app = Flask(__name__)
app.config.from_object(Config)

# Initialize security middleware
initialize_security(app)

# Initialize Prometheus metrics
setup_metrics(app)

# Register Blueprints
from app.routes.analysis import analysis_bp
from app.routes.discovery import discovery_bp
from app.routes.ml import ml_bp
from app.routes.agi import agi_bp

app.register_blueprint(analysis_bp)
app.register_blueprint(discovery_bp)
app.register_blueprint(ml_bp)
app.register_blueprint(agi_bp)


# ============================================================================
# FLASK ROUTES (Core Pages)
# ============================================================================

@app.route('/')
def index():
    """Main dashboard page."""
    return render_template('index.html')


@app.route('/admin')
def admin():
    """Admin panel for system maintenance."""
    return render_template('admin.html')


@app.route('/health')
def health():
    """Lightweight health endpoint for load balancers and platform health checks."""
    try:
        return jsonify({'success': True, 'status': 'ok'}), 200
    except Exception:
        return jsonify({'success': False}), 500


@app.route('/healthz')
def healthz():
    """Compatibility alias for health checks."""
    return health()


# ============================================================================
# MAIN APPLICATION ENTRY POINT
# ============================================================================

# Start daemon when module is imported (works with gunicorn)
start_autonomous_daemon()

if __name__ == '__main__':
    print("=" * 70)
    print("Orion Octave Cubes - Web Application")
    print("=" * 70)
    
    if Config.DEBUG:
        print("\n⚠️  WARNING: Running in DEBUG mode")
        print("   For production, set FLASK_DEBUG=false")
    
    print(f"\nStarting Flask server...")
    print(f"  Mode: {'DEBUG' if Config.DEBUG else 'PRODUCTION'}")
    print(f"  Host: {Config.HOST}")
    print(f"  Port: {Config.PORT}")
    print(f"\nAccess the dashboard at: http://localhost:{Config.PORT}")
    print("\nPress Ctrl+C to stop the server")
    print("\nEnvironment Variables:")
    print(f"  FLASK_DEBUG={Config.DEBUG}")
    print(f"  FLASK_HOST={Config.HOST}")
    print(f"  FLASK_PORT={Config.PORT}")
    print("=" * 70)
    
    app.run(debug=Config.DEBUG, host=Config.HOST, port=Config.PORT)
