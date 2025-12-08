# Orion Octave Cubes - Quick Reference

## 🚀 Quick Start

### Run the Application
```bash
python app.py
```
Access at: http://localhost:5000

### Run Tests
```bash
# All tests
pytest

# With coverage
pytest --cov --cov-report=html

# Specific tests
pytest -m unit              # Unit tests only
pytest -m api               # API tests only
pytest tests/test_geometry.py  # Specific file
```

### Code Quality
```bash
# Format code
black . && isort .

# Lint
flake8

# Type check
mypy orion_octave_test.py app.py
```

---

## 📦 New Modules

### Custom Exceptions (`models/exceptions.py`)
```python
from models.exceptions import (
    InvalidParameterError,
    CalculationError,
    CacheKeyError,
    ValidationError
)

# Usage
if value < 0:
    raise InvalidParameterError('value', value, 'must be positive')
```

### Validation Utilities (`utils/validation.py`)
```python
from utils.validation import (
    validate_side_length,
    validate_angle,
    validate_analysis_params
)

# Validate single parameter
side = validate_side_length(2.5, min_val=0.01, max_val=100.0)

# Validate all at once
params = {'side': 2.0, 'angle': 30.0, ...}
side, angle, max_dist, max_dir = validate_analysis_params(params, Config)
```

---

## 🧪 Testing

### Test Structure
```
tests/
├── conftest.py          # Fixtures
├── test_geometry.py     # Geometry engine (50+ tests)
└── test_api.py          # API endpoints (30+ tests)
```

### Writing Tests
```python
import pytest

def test_your_function():
    # Arrange
    input_val = 10
    
    # Act
    result = your_function(input_val)
    
    # Assert
    assert result == expected
```

### Using Fixtures
```python
def test_with_app(client, sample_analysis_params):
    """Test using pytest fixtures."""
    response = client.post('/api/analyze', 
                          json=sample_analysis_params)
    assert response.status_code == 200
```

### Test Markers
```python
@pytest.mark.unit
def test_unit(): pass

@pytest.mark.integration
def test_integration(): pass

@pytest.mark.api
def test_api(): pass

@pytest.mark.slow
def test_slow(): pass
```

---

## ⚙️ Configuration Files

### pytest.ini
```ini
[pytest]
testpaths = tests
markers =
    unit: Unit tests
    integration: Integration tests
    api: API tests
    slow: Slow tests
```

### mypy.ini
```ini
[mypy]
python_version = 3.8
check_untyped_defs = True
ignore_missing_imports = True
```

### .flake8
```ini
[flake8]
max-line-length = 120
max-complexity = 15
```

---

## 🎯 Common Tasks

### Add a New Exception
```python
# In models/exceptions.py
class MyCustomError(GeometryError):
    """Description of error."""
    def __init__(self, param: str):
        super().__init__(f"Error with {param}")
```

### Add a New Validation
```python
# In utils/validation.py
def validate_my_param(value: float) -> float:
    """Validate custom parameter."""
    if value < 0:
        raise InvalidParameterError('my_param', value, 'must be positive')
    return value
```

### Add a New Test
```python
# In tests/test_geometry.py
class TestMyFeature:
    def test_basic_case(self):
        result = my_function(input_value)
        assert result == expected

    @pytest.mark.slow
    def test_large_case(self):
        # Expensive test
        pass
```

---

## 📊 Exception Hierarchy

```
GeometryError
  ├── InvalidParameterError
  ├── CalculationError
  └── IntersectionError

CacheError
  ├── CacheKeyError
  └── CacheSizeError

DiscoveryError
  ├── DiscoveryNotFoundError
  └── DiscoveryGenerationError

ValidationError
APIError
  └── RateLimitError
```

---

## 🔍 Debugging

### Enable Debug Logging
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Run Single Test with Verbose Output
```bash
pytest tests/test_geometry.py::TestBasicHelpers::test_normalize -v
```

### Check Coverage for Specific File
```bash
pytest --cov=orion_octave_test tests/test_geometry.py
```

---

## 📝 Code Style

### Formatting Standards
- **Line length**: 120 characters
- **Formatter**: Black
- **Import sorter**: isort
- **Linter**: flake8

### Type Hints
```python
def analyze_cube(side: float, angle: float) -> Dict[str, Any]:
    """Type hints for function signature."""
    pass
```

### Docstrings
```python
def function_name(param: str) -> bool:
    """
    Short description.
    
    Args:
        param: Description of parameter
        
    Returns:
        Description of return value
        
    Raises:
        InvalidParameterError: When param is invalid
    """
    pass
```

---

## 🚨 Common Issues & Solutions

### Import Errors
```bash
# Add project root to PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:$(pwd)"  # Linux/Mac
set PYTHONPATH=%PYTHONPATH%;%cd%          # Windows
```

### Tests Not Found
```bash
# Ensure you're in project root
cd c:\Users\fc\Documents\GitHub\ddd
pytest
```

### Module Not Found
```python
# Add to top of test file
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
```

---

## 📚 Resources

- **Main README**: [README.md](../README.md)
- **Development Guide**: [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md)
- **Implementation Plan**: Review improvements made
- **Walkthrough**: Detailed change documentation

---

## ✅ Pre-Commit Checklist

Before committing:
- [ ] Run tests: `pytest`
- [ ] Format code: `black . && isort .`
- [ ] Lint: `flake8`
- [ ] Type check (optional): `mypy orion_octave_test.py`
- [ ] Update docs if needed
- [ ] Write descriptive commit message

---

## 🎓 Best Practices

1. **Always use specific exceptions** - No bare `except Exception`
2. **Validate inputs** - Use `utils.validation` functions
3. **Write tests** - Aim for >80% coverage
4. **Type hint** - Add type hints to new functions
5. **Document** - Add docstrings to public functions
6. **Format** - Run `black` and `isort` before committing

---

**Last Updated**: 2025-12-08  
**Version**: 2.0 (Post-Improvement)
