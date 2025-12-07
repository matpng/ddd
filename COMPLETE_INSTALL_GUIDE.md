# Installation Guide - Orion Octave Cubes

## Quick Start (Development)

### 1. Install Dependencies

```bash
# Install all required packages
pip install -r requirements.txt
```

### 2. Verify Installation

```bash
# Run the verification script
python verify_startup.py
```

This will check:
- ✓ Python version (3.8+ required)
- ✓ All dependencies installed
- ✓ Required directories exist
- ✓ Required files present
- ✓ Port 5000 availability

### 3. Start the Application

```bash
# Development mode (auto-reload enabled)
python app.py
```

Or with custom settings:

```bash
# Set environment variables
export FLASK_DEBUG=true
export ENABLE_AUTONOMOUS=true
export ENABLE_ML_DISCOVERY=true

# Run the app
python app.py
```

### 4. Access the Dashboard

Open your browser to:
- **Main Dashboard**: http://localhost:5000
- **Discoveries**: http://localhost:5000/discoveries
- **API Docs**: See API_DOCUMENTATION.md
- **Metrics**: http://localhost:5000/metrics (Prometheus format)

---

## Production Deployment

### Option 1: Gunicorn (Recommended)

```bash
# Install gunicorn if not already installed
pip install gunicorn

# Start with 2 workers
gunicorn --workers 2 --threads 4 --bind 0.0.0.0:5000 app:app
```

### Option 2: Docker

```bash
# Build the container
docker build -t orion-octave-cubes .

# Run the container
docker run -p 5000:5000 orion-octave-cubes
```

### Option 3: Docker Compose (Full Stack)

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

---

## Environment Variables

Create a `.env` file or set these in your environment:

```bash
# Flask Configuration
FLASK_ENV=production                    # production | development
FLASK_DEBUG=false                       # true | false
FLASK_HOST=0.0.0.0                      # Bind address
FLASK_PORT=5000                         # Port number
SECRET_KEY=your-secret-key-here         # Generate with: python3 -c 'import secrets; print(secrets.token_hex(32))'

# Autonomous Discovery
ENABLE_AUTONOMOUS=true                  # Enable autonomous daemon
DISCOVERY_INTERVAL=3600                 # Seconds between discoveries (3600 = 1 hour)

# Machine Learning
ENABLE_ML_DISCOVERY=true                # Enable ML pattern discovery
ML_ANALYSIS_INTERVAL=7200               # Seconds between ML analysis (7200 = 2 hours)

# Analysis Configuration
DEFAULT_SIDE=2.0                        # Default cube side length
DEFAULT_ANGLE=45.0                      # Default rotation angle
MAX_DISTANCE_PAIRS=50000                # Maximum distance pairs to analyze
MAX_DIRECTION_PAIRS=50000               # Maximum direction pairs to analyze

# Caching
CACHE_ENABLED=true                      # Enable result caching
CACHE_MAX_SIZE=100                      # Maximum cache entries

# Logging
LOG_LEVEL=INFO                          # DEBUG | INFO | WARNING | ERROR | CRITICAL

# WakaTime (Optional)
WAKATIME_API_KEY=your-api-key-here      # Your WakaTime API key (optional)
```

**Security Note**: Never commit `.env` files or API keys to version control!

---

## Dependencies Explained

### Core Framework
- **Flask 2.3+**: Web framework for API and dashboard
- **Gunicorn 21.0+**: Production WSGI server

### Scientific Computing
- **NumPy 1.24+**: Array operations and linear algebra
- **SciPy 1.10+**: Scientific computing utilities
- **Matplotlib 3.5+**: Visualization and plotting

### Machine Learning
- **scikit-learn 1.3+**: Pattern discovery algorithms
  - DBSCAN clustering
  - K-means clustering
  - PCA dimensionality reduction
  - Isolation Forest anomaly detection

### System Monitoring
- **psutil 5.9+**: System resource monitoring (CPU, memory, disk)
- **requests 2.31+**: HTTP client for external integrations

---

## Common Issues & Solutions

### Issue: Import errors when running app

**Solution**: Install all dependencies
```bash
pip install -r requirements.txt
```

### Issue: Port 5000 already in use

**Solution**: Kill existing process or use a different port
```bash
# Find process using port 5000
lsof -i :5000  # On macOS/Linux
netstat -ano | findstr :5000  # On Windows

# Or use a different port
export FLASK_PORT=8000
python app.py
```

### Issue: Autonomous daemon not starting

**Solution**: Check environment variables
```bash
export ENABLE_AUTONOMOUS=true
python app.py
```

### Issue: Missing directories

**Solution**: Run verification script (it creates them automatically)
```bash
python verify_startup.py
```

### Issue: Out of memory errors

**Solution**: Reduce analysis limits
```bash
export MAX_DISTANCE_PAIRS=10000
export MAX_DIRECTION_PAIRS=5000
export CACHE_MAX_SIZE=50
```

---

## Running Tests

### Comprehensive Test Suite

```bash
# Run all tests
python test_comprehensive.py

# Run with verbose output
python test_comprehensive.py -v
```

### Individual Test Classes

```bash
# Test geometry primitives only
python -m unittest test_comprehensive.TestGeometryPrimitives

# Test discovery manager only
python -m unittest test_comprehensive.TestDiscoveryManager
```

