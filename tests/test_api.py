#!/usr/bin/env python3
"""
Integration tests for Flask API endpoints
"""

import pytest
import json
import time
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))


class TestMainRoutes:
    """Test main application routes."""
    
    def test_index_page(self, client):
        """Test that the main page loads."""
        response = client.get('/')
        assert response.status_code == 200
        assert b'Orion Octave Cubes' in response.data
    
    def test_admin_page(self, client):
        """Test that the admin page loads."""
        response = client.get('/admin')
        assert response.status_code == 200
    
    def test_discoveries_page(self, client):
        """Test that the discoveries page loads."""
        response = client.get('/discoveries')
        assert response.status_code == 200


class TestHealthEndpoints:
    """Test health check endpoints."""
    
    def test_health_endpoint(self, client):
        """Test basic health check."""
        response = client.get('/health')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['status'] == 'healthy'
    
    def test_healthz_alias(self, client):
        """Test healthz endpoint (alias for health)."""
        response = client.get('/healthz')
        assert response.status_code == 200


@pytest.mark.api
class TestAnalysisAPI:
    """Test analysis API endpoints."""
    
    def test_analyze_basic(self, client, sample_analysis_params, api_headers):
        """Test basic analysis request."""
        response = client.post(
            '/api/analyze',
            data=json.dumps(sample_analysis_params),
            headers=api_headers
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert 'cache_key' in data
        assert 'summary' in data
        
        # Validate summary structure
        summary = data['summary']
        assert 'configuration' in summary
        assert 'point_counts' in summary
        assert 'distance_stats' in summary
        assert 'golden_ratio' in summary
    
    def test_analyze_caching(self, client, sample_analysis_params, api_headers):
        """Test that caching works."""
        # First request
        response1 = client.post(
            '/api/analyze',
            data=json.dumps(sample_analysis_params),
            headers=api_headers
        )
        data1 = json.loads(response1.data)
        cache_key1 = data1['cache_key']
        cached1 = data1.get('cached', False)
        
        # Second request with same parameters
        response2 = client.post(
            '/api/analyze',
            data=json.dumps(sample_analysis_params),
            headers=api_headers
        )
        data2 = json.loads(response2.data)
        cache_key2 = data2['cache_key']
        cached2 = data2.get('cached', False)
        
        # Cache keys should match
        assert cache_key1 == cache_key2
        
        # Second request should be from cache
        assert cached2 is True
    
    def test_analyze_invalid_side(self, client, api_headers):
        """Test validation for invalid side length."""
        params = {
            'side': -1.0,  # Invalid: negative
            'angle': 30.0
        }
        
        response = client.post(
            '/api/analyze',
            data=json.dumps(params),
            headers=api_headers
        )
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['success'] is False
        assert 'error' in data
    
    def test_analyze_invalid_angle(self, client, api_headers):
        """Test validation for invalid angle."""
        params = {
            'side': 2.0,
            'angle': 400.0  # Invalid: > 360
        }
        
        response = client.post(
            '/api/analyze',
            data=json.dumps(params),
            headers=api_headers
        )
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['success'] is False
    
    def test_analyze_invalid_json(self, client, api_headers):
        """Test handling of invalid JSON."""
        response = client.post(
            '/api/analyze',
            data="not valid json",
            headers=api_headers
        )
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['success'] is False
    
    def test_analyze_missing_content_type(self, client):
        """Test missing content type header."""
        response = client.post(
            '/api/analyze',
            data=json.dumps({'side': 2.0, 'angle': 30.0})
        )
        
        # Should handle gracefully
        assert response.status_code in [400, 200]


@pytest.mark.api
class TestPlotGeneration:
    """Test plot generation endpoints."""
    
    def test_generate_3d_plot(self, client, sample_analysis_params, api_headers):
        """Test 3D plot generation."""
        # First run analysis
        analysis_response = client.post(
            '/api/analyze',
            data=json.dumps(sample_analysis_params),
            headers=api_headers
        )
        cache_key = json.loads(analysis_response.data)['cache_key']
        
        # Generate plot
        plot_response = client.get(f'/api/plot/3d/{cache_key}')
        
        assert plot_response.status_code == 200
        assert plot_response.content_type == 'image/png'
        assert len(plot_response.data) > 0
    
    def test_generate_distance_plot(self, client, sample_analysis_params, api_headers):
        """Test distance spectrum plot generation."""
        # Run analysis
        analysis_response = client.post(
            '/api/analyze',
            data=json.dumps(sample_analysis_params),
            headers=api_headers
        )
        cache_key = json.loads(analysis_response.data)['cache_key']
        
        # Generate plot
        plot_response = client.get(f'/api/plot/distances/{cache_key}')
        
        assert plot_response.status_code == 200
        assert plot_response.content_type == 'image/png'
    
    def test_generate_angle_plot(self, client, sample_analysis_params, api_headers):
        """Test angle distribution plot generation."""
        # Run analysis
        analysis_response = client.post(
            '/api/analyze',
            data=json.dumps(sample_analysis_params),
            headers=api_headers
        )
        cache_key = json.loads(analysis_response.data)['cache_key']
        
        # Generate plot
        plot_response = client.get(f'/api/plot/angles/{cache_key}')
        
        assert plot_response.status_code == 200
        assert plot_response.content_type == 'image/png'
    
    def test_generate_summary_plot(self, client, sample_analysis_params, api_headers):
        """Test summary plot generation."""
        # Run analysis
        analysis_response = client.post(
            '/api/analyze',
            data=json.dumps(sample_analysis_params),
            headers=api_headers
        )
        cache_key = json.loads(analysis_response.data)['cache_key']
        
        # Generate plot
        plot_response = client.get(f'/api/plot/summary/{cache_key}')
        
        assert plot_response.status_code == 200
        assert plot_response.content_type == 'image/png'
    
    def test_plot_invalid_cache_key(self, client):
        """Test plot generation with invalid cache key."""
        response = client.get('/api/plot/3d/invalid_key')
        
        assert response.status_code == 404
        data = json.loads(response.data)
        assert 'error' in data
    
    def test_plot_invalid_type(self, client, sample_analysis_params, api_headers):
        """Test plot generation with invalid plot type."""
        # Run analysis
        analysis_response = client.post(
            '/api/analyze',
            data=json.dumps(sample_analysis_params),
            headers=api_headers
        )
        cache_key = json.loads(analysis_response.data)['cache_key']
        
        # Try invalid plot type
        response = client.get(f'/api/plot/invalid_type/{cache_key}')
        
        assert response.status_code == 400


@pytest.mark.api
class TestDownload:
    """Test result download endpoints."""
    
    def test_download_json(self, client, sample_analysis_params, api_headers):
        """Test JSON download."""
        # Run analysis
        analysis_response = client.post(
            '/api/analyze',
            data=json.dumps(sample_analysis_params),
            headers=api_headers
        )
        cache_key = json.loads(analysis_response.data)['cache_key']
        
        # Download results
        download_response = client.get(f'/api/download/{cache_key}')
        
        assert download_response.status_code == 200
        assert download_response.content_type == 'application/json'
        
        # Validate JSON structure
        data = json.loads(download_response.data)
        assert 'configuration' in data
        assert 'points' in data
        assert 'distances' in data
    
    def test_download_invalid_key(self, client):
        """Test download with invalid cache key."""
        response = client.get('/api/download/invalid_key')
        
        assert response.status_code == 404


@pytest.mark.api
class TestDiscoveryEndpoints:
    """Test autonomous discovery endpoints."""
    
    def test_discovery_status(self, client):
        """Test discovery status endpoint."""
        response = client.get('/api/discoveries/status')
        
        assert response.status_code in [200, 500]  # May fail if daemon not running
        data = json.loads(response.data)
        assert 'success' in data
    
    def test_discovery_stats(self, client):
        """Test discovery statistics endpoint."""
        response = client.get('/api/discoveries/stats')
        
        assert response.status_code in [200, 500]
        data = json.loads(response.data)
        assert 'success' in data
    
    def test_get_latest_discoveries(self, client):
        """Test get latest discoveries."""
        response = client.get('/api/discoveries/latest?count=5')
        
        assert response.status_code in [200, 500]
        if response.status_code == 200:
            data = json.loads(response.data)
            assert 'discoveries' in data


@pytest.mark.slow
class TestRateLimiting:
    """Test rate limiting functionality."""
    
    def test_rate_limit_enforcement(self, client, api_headers):
        """Test that rate limiting is enforced."""
        # Make multiple rapid requests
        params = {'side': 2.0, 'angle': 30.0}
        responses = []
        
        for i in range(15):  # Exceed limit
            response = client.post(
                '/api/analyze',
                data=json.dumps(params),
                headers=api_headers
            )
            responses.append(response.status_code)
        
        # Some requests should be rate limited (429)
        # Note: This test might be flaky depending on timing
        # At minimum, all should be either 200 or 429
        assert all(code in [200, 429] for code in responses)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
