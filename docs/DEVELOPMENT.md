# Orion Octave Cubes - Development Guide

## Table of Contents

1. [Setup](#setup)
2. [Architecture](#architecture)
3. [Development Workflow](#development-workflow)
4. [Testing](#testing)
5. [Code Quality](#code-quality)
6. [Contributing](#contributing)

## Setup

### Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- Virtual environment (recommended)

### Installation

```bash
# Clone the repository
git clone https://github.com/matpng/ddd.git
cd ddd

# Create virtual environment
python -m venv .venv

# Activate virtual environment
# Windows:
.venv\Scripts\activate
# Linux/Mac:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Environment Variables

Create a `.env` file in the project root:

```bash
# Flask Configuration
FLASK_ENV=development
FLASK_HOST=0.0.0.0
FLASK_PORT=5000

# Security
SECRET_KEY=your-secret-key-here

# Analysis Limits
MAX_SIDE_LENGTH=100
MIN_SIDE_LENGTH=0.01
MAX_DISTANCE_PAIRS=100000
MAX_DIRECTION_PAIRS=100000

# Cache
CACHE_MAX_SIZE=100
```

## Architecture

### Project Structure

```
ddd/
├── app.py                          # Main Flask application
├── orion_octave_test.py           # Core geometry engine
├── config.py                       # Configuration management
├── models/
│   ├── __init__.py
│   └── exceptions.py              # Custom exceptions
├── utils/
│   ├── __init__.py
│   └── validation.py              # Validation utilities
├── security_middleware.py         # Security & rate limiting
├── prometheus_metrics.py          # Metrics collection
├── discovery_manager.py           # Discovery system
├── ml_integration.py              # Machine learning
├── static/
│   ├── css/
│   │   └── style.css
│   └── js/
│       └── app.js
├── templates/
│   ├── index.html                 # Main dashboard
│   ├── admin.html                 # Admin panel
│   └── discoveries.html           # Discoveries view
├── tests/
│   ├── __init__.py
│   ├── conftest.py                # Pytest fixtures
│   ├── test_geometry.py           # Geometry tests
│   └── test_api.py                # API tests
└── docs/
    └── DEVELOPMENT.md             # This file
```

### Core Components

#### 1. Geometry Engine (`orion_octave_test.py`)

Handles all geometric computations:
- Cube creation and transformation
- Edge-face and edge-edge intersections
- Distance and direction analysis
- Golden ratio detection
- Symmetry analysis

**Key Classes:**
- `Cube`: Represents oriented cube
- `Face`: Square face representation
- `Edge`: Line segment

**Key Functions:**
- `main()`: Main analysis pipeline
- `analyze_distances()`: Distance spectrum
- `analyze_directions()`: Direction vectors
- `scan_for_phi()`: Golden ratio detection

#### 2. Web Application (`app.py`)

Flask-based web interface:
- REST API endpoints
- Plot generation
- Caching system
- Discovery management

**Main Routes:**
- `/` - Dashboard
- `/admin` - Admin panel
- `/api/analyze` - Run analysis
- `/api/plot/<type>/<key>` - Generate plots
- `/api/download/<key>` - Download results

#### 3. Security (`security_middleware.py`)

- Rate limiting (token bucket algorithm)
- CORS configuration
- Request validation
- Security headers

#### 4. Discovery System (`discovery_manager.py`)

Autonomous discovery features:
- Scheduled angle sweeps
- Pattern detection
- Research paper generation
- Database storage

## Development Workflow

### Running the Application

```bash
# Development server
python app.py

# Or use the start script
./start_app.sh  # Linux/Mac
start_app.sh    # Windows
```

The application will be available at `http://localhost:5000`

### Making Changes

1. **Create a feature branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes**
   - Follow PEP 8 style guide
   - Add type hints where possible
   - Include docstrings for functions

3. **Run tests**
   ```bash
   pytest tests/ -v
   ```

4. **Check code quality**
   ```bash
   # Format code
   black .
   isort .
   
   # Lint
   flake8
   
   # Type check
   mypy orion_octave_test.py app.py
   ```

5. **Commit and push**
   ```bash
   git add .
   git commit -m "feat: your feature description"
   git push origin feature/your-feature-name
   ```

## Testing

### Running Tests

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_geometry.py

# Run with coverage
pytest --cov=. --cov-report=html

# Run only unit tests
pytest -m unit

# Run only API tests
pytest -m api

# Skip slow tests
pytest -m "not slow"
```

### Test Organization

- **Unit tests** (`test_geometry.py`): Test individual functions
- **Integration tests** (`test_api.py`): Test API endpoints
- **Fixtures** (`conftest.py`): Shared test setup

### Writing Tests

```python
import pytest

def test_your_function():
    """Test description."""
    # Arrange
    input_value = 42
    
    # Act
    result = your_function(input_value)
    
    # Assert
    assert result == expected_value
```

### Test Markers

```python
@pytest.mark.unit
def test_unit():
    pass

@pytest.mark.integration
def test_integration():
    pass

@pytest.mark.slow
def test_slow_operation():
    pass

@pytest.mark.api
def test_api_endpoint():
    pass
```

## Code Quality

### Code Formatting

We use **Black** for code formatting:

```bash
# Format all files
black .

# Check without modifying
black --check .
```

### Import Sorting

We use **isort** for import organization:

```bash
# Sort imports
isort .

# Check without modifying
isort --check-only .
```

### Linting

We use **flake8** for linting:

```bash
# Lint all files
flake8

# Lint specific file
flake8 app.py
```

Configuration in `.flake8`:
- Max line length: 120
- Complexity limit: 15

### Type Checking

We use **mypy** for static type checking:

```bash
# Check types
mypy orion_octave_test.py app.py

# Check with strict mode
mypy --strict orion_octave_test.py
```

### Pre-commit Checks

Before committing, run:

```bash
# Quick check
black --check . && isort --check-only . && flake8 && pytest

# Or create a git pre-commit hook
```

## Exception Handling

Use custom exceptions from `models.exceptions`:

```python
from models.exceptions import InvalidParameterError, CalculationError

def analyze_cube(side: float):
    if side <= 0:
        raise InvalidParameterError('side', side, 'must be positive')
    
    try:
        result = complex_calculation(side)
    except ZeroDivisionError as e:
        raise CalculationError('cube analysis', str(e))
    
    return result
```

### Exception Hierarchy

- `GeometryError` - Base for geometry errors
  - `InvalidParameterError` - Invalid input
  - `CalculationError` - Computation failed
  - `IntersectionError` - Intersection failed
- `CacheError` - Cache-related errors
  - `CacheKeyError` - Key not found
  - `CacheSizeError` - Size exceeded
- `DiscoveryError` - Discovery errors
  - `DiscoveryNotFoundError` - Not found
  - `DiscoveryGenerationError` - Generation failed
- `ValidationError` - Input validation failed
- `APIError` - API errors
  - `RateLimitError` - Rate limit exceeded

## Contributing

### Guidelines

1. **Follow existing patterns** - Maintain consistency
2. **Write tests** - Cover new functionality
3. **Document changes** - Update docstrings and docs
4. **Small commits** - Atomic, focused changes
5. **Descriptive messages** - Clear commit messages

### Commit Message Format

```
type(scope): subject

body (optional)

footer (optional)
```

Types:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation
- `style`: Formatting
- `refactor`: Code restructuring
- `test`: Adding tests
- `chore`: Maintenance

Example:
```
feat(api): add rate limiting to analysis endpoint

Implements token bucket algorithm for rate limiting.
Limits analysis requests to 10/minute per client.

Closes #123
```

### Pull Request Process

1. Update documentation
2. Add/update tests
3. Ensure all tests pass
4. Update CHANGELOG.md
5. Request review

## Debugging

### Enable Debug Mode

```python
# In config.py
DEBUG = True
```

### Logging

```python
import logging

logger = logging.getLogger(__name__)
logger.debug("Debug message")
logger.info("Info message")
logger.warning("Warning message")
logger.error("Error message")
logger.exception("Exception with traceback")
```

### Common Issues

**Import errors:**
```bash
# Ensure project root is in PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
```

**Port already in use:**
```bash
# Change port in .env or config.py
PORT=5001
```

**Cache issues:**
- Clear the cache: Restart the application
- Disable caching: Set `CACHE_ENABLED=False` in config

## Performance

### Profiling

```python
import cProfile
import pstats

profiler = cProfile.Profile()
profiler.enable()

# Your code here

profiler.disable()
stats = pstats.Stats(profiler)
stats.sort_stats('cumulative')
stats.print_stats(20)
```

### Optimization Tips

1. **Use caching** - Cache expensive computations
2. **Limit sampling** - Use max_pairs parameters
3. **Vectorize operations** - Use NumPy operations
4. **Profile first** - Measure before optimizing

## Resources

- [Flask Documentation](https://flask.palletsprojects.com/)
- [NumPy Documentation](https://numpy.org/doc/)
- [Pytest Documentation](https://docs.pytest.org/)
- [PEP 8 Style Guide](https://pep8.org/)

## Questions?

For questions or issues, please:
1. Check existing documentation
2. Search closed issues
3. Open a new issue with details

---

**Happy coding!** 🚀
