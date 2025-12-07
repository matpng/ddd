#!/usr/bin/env python3
"""
Enhanced Daemon Monitor
Provides health checking, performance metrics, and status tracking
for the autonomous discovery daemon.
"""

import time
import logging
import threading
import psutil
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from collections import deque
import json
from pathlib import Path

logger = logging.getLogger(__name__)


class DaemonMonitor:
    """
    Monitor and track autonomous daemon performance and health.
    """
    
    def __init__(self, max_history=1000):
        self.max_history = max_history
        self.start_time = None
        self.is_running = False
        self.last_heartbeat = None
        self.error_count = 0
        self.success_count = 0
        
        # Performance metrics
        self.discovery_times = deque(maxlen=max_history)
        self.error_history = deque(maxlen=100)
        self.discovery_history = deque(maxlen=max_history)
        
        # Resource tracking
        self.peak_memory = 0
        self.peak_cpu = 0
        
        # Thread safety
        self._lock = threading.Lock()
    
    def start(self):
        """Mark daemon as started."""
        with self._lock:
            self.start_time = datetime.utcnow()
            self.is_running = True
            self.last_heartbeat = datetime.utcnow()
            logger.info("Daemon monitor started")
    
    def stop(self):
        """Mark daemon as stopped."""
        with self._lock:
            self.is_running = False
            logger.info("Daemon monitor stopped")
    
    def heartbeat(self):
        """Record daemon heartbeat."""
        with self._lock:
            self.last_heartbeat = datetime.utcnow()
    
    def record_discovery(self, discovery_id: str, duration: float, success: bool = True):
        """
        Record a discovery attempt.
        
        Args:
            discovery_id: ID of the discovery
            duration: Time taken in seconds
            success: Whether the discovery was successful
        """
        with self._lock:
            timestamp = datetime.utcnow()
            
            if success:
                self.success_count += 1
                self.discovery_times.append(duration)
                self.discovery_history.append({
                    'id': discovery_id,
                    'timestamp': timestamp.isoformat(),
                    'duration': duration,
                    'success': True
                })
            else:
                self.error_count += 1
            
            self.heartbeat()
    
    def record_error(self, error_msg: str, error_type: str = 'unknown'):
        """Record an error occurrence."""
        with self._lock:
            self.error_count += 1
            self.error_history.append({
                'timestamp': datetime.utcnow().isoformat(),
                'type': error_type,
                'message': error_msg
            })
            self.heartbeat()
    
    def update_resources(self):
        """Update resource usage metrics."""
        try:
            process = psutil.Process()
            
            with self._lock:
                # Memory usage in MB
                memory_mb = process.memory_info().rss / 1024 / 1024
                self.peak_memory = max(self.peak_memory, memory_mb)
                
                # CPU percentage
                cpu_percent = process.cpu_percent(interval=0.1)
                self.peak_cpu = max(self.peak_cpu, cpu_percent)
                
        except Exception as e:
            logger.error(f"Error updating resources: {e}")
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get comprehensive daemon status.
        
        Returns:
            Dictionary with status information
        """
        with self._lock:
            uptime = None
            if self.start_time:
                uptime = (datetime.utcnow() - self.start_time).total_seconds()
            
            # Calculate health score (0-100)
            health_score = self._calculate_health_score()
            
            # Recent performance
            avg_discovery_time = None
            if self.discovery_times:
                avg_discovery_time = sum(self.discovery_times) / len(self.discovery_times)
            
            # Heartbeat age
            heartbeat_age = None
            heartbeat_healthy = False
            if self.last_heartbeat:
                heartbeat_age = (datetime.utcnow() - self.last_heartbeat).total_seconds()
                heartbeat_healthy = heartbeat_age < 300  # 5 minutes
            
            return {
                'is_running': self.is_running,
                'health_score': health_score,
                'uptime_seconds': uptime,
                'started_at': self.start_time.isoformat() if self.start_time else None,
                'last_heartbeat': self.last_heartbeat.isoformat() if self.last_heartbeat else None,
                'heartbeat_age_seconds': heartbeat_age,
                'heartbeat_healthy': heartbeat_healthy,
                'statistics': {
                    'total_discoveries': self.success_count,
                    'total_errors': self.error_count,
                    'success_rate': self._calculate_success_rate(),
                    'avg_discovery_time_seconds': avg_discovery_time
                },
                'resources': {
                    'peak_memory_mb': round(self.peak_memory, 2),
                    'peak_cpu_percent': round(self.peak_cpu, 2),
                    'current_memory_mb': self._get_current_memory(),
                    'current_cpu_percent': self._get_current_cpu()
                },
                'recent_errors': list(self.error_history)[-5:],  # Last 5 errors
                'recent_discoveries': list(self.discovery_history)[-10:]  # Last 10
            }
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get performance metrics for monitoring."""
        with self._lock:
            return {
                'discovery_count': self.success_count,
                'error_count': self.error_count,
                'success_rate': self._calculate_success_rate(),
                'avg_discovery_time': sum(self.discovery_times) / len(self.discovery_times) if self.discovery_times else 0,
                'peak_memory_mb': self.peak_memory,
                'peak_cpu_percent': self.peak_cpu,
                'uptime_seconds': (datetime.utcnow() - self.start_time).total_seconds() if self.start_time else 0
            }
    
    def _calculate_health_score(self) -> float:
        """
        Calculate overall health score (0-100).
        
        Factors:
        - Is running: 30 points
        - Recent heartbeat: 30 points
        - Success rate: 30 points
        - Low error rate: 10 points
        """
        score = 0.0
        
        # Running status
        if self.is_running:
            score += 30
        
        # Heartbeat recency
        if self.last_heartbeat:
            age = (datetime.utcnow() - self.last_heartbeat).total_seconds()
            if age < 60:  # < 1 minute
                score += 30
            elif age < 300:  # < 5 minutes
                score += 20
            elif age < 600:  # < 10 minutes
                score += 10
        
        # Success rate
        success_rate = self._calculate_success_rate()
        score += success_rate * 0.3
        
        # Error rate (inverse)
        total_attempts = self.success_count + self.error_count
        if total_attempts > 0:
            error_rate = self.error_count / total_attempts
            score += (1 - error_rate) * 10
        else:
            score += 10
        
        return round(score, 2)
    
    def _calculate_success_rate(self) -> float:
        """Calculate success rate as percentage."""
        total = self.success_count + self.error_count
        if total == 0:
            return 100.0
        return round((self.success_count / total) * 100, 2)
    
    def _get_current_memory(self) -> float:
        """Get current memory usage in MB."""
        try:
            process = psutil.Process()
            return round(process.memory_info().rss / 1024 / 1024, 2)
        except:
            return 0.0
    
    def _get_current_cpu(self) -> float:
        """Get current CPU percentage."""
        try:
            process = psutil.Process()
            return round(process.cpu_percent(interval=0.1), 2)
        except:
            return 0.0
    
    def export_metrics(self, filepath: str):
        """Export metrics to JSON file."""
        try:
            metrics = self.get_status()
            with open(filepath, 'w') as f:
                json.dump(metrics, f, indent=2)
            logger.info(f"Metrics exported to {filepath}")
        except Exception as e:
            logger.error(f"Error exporting metrics: {e}")
    
    def get_performance_report(self) -> str:
        """Generate a human-readable performance report."""
        status = self.get_status()
        
        report = []
        report.append("=" * 70)
        report.append("DAEMON PERFORMANCE REPORT")
        report.append("=" * 70)
        report.append(f"Status: {'🟢 RUNNING' if status['is_running'] else '🔴 STOPPED'}")
        report.append(f"Health Score: {status['health_score']}/100")
        
        if status['uptime_seconds']:
            uptime = timedelta(seconds=int(status['uptime_seconds']))
            report.append(f"Uptime: {uptime}")
        
        report.append(f"\nStatistics:")
        report.append(f"  Total Discoveries: {status['statistics']['total_discoveries']}")
        report.append(f"  Total Errors: {status['statistics']['total_errors']}")
        report.append(f"  Success Rate: {status['statistics']['success_rate']}%")
        
        if status['statistics']['avg_discovery_time_seconds']:
            report.append(f"  Avg Discovery Time: {status['statistics']['avg_discovery_time_seconds']:.2f}s")
        
        report.append(f"\nResource Usage:")
        report.append(f"  Current Memory: {status['resources']['current_memory_mb']} MB")
        report.append(f"  Peak Memory: {status['resources']['peak_memory_mb']} MB")
        report.append(f"  Current CPU: {status['resources']['current_cpu_percent']}%")
        report.append(f"  Peak CPU: {status['resources']['peak_cpu_percent']}%")
        
        if status['recent_errors']:
            report.append(f"\nRecent Errors ({len(status['recent_errors'])}):")
            for error in status['recent_errors'][-3:]:
                report.append(f"  - [{error['timestamp']}] {error['type']}: {error['message'][:60]}")
        
        report.append("=" * 70)
        
        return "\n".join(report)


# Global monitor instance
daemon_monitor = DaemonMonitor()
