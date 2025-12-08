#!/usr/bin/env python3
"""
Pytest configuration and fixtures for Orion Octave Cubes tests
"""

import pytest
import json
import tempfile
from pathlib import Path
from typing import Dict, Any

# Import main application for testing
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from app import app as flask_app
from config import TestingConfig
import orion_octave_test


@pytest.fixture
def app():
    """Create and configure a test Flask application instance."""
    flask_app.config.from_object(TestingConfig)
    
    # Create a test client
    with flask_app.app_context():
        yield flask_app


@pytest.fixture
def client(app):
    """Fixture for test client."""
    return app.test_client()


@pytest.fixture
def runner(app):
    """Fixture for CLI runner."""
    return app.test_cli_runner()


@pytest.fixture
def sample_analysis_params() -> Dict[str, Any]:
    """Sample parameters for geometry analysis."""
    return {
        'side': 2.0,
        'angle': 30.0,
        'max_distance_pairs': 1000,
        'max_direction_pairs': 500
    }


@pytest.fixture
def sample_analysis_result(sample_analysis_params) -> Dict[str, Any]:
    """Run a sample analysis and return results."""
    return orion_octave_test.main(
        side=sample_analysis_params['side'],
        angle=sample_analysis_params['angle'],
        max_distance_pairs=sample_analysis_params['max_distance_pairs'],
        max_direction_pairs=sample_analysis_params['max_direction_pairs'],
        verbose=False
    )


@pytest.fixture
def temp_output_dir(tmp_path):
    """Create a temporary directory for test outputs."""
    output_dir = tmp_path / "test_outputs"
    output_dir.mkdir()
    return output_dir


@pytest.fixture
def mock_discovery_data() -> Dict[str, Any]:
    """Mock discovery data for testing."""
    return {
        'id': 'test_discovery_001',
        'timestamp': '2024-01-01T12:00:00Z',
        'type': 'angle_sweep',
        'data': {
            'title': 'Test Discovery',
            'summary': {
                'angle': 45.0,
                'unique_points': 32,
                'golden_ratio_candidates': 2,
                'special_angles': {
                    '36.0': 10,
                    '60.0': 15
                }
            },
            'configuration': {
                'side_length': 2.0,
                'rotation_angle_degrees': 45.0
            }
        }
    }


@pytest.fixture(autouse=True)
def reset_caches(app):
    """Reset application caches before each test."""
    with app.app_context():
        # Clear any cached data
        from app import analysis_cache
        analysis_cache.cache.clear()
    
    yield
    
    # Cleanup after test
    with app.app_context():
        analysis_cache.cache.clear()


@pytest.fixture
def api_headers():
    """Standard headers for API requests."""
    return {
        'Content-Type': 'application/json',
        'Accept': 'application/json'
    }
