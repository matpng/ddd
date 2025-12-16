# Test Suite Structure

## Overview
This directory contains comprehensive tests for the Orion Octave Cubes application.

## Structure
```
tests/
├── unit/                    # Unit tests (isolated function tests)
│   ├── test_analysis.py    # Core analysis functions
│   ├── test_cache.py       # LRU cache logic
│   ├── test_config.py      # Configuration validation
│   ├── test_pak_database.py # PAK database operations
│   └── test_pak_agents.py  # Goal/Value engines
├── integration/             # Integration tests (multiple components)
│   ├── test_api_endpoints.py  # All API routes
│   ├── test_daemon.py       # Daemon functionality
│   └── test_discovery_flow.py # Discovery workflow
├── e2e/                     # End-to-end tests
│   └── test_full_workflow.py # Complete user journeys
├── fixtures/                # Test data and fixtures
│   ├── sample_discoveries/ 
│   └── test_data.json
└── conftest.py             # Pytest configuration and fixtures

## Running Tests

### All tests
```bash
pytest
```

### Specific test file
```bash
pytest tests/unit/test_analysis.py
```

### With coverage
```bash
pytest --cov=. --cov-report=html
```

### Specific test
```bash
pytest tests/unit/test_analysis.py::test_distance_calculation
```

## Writing Tests

### Unit Test Example
```python
def test_cache_set_and_get():
    cache = LRUCache(max_size=2)
    cache.set("key1", "value1")
    assert cache.get("key1") == "value1"
```

### Integration Test Example
```python
def test_api_analyze_endpoint(client):
    response = client.post('/api/analyze', json={
        'side': 2.0,
        'angle': 30.0
    })
    assert response.status_code == 200
    assert 'success' in response.json
```

## Test Coverage Goals
- **Unit Tests:** 80%+ coverage
- **Integration Tests:** All API endpoints
- **E2E Tests:** Critical user flows

## CI/CD Integration
Tests run automatically on:
- Every push to `main` or `develop`
- Every pull request
- Pre-deployment checks
