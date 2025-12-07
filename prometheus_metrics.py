#!/usr/bin/env python3
"""
Prometheus Metrics Exporter for Orion Octave Cubes
Provides /metrics endpoint with request tracking, latency, and application metrics
"""

from functools import wraps
from flask import request, Response
from datetime import datetime
import threading
import time
import logging
from collections import defaultdict, Counter

logger = logging.getLogger(__name__)


# ============================================================================
# METRICS STORAGE
# ============================================================================

class MetricsCollector:
    """Collect and format Prometheus metrics."""
    
    def __init__(self):
        self.lock = threading.Lock()
        
        # Counter metrics
        self.request_count = Counter()  # {method_path: count}
        self.status_count = Counter()   # {method_path_status: count}
        self.error_count = Counter()    # {endpoint_error_type: count}
        
        # Histogram buckets for latency (in seconds)
        self.latency_buckets = [0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0]
        self.latency_histogram = defaultdict(lambda: defaultdict(int))  # {method_path: {bucket: count}}
        self.latency_sum = defaultdict(float)  # {method_path: total_seconds}
        self.latency_count = defaultdict(int)  # {method_path: count}
        
        # Gauge metrics (current values)
        self.active_requests = 0
        self.discovery_count = 0
        self.daemon_health_score = 0
        self.cache_size = 0
        
        # Custom metrics
        self.discovery_duration_sum = 0.0
        self.discovery_duration_count = 0
        self.ml_analysis_count = 0
        
        # Application start time
        self.start_time = time.time()
    
    def record_request(self, method, path, status_code, duration):
        """Record an HTTP request with its metrics."""
        with self.lock:
            # Sanitize path (remove IDs for aggregation)
            clean_path = self._sanitize_path(path)
            key = f"{method} {clean_path}"
            
            # Increment counters
            self.request_count[key] += 1
            self.status_count[f"{key} {status_code}"] += 1
            
            # Record latency
            self.latency_sum[key] += duration
            self.latency_count[key] += 1
            
            # Record in histogram buckets
            for bucket in self.latency_buckets:
                if duration <= bucket:
                    self.latency_histogram[key][bucket] += 1
            
            # Also count in +Inf bucket
            self.latency_histogram[key]['+Inf'] += 1
    
    def record_error(self, endpoint, error_type):
        """Record an application error."""
        with self.lock:
            self.error_count[f"{endpoint} {error_type}"] += 1
    
    def update_gauge(self, metric_name, value):
        """Update a gauge metric."""
        with self.lock:
            if metric_name == 'active_requests':
                self.active_requests = value
            elif metric_name == 'discovery_count':
                self.discovery_count = value
            elif metric_name == 'daemon_health_score':
                self.daemon_health_score = value
            elif metric_name == 'cache_size':
                self.cache_size = value
    
    def increment_active_requests(self):
        """Increment active request counter."""
        with self.lock:
            self.active_requests += 1
    
    def decrement_active_requests(self):
        """Decrement active request counter."""
        with self.lock:
            self.active_requests -= 1
    
    def record_discovery(self, duration):
        """Record a discovery completion with duration."""
        with self.lock:
            self.discovery_duration_sum += duration
            self.discovery_duration_count += 1
            self.discovery_count += 1
    
    def record_ml_analysis(self):
        """Record an ML analysis execution."""
        with self.lock:
            self.ml_analysis_count += 1
    
    def _sanitize_path(self, path):
        """Remove variable path segments for metric aggregation."""
        # Replace UUIDs, numbers, cache keys with placeholders
        import re
        
        # Replace cache keys (pattern: number_number_number_number)
        path = re.sub(r'\d+_\d+_\d+_\d+', ':cache_key', path)
        
        # Replace UUIDs
        path = re.sub(
            r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}',
            ':id',
            path,
            flags=re.IGNORECASE
        )
        
        # Replace discovery IDs (pattern: type_YYYYMMDD_HHMMSS)
        path = re.sub(r'[a-z_]+_\d{8}_\d{6}', ':discovery_id', path)
        
        # Replace other numeric IDs
        path = re.sub(r'/\d+(?=/|$)', '/:id', path)
        
        return path
    
    def generate_prometheus_format(self):
        """Generate metrics in Prometheus text format."""
        lines = []
        
        # Add timestamp
        lines.append(f"# Orion Octave Cubes Metrics - {datetime.utcnow().isoformat()}Z")
        lines.append("")
        
        with self.lock:
            # HTTP request count
            lines.append("# HELP http_requests_total Total number of HTTP requests")
            lines.append("# TYPE http_requests_total counter")
            for key, count in sorted(self.request_count.items()):
                method, path = key.split(' ', 1)
                lines.append(f'http_requests_total{{method="{method}",path="{path}"}} {count}')
            lines.append("")
            
            # HTTP request count by status
            lines.append("# HELP http_requests_by_status Total number of HTTP requests by status code")
            lines.append("# TYPE http_requests_by_status counter")
            for key, count in sorted(self.status_count.items()):
                parts = key.rsplit(' ', 1)
                method_path, status = parts[0], parts[1]
                method, path = method_path.split(' ', 1)
                lines.append(f'http_requests_by_status{{method="{method}",path="{path}",status="{status}"}} {count}')
            lines.append("")
            
            # HTTP request latency histogram
            lines.append("# HELP http_request_duration_seconds HTTP request latency")
            lines.append("# TYPE http_request_duration_seconds histogram")
            for key in sorted(self.latency_histogram.keys()):
                method, path = key.split(' ', 1)
                
                # Output histogram buckets
                for bucket in self.latency_buckets + ['+Inf']:
                    count = self.latency_histogram[key].get(bucket, 0)
                    le = bucket if bucket == '+Inf' else f'{bucket:.2f}'
                    lines.append(f'http_request_duration_seconds_bucket{{method="{method}",path="{path}",le="{le}"}} {count}')
                
                # Output sum and count
                total_seconds = self.latency_sum[key]
                total_count = self.latency_count[key]
                lines.append(f'http_request_duration_seconds_sum{{method="{method}",path="{path}"}} {total_seconds:.6f}')
                lines.append(f'http_request_duration_seconds_count{{method="{method}",path="{path}"}} {total_count}')
            lines.append("")
            
            # Error count
            lines.append("# HELP application_errors_total Total number of application errors")
            lines.append("# TYPE application_errors_total counter")
            for key, count in sorted(self.error_count.items()):
                endpoint, error_type = key.rsplit(' ', 1)
                lines.append(f'application_errors_total{{endpoint="{endpoint}",type="{error_type}"}} {count}')
            lines.append("")
            
            # Active requests gauge
            lines.append("# HELP http_requests_active Number of currently active HTTP requests")
            lines.append("# TYPE http_requests_active gauge")
            lines.append(f"http_requests_active {self.active_requests}")
            lines.append("")
            
            # Discovery count
            lines.append("# HELP discoveries_total Total number of discoveries made")
            lines.append("# TYPE discoveries_total counter")
            lines.append(f"discoveries_total {self.discovery_count}")
            lines.append("")
            
            # Discovery duration
            if self.discovery_duration_count > 0:
                lines.append("# HELP discovery_duration_seconds Discovery execution time")
                lines.append("# TYPE discovery_duration_seconds summary")
                lines.append(f"discovery_duration_seconds_sum {self.discovery_duration_sum:.6f}")
                lines.append(f"discovery_duration_seconds_count {self.discovery_duration_count}")
                lines.append("")
            
            # Daemon health score
            lines.append("# HELP daemon_health_score Daemon health score (0-100)")
            lines.append("# TYPE daemon_health_score gauge")
            lines.append(f"daemon_health_score {self.daemon_health_score}")
            lines.append("")
            
            # Cache size
            lines.append("# HELP cache_entries Number of entries in analysis cache")
            lines.append("# TYPE cache_entries gauge")
            lines.append(f"cache_entries {self.cache_size}")
            lines.append("")
            
            # ML analysis count
            lines.append("# HELP ml_analysis_total Total number of ML analyses performed")
            lines.append("# TYPE ml_analysis_total counter")
            lines.append(f"ml_analysis_total {self.ml_analysis_count}")
            lines.append("")
            
            # Application uptime
            uptime = time.time() - self.start_time
            lines.append("# HELP process_uptime_seconds Application uptime in seconds")
            lines.append("# TYPE process_uptime_seconds gauge")
            lines.append(f"process_uptime_seconds {uptime:.2f}")
            lines.append("")
        
        return '\n'.join(lines)