### Test Coverage

The test suite includes:
- ✓ Geometry primitives (rotation, normalization, etc.)
- ✓ Cube generation (vertices, edges, faces)
- ✓ Intersection algorithms
- ✓ Analysis functions (distances, directions, angles)
- ✓ Discovery manager (save, retrieve, search)
- ✓ Configuration management
- ✓ Golden ratio detection

---

## Monitoring & Metrics

### Prometheus Metrics

The application exposes metrics at `/metrics` in Prometheus format:

```bash
# View metrics
curl http://localhost:5000/metrics

# Human-readable summary
curl http://localhost:5000/api/metrics/summary | python -m json.tool
```

**Available Metrics**:
- `http_requests_total` - Total HTTP requests
- `http_request_duration_seconds` - Request latency histogram
- `discoveries_total` - Total discoveries made
- `daemon_health_score` - Daemon health (0-100)
- `cache_entries` - Cache size
- `ml_analysis_total` - ML analyses performed
- `process_uptime_seconds` - Application uptime

### Integration with Monitoring Systems

**Prometheus Configuration** (`prometheus.yml`):
```yaml
scrape_configs:
  - job_name: 'orion-octave-cubes'
    scrape_interval: 30s
    static_configs:
      - targets: ['localhost:5000']
```

**Grafana Dashboard**:
- Import metrics from Prometheus
- Create visualizations for request rate, latency, discoveries
- Set up alerts for errors and health score

---

## Security Features

### Rate Limiting

All API endpoints have rate limiting enabled:

- **Standard endpoints**: 60 requests/minute
- **Analysis endpoint**: 10 requests/minute
- **ML analysis**: 5 requests/minute
- **Downloads**: 30 requests/minute
- **Search**: 30 requests/minute

When rate limit is exceeded, the API returns HTTP 429 with `Retry-After` header.

### CORS

Cross-Origin Resource Sharing (CORS) is configured for local development:

- Allowed origins: `localhost:5000`, `localhost:3000`
- Methods: GET, POST, PUT, DELETE, OPTIONS
- Headers: Content-Type, Authorization

### Request Validation

All POST/PUT requests are validated for:
- SQL injection attempts
- XSS (Cross-Site Scripting) patterns
- Path traversal attempts
- Payload size limits (50KB default for analysis, 10KB for ML)

### Security Headers

All responses include security headers:
- `X-Frame-Options: SAMEORIGIN` (prevent clickjacking)
- `X-Content-Type-Options: nosniff` (prevent MIME sniffing)
- `X-XSS-Protection: 1; mode=block` (XSS protection)
- `Referrer-Policy: strict-origin-when-cross-origin`
- `Content-Security-Policy` (in production)

---

## File Structure

```
orion-octave-cubes/
├── app.py                          # Main Flask application
├── orion_octave_test.py           # Core geometry analysis
├── config.py                      # Configuration management
├── discovery_manager.py           # Discovery storage system
├── daemon_monitor.py              # Health monitoring
├── ml_integration.py              # ML pattern discovery
├── ml_discovery.py                # ML algorithms
├── security_middleware.py         # Rate limiting & security
├── prometheus_metrics.py          # Metrics export
├── verify_startup.py              # Startup verification
├── requirements.txt               # Python dependencies
├── .env.example                   # Environment variable template
├── .gitignore                     # Git ignore rules
├── Dockerfile                     # Docker container config
├── docker-compose.yml             # Docker Compose config
│
├── autonomous_discoveries/        # Autonomous discovery results
│   ├── index.json                # Discovery index
│   └── YYYY-MM-DD/               # Daily discovery folders
│
├── test_results/                  # Test output files
│
├── static/                        # Frontend assets
│   ├── css/style.css
│   └── js/app.js
│
├── templates/                     # HTML templates
│   ├── index.html
│   └── discoveries.html
│
└── docs/                          # Documentation
    ├── API_DOCUMENTATION.md
    ├── IMPLEMENTATION_COMPLETE.md
    └── NETWORK_ERROR_FIXES.md
```

---

## Next Steps

After installation:

1. **Explore the Dashboard**: http://localhost:5000
   - Try different angles and cube sizes
   - View 3D visualizations
   - Download results as JSON

2. **Monitor Autonomous Discoveries**: http://localhost:5000/discoveries
   - Watch real-time discoveries
   - View discovery statistics
   - Search and filter results

3. **Test the API**: See `API_DOCUMENTATION.md`
   - Use the Python/JavaScript examples
   - Try different analysis parameters
   - Integrate with your own applications

4. **Set Up Monitoring**:
   - Configure Prometheus to scrape `/metrics`
   - Create Grafana dashboards
   - Set up alerts for errors

5. **Run Tests**:
   ```bash
   python test_comprehensive.py
   ```

6. **Review Security**:
   - Set strong `SECRET_KEY`
   - Configure allowed CORS origins
   - Adjust rate limits as needed

---

## Support & Documentation

- **API Documentation**: `API_DOCUMENTATION.md`
- **Implementation Details**: `IMPLEMENTATION_COMPLETE.md`
- **Network Troubleshooting**: `NETWORK_ERROR_FIXES.md`
- **Quick Start**: `QUICKSTART.md`
- **Main README**: `README.md`

For issues or questions, review the documentation or check the code comments.

---

## License

See LICENSE file for details.
