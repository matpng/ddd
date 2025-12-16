"""
Integration tests for Flask API endpoints
"""
import pytest
import json


class TestHealthEndpoints:
    """Tests for health check endpoints"""
    
    def test_health_endpoint(self, client):
        """Test /health endpoint returns 200"""
        response = client.get('/health')
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert data['status'] == 'ok'
    
    def test_healthz_endpoint(self, client):
        """Test /healthz alias endpoint"""
        response = client.get('/healthz')
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True


class TestMainRoutes:
    """Tests for main page routes"""
    
    def test_index_page(self, client):
        """Test main dashboard loads"""
        response = client.get('/')
        assert response.status_code == 200
    
    def test_discoveries_page(self, client):
        """Test discoveries page loads"""
        response = client.get('/discoveries')
        assert response.status_code == 200
    
    def test_admin_page(self, client):
        """Test admin page loads"""
        response = client.get('/admin')
        assert response.status_code == 200


class TestAnalysisAPI:
    """Tests for analysis API endpoints"""
    
    def test_analyze_endpoint_success(self, client, sample_analysis_data):
        """Test successful analysis request"""
        response = client.post(
            '/api/analyze',
            data=json.dumps(sample_analysis_data),
            content_type='application/json'
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert 'summary' in data
        assert 'cache_key' in data
    
    def test_analyze_missing_data(self, client):
        """Test analysis with missing data"""
        response = client.post(
            '/api/analyze',
            data=json.dumps({}),
            content_type='application/json'
        )
        
        # Should use defaults and succeed or return 400
        assert response.status_code in [200, 400]
    
    def test_analyze_invalid_side(self, client):
        """Test analysis with invalid side length"""
        response = client.post(
            '/api/analyze',
            data=json.dumps({
                'side': -5.0,  # Invalid
                'angle': 30.0
            }),
            content_type='application/json'
        )
        
        assert response.status_code == 400
        data = response.get_json()
        assert data['success'] is False
        assert 'error' in data
    
    def test_analyze_invalid_angle(self, client):
        """Test analysis with invalid angle"""
        response = client.post(
            '/api/analyze',
            data=json.dumps({
                'side': 2.0,
                'angle': 500.0  # Invalid
            }),
            content_type='application/json'
        )
        
        assert response.status_code == 400
        data = response.get_json()
        assert data['success'] is False
    
    def test_analyze_invalid_json(self, client):
        """Test analysis with invalid JSON"""
        response = client.post(
            '/api/analyze',
            data='invalid json',
            content_type='application/json'
        )
        
        assert response.status_code == 400
        data = response.get_json()
        assert data['success'] is False
    
    def test_analyze_caching(self, client, sample_analysis_data):
        """Test that identical requests use cache"""
        # First request
        response1 = client.post(
            '/api/analyze',
            data=json.dumps(sample_analysis_data),
            content_type='application/json'
        )
        data1 = response1.get_json()
        
        # Second identical request
        response2 = client.post(
            '/api/analyze',
            data=json.dumps(sample_analysis_data),
            content_type='application/json'
        )
        data2 = response2.get_json()
        
        # Both should succeed
        assert response1.status_code == 200
        assert response2.status_code == 200
        
        # Cache keys should match
        assert data1['cache_key'] == data2['cache_key']


class TestDiscoveryAPI:
    """Tests for discovery API endpoints"""
    
    def test_discovery_status(self, client):
        """Test discovery status endpoint"""
        response = client.get('/api/discoveries/status')
        assert response.status_code == 200
        data = response.get_json()
        assert 'running' in data
        assert 'total_discoveries' in data
    
    def test_discovery_latest(self, client):
        """Test latest discoveries endpoint"""
        response = client.get('/api/discoveries/latest')
        assert response.status_code == 200
        data = response.get_json()
        assert isinstance(data, list)
    
    def test_discovery_all(self, client):
        """Test all discoveries endpoint"""
        response = client.get('/api/discoveries/all')
        assert response.status_code == 200
        data = response.get_json()
        assert 'discoveries' in data
        assert 'total' in data
    
    def test_discovery_stats(self, client):
        """Test discovery statistics endpoint"""
        response = client.get('/api/discoveries/stats')
        assert response.status_code == 200
        data = response.get_json()
        assert 'total_discoveries' in data


class TestDaemonAPI:
    """Tests for daemon control endpoints"""
    
    def test_daemon_health(self, client):
        """Test daemon health endpoint"""
        response = client.get('/api/daemon/health')
        assert response.status_code == 200
        data = response.get_json()
        assert 'status' in data
    
    def test_daemon_metrics(self, client):
        """Test daemon metrics endpoint"""
        response = client.get('/api/daemon/metrics')
        assert response.status_code == 200
        data = response.get_json()
        assert isinstance(data, dict)


class TestMLAPI:
    """Tests for ML API endpoints"""
    
    def test_ml_status(self, client):
        """Test ML status endpoint"""
        response = client.get('/api/ml/status')
        assert response.status_code == 200
        data = response.get_json()
        assert 'enabled' in data or 'status' in data


class TestErrorHandling:
    """Tests for error handling"""
    
    def test_404_on_invalid_route(self, client):
        """Test 404 on non-existent route"""
        response = client.get('/nonexistent/route')
        assert response.status_code == 404
    
    def test_405_on_wrong_method(self, client):
        """Test 405 on wrong HTTP method"""
        response = client.get('/api/analyze')  # POST only
        assert response.status_code == 405