# Global metrics collector
metrics = MetricsCollector()


# ============================================================================
# DECORATORS
# ============================================================================

def track_metrics(f):
    """
    Decorator to automatically track request metrics.
    
    Usage:
        @app.route('/api/analyze')
        @track_metrics
        def analyze():
            ...
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        start_time = time.time()
        metrics.increment_active_requests()
        
        try:
            response = f(*args, **kwargs)
            
            # Calculate duration
            duration = time.time() - start_time
            
            # Extract status code
            if isinstance(response, tuple):
                status_code = response[1] if len(response) > 1 else 200
            else:
                status_code = getattr(response, 'status_code', 200)
            
            # Record metrics
            metrics.record_request(
                request.method,
                request.path,
                status_code,
                duration
            )
            
            return response
        
        except Exception as e:
            # Record error
            duration = time.time() - start_time
            metrics.record_request(request.method, request.path, 500, duration)
            metrics.record_error(request.path, type(e).__name__)
            raise
        
        finally:
            metrics.decrement_active_requests()
    
    return decorated_function


# ============================================================================
# FLASK INTEGRATION
# ============================================================================

def setup_metrics(app):
    """
    Setup Prometheus metrics endpoint for Flask app.
    
    Usage:
        from prometheus_metrics import setup_metrics
        
        app = Flask(__name__)
        setup_metrics(app)
    """
    
    @app.route('/metrics')
    def prometheus_metrics():
        """Prometheus metrics endpoint."""
        output = metrics.generate_prometheus_format()
        return Response(output, mimetype='text/plain; version=0.0.4; charset=utf-8')
    
    @app.route('/api/metrics/summary')
    def metrics_summary():
        """Human-readable metrics summary (JSON)."""
        with metrics.lock:
            summary = {
                'uptime_seconds': time.time() - metrics.start_time,
                'active_requests': metrics.active_requests,
                'total_requests': sum(metrics.request_count.values()),
                'total_errors': sum(metrics.error_count.values()),
                'discovery_count': metrics.discovery_count,
                'ml_analysis_count': metrics.ml_analysis_count,
                'daemon_health_score': metrics.daemon_health_score,
                'cache_size': metrics.cache_size,
                'top_endpoints': sorted(
                    metrics.request_count.items(),
                    key=lambda x: x[1],
                    reverse=True
                )[:10],
                'avg_latency_by_endpoint': {
                    key: (metrics.latency_sum[key] / metrics.latency_count[key])
                    for key in metrics.latency_count.keys()
                }
            }
            
            return Response(
                __import__('json').dumps(summary, indent=2),
                mimetype='application/json'
            )
    
    @app.before_request
    def before_request_metrics():
        """Track request start time."""
        request._start_time = time.time()
    
    @app.after_request
    def after_request_metrics(response):
        """Track request completion."""
        if hasattr(request, '_start_time'):
            duration = time.time() - request._start_time
            
            # Skip metrics endpoint itself to avoid recursion
            if request.path not in ['/metrics', '/api/metrics/summary']:
                metrics.record_request(
                    request.method,
                    request.path,
                    response.status_code,
                    duration
                )
        
        return response
    
    logger.info("✓ Prometheus metrics endpoint configured at /metrics")


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def update_application_metrics(discovery_manager=None, daemon_monitor=None, cache=None):
    """
    Update application-specific gauge metrics.
    Call this periodically from a background thread.
    
    Args:
        discovery_manager: DiscoveryManager instance
        daemon_monitor: DaemonMonitor instance
        cache: Analysis cache dict/LRUCache
    """
    if discovery_manager:
        try:
            stats = discovery_manager.get_stats()
            metrics.update_gauge('discovery_count', stats.get('total_discoveries', 0))
        except Exception as e:
            logger.error(f"Error updating discovery metrics: {e}")
    
    if daemon_monitor:
        try:
            health = daemon_monitor.get_status()
            metrics.update_gauge('daemon_health_score', health.get('health_score', 0))
        except Exception as e:
            logger.error(f"Error updating daemon health metrics: {e}")
    
    if cache:
        try:
            cache_size = len(cache.cache) if hasattr(cache, 'cache') else len(cache)
            metrics.update_gauge('cache_size', cache_size)
        except Exception as e:
            logger.error(f"Error updating cache metrics: {e}")


def start_metrics_updater(discovery_manager, daemon_monitor, cache, interval=30):
    """
    Start a background thread to update application metrics.
    
    Args:
        discovery_manager: DiscoveryManager instance
        daemon_monitor: DaemonMonitor instance  
        cache: Analysis cache
        interval: Update interval in seconds (default 30)
    """
    def updater():
        while True:
            time.sleep(interval)
            update_application_metrics(discovery_manager, daemon_monitor, cache)
    
    thread = threading.Thread(target=updater, daemon=True)
    thread.start()
    logger.info(f"✓ Metrics updater started (interval={interval}s)")
