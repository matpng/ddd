"""
Pytest configuration and shared fixtures
"""
import pytest
import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Set test environment
os.environ['FLASK_ENV'] = 'testing'
os.environ['TESTING'] = 'true'


@pytest.fixture
def app():
    """Create Flask app for testing"""
    from app import app as flask_app
    flask_app.config['TESTING'] = True
    flask_app.config['CACHE_ENABLED'] = False
    yield flask_app


@pytest.fixture
def client(app):
    """Create Flask test client"""
    return app.test_client()


@pytest.fixture
def runner(app):
    """Create Flask CLI runner"""
    return app.test_cli_runner()


@pytest.fixture
def sample_analysis_data():
    """Sample analysis request data"""
    return {
        'side': 2.0,
        'angle': 30.0,
        'max_distance_pairs': 5000,
        'max_direction_pairs': 2000
    }


@pytest.fixture
def sample_discovery():
    """Sample discovery data"""
    return {
        'angle': 45.0,
        'summary': {
            'unique_points': 32,
            'golden_ratio_candidates': 1,
            'unique_distances': 28,
            'special_angles': {
                '36.0': {'count': 120, 'description': 'Pentagon/Icosahedron'},
                '60.0': {'count': 98, 'description': 'Hexagon/Octahedron'},
                '90.0': {'count': 320, 'description': 'Cube/Octahedron'}
            }
        },
        'full_results': {}
    }


@pytest.fixture
def mock_pak_database(tmp_path):
    """Create temporary PAK database for testing"""
    from pak_database import PAKDatabase
    db_path = tmp_path / "test_pak.db"
    db = PAKDatabase(str(db_path))
    yield db
    db.close()


@pytest.fixture(autouse=True)
def reset_caches():
    """Reset all caches between tests"""
    yield
    # Clear any global caches here if needed
