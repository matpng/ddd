# Test Execution Guide

## Running the Test Suite

### Quick Start
```bash
# Install dependencies first
pip install -r requirements.txt

# Run all tests
pytest

# Run with verbose output
pytest -v

# Run with coverage report
pytest --cov=. --cov-report=html

# Open coverage report in browser (after running above)
# Windows:
start htmlcov\index.html
# Linux/Mac:
open htmlcov/index.html
```

### Running Specific Tests

```bash
# Run only geometry tests
pytest tests/test_geometry.py -v

# Run only API tests
pytest tests/test_api.py -v

# Run specific test class
pytest tests/test_geometry.py::TestBasicHelpers -v

# Run specific test function
pytest tests/test_geometry.py::TestBasicHelpers::test_normalize -v

# Run tests matching a pattern
pytest -k "test_validate" -v
```

### Using Test Markers

```bash
# Run only unit tests
pytest -m unit

# Run only integration tests
pytest -m integration

# Run only API tests
pytest -m api

# Skip slow tests
pytest -m "not slow"

# Combine markers
pytest -m "unit and not slow"
```

### Advanced Options

```bash
# Stop on first failure
pytest -x

# Run last failed tests
pytest --lf

# Run in parallel (requires pytest-xdist)
pip install pytest-xdist
pytest -n auto

# Generate XML report for CI
pytest --junitxml=test-results.xml

# Detailed output
pytest -vv --tb=long
```

## Expected Test Results

### Geometry Tests (test_geometry.py)
- ✅ TestBasicHelpers: 5 tests (normalize, rotation, etc.)
- ✅ TestGeometryPrimitives: 6 tests (Cube, Face, Edge)
- ✅ TestIntersections: 4 tests (line-plane, edge-edge)
- ✅ TestAnalysisFunctions: 5 tests (distances, angles, φ)
- ✅ TestEndToEndAnalysis: 3 tests (full pipeline)

**Total: ~23 tests**

### API Tests (test_api.py)
- ✅ TestMainRoutes: 3 tests (pages load)
- ✅ TestHealthEndpoints: 2 tests (health checks)
- ✅ TestAnalysisAPI: 6 tests (validation, caching)
- ✅ TestPlotGeneration: 6 tests (all plot types)
- ✅ TestDownload: 2 tests (JSON download)
- ✅ TestDiscoveryEndpoints: 3 tests (discovery API)
- ✅ TestRateLimiting: 1 test (rate limits)

**Total: ~23 tests**

### Coverage Goals
- **Target**: >80% coverage
- **Core modules**: orion_octave_test.py, app.py
- **Utils**: models/exceptions.py, utils/validation.py

## Troubleshooting

### Common Issues

**1. ModuleNotFoundError**
```bash
# Solution: Ensure you're in the project root
cd c:\Users\fc\Documents\GitHub\ddd
pytest
```

**2. Import errors**
```bash
# Solution: Install all dependencies
pip install -r requirements.txt
```

**3. Flask app not starting in tests**
```bash
# Solution: Check conftest.py is present
ls tests/conftest.py
```

**4. Tests fail due to missing fixtures**
```bash
# Solution: Ensure tests/__init__.py exists
touch tests/__init__.py  # Linux/Mac
type nul > tests\__init__.py  # Windows
```

### Debugging Failed Tests

```bash
# Run with print statements visible
pytest -s

# Run with detailed traceback
pytest --tb=long

# Run specific failing test with verbose output
pytest tests/test_geometry.py::test_name -vv --tb=long
```

## Integration with IDEs

### VS Code
Add to `.vscode/settings.json`:
```json
{
    "python.testing.pytestEnabled": true,
    "python.testing.pytestArgs": [
        "tests",
        "-v"
    ]
}
```

### PyCharm
1. Go to Settings → Tools → Python Integrated Tools
2. Set "Default test runner" to pytest
3. Right-click on test files to run

## Continuous Integration

### GitHub Actions Example
```yaml
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
        with:
          python-version: '3.8'
      - run: pip install -r requirements.txt
      - run: pytest --cov --cov-report=xml
      - uses: codecov/codecov-action@v2
```

## Performance

### Test Execution Time
- **Unit tests**: <5 seconds
- **Integration tests**: 10-30 seconds
- **All tests**: 30-60 seconds
- **With coverage**: +10-20 seconds

### Optimizing Slow Tests
```python
# Mark slow tests
@pytest.mark.slow
def test_expensive_operation():
    pass

# Skip in regular runs
pytest -m "not slow"
```

## Next Steps

1. Run the full test suite: `pytest --cov`
2. Review the coverage report: Open `htmlcov/index.html`
3. Add more tests for uncovered code
4. Set up pre-commit hooks for automatic testing

---

**Last Updated**: 2025-12-08
