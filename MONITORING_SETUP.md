# 🔍 Monitoring & Observability Setup Guide

## Overview

This guide provides step-by-step instructions for setting up comprehensive monitoring for the Orion Octave Cubes application deployed on Render.com.

---

## 1. Application Performance Monitoring (APM)

### Option A: Sentry (Recommended - Free tier available)

**Setup:**

1. **Create Sentry Account:**
   - Go to https://sentry.io
   - Create free account
   - Create new project: "orion-octave-cubes"
   - Copy your DSN

2. **Add to Requirements:**
   ```bash
   echo "sentry-sdk[flask]>=1.40.0" >> requirements.txt
   ```

3. **Add to app.py** (at the top):
   ```python
   import sentry_sdk
   from sentry_sdk.integrations.flask import FlaskIntegration
   
   # Initialize Sentry
   if os.environ.get('SENTRY_DSN'):
       sentry_sdk.init(
           dsn=os.environ.get('SENTRY_DSN'),
           integrations=[FlaskIntegration()],
           traces_sample_rate=0.1,  # 10% of transactions
           environment=os.environ.get('FLASK_ENV', 'production'),
           release=f"orion-octave@{os.environ.get('GIT_COMMIT', 'unknown')}"
       )
   ```

4. **Add to Render Environment Variables:**
   ```
   SENTRY_DSN=https://your-sentry-dsn@sentry.io/project-id
   ```

---

## 2. Uptime Monitoring

### UptimeRobot (Free - 50 monitors)

**Setup:**

1. Go to https://uptimerobot.com
2. Create free account
3. Add new monitor:
   - **Monitor Type:** HTTP(s)
   - **Friendly Name:** Orion Octave Cubes
   - **URL:** https://ddd-lwhl.onrender.com/health
   - **Monitoring Interval:** 5 minutes
   - **Monitor Timeout:** 30 seconds
   - **Alert Contacts:** Your email/Slack/Discord

4. **Advanced Settings:**
   - Expected Status Code: 200
   - Keyword Check: `"success":true`
   - Alert when down for: 2 checks (10 minutes)

**Alternative: BetterUptime**
- https://betteruptime.com
- More features on free tier
- Better alerting options

---

## 3. Log Aggregation

### Papertrail (Free - 50MB/month search)

**Setup:**

1. Go to https://papertrailapp.com
2. Create account
3. Get your log destination (e.g., `logs7.papertrailapp.com:12345`)

4. **Add to Render:**
   - Go to Render Dashboard
   - Select your service
   - Navigate to "Logs" → "External Logs"
   - Add Papertrail destination

5. **Configure Alerts:**
   - Search: `ERROR` or `CRITICAL`
   - Create alert → Email/Slack notification

---

## 4. Custom Health Monitoring

### Enhanced Health Endpoint

Already implemented in `app.py`, but can be enhanced:

```python
@app.route('/api/health/detailed')
@require_api_token
def detailed_health():
    """Comprehensive health check with all metrics"""
    try:
        health_data = {
            'status': 'healthy',
            'timestamp': datetime.utcnow().isoformat(),
            'uptime_seconds': time.time() - daemon_status.get('started_at', time.time()),
            'components': {
                'daemon': {
                    'status': 'running' if daemon_status.get('running') else 'stopped',
                    'discoveries_today': daemon_status.get('discoveries_today', 0),
                    'last_discovery': daemon_status.get('last_discovery'),
                    'cycle_count': daemon_status.get('cycle_count', 0)
                },
                'database': {
                    'status': 'connected',
                    'path': 'pak_intelligence.db',
                    'size_mb': get_db_size()
                },
                'cache': {
                    'status': 'active' if Config.CACHE_ENABLED else 'disabled',
                    'size': len(analysis_cache.cache) if hasattr(analysis_cache, 'cache') else 0,
                    'max_size': Config.CACHE_MAX_SIZE
                },
                'discoveries': {
                    'total': len(discovery_manager.get_all()['discoveries']),
                    'today': daemon_status.get('discoveries_today', 0)
                }
            }
        }
        
        return jsonify(health_data), 200
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'error': str(e)
        }), 500
```

---

## 5. Metrics Dashboard

### Prometheus + Grafana (Already integrated!)

The app already has Prometheus metrics. To visualize:

1. **Local Setup:**
   ```bash
   # Create prometheus.yml
   cat > prometheus.yml << EOF
   global:
     scrape_interval: 15s
   
   scrape_configs:
     - job_name: 'orion-octave'
       static_configs:
         - targets: ['ddd-lwhl.onrender.com:5000']
       metrics_path: '/metrics'
   EOF
   
   # Run Prometheus
   docker run -p 9090:9090 -v $(pwd)/prometheus.yml:/etc/prometheus/prometheus.yml prom/prometheus
   
   # Run Grafana
   docker run -p 3000:3000 grafana/grafana
   ```

2. **Configure Grafana:**
   - Open http://localhost:3000
   - Add Prometheus data source
   - Import dashboard for Flask apps
   - Create custom dashboards

---

## 6. Synthetic Monitoring

### Checkly (Free - 10 checks)

**Setup:**

1. Go to https://checklyhq.com
2. Create API check for key endpoints:
   - **Check 1:** Health endpoint
     ```javascript
     const response = await axios.get('https://ddd-lwhl.onrender.com/health')
     expect(response.status).toBe(200)
     expect(response.data.success).toBe(true)
     ```
   
   - **Check 2:** Analysis API
     ```javascript
     const response = await axios.post('https://ddd-lwhl.onrender.com/api/analyze', {
       side: 2.0,
       angle: 30.0
     })
     expect(response.status).toBe(200)
     expect(response.data.success).toBe(true)
     ```

3. **Run Frequency:** Every 5-10 minutes
4. **Alert on:** 2 consecutive failures

---

## 7. GitHub Actions Monitoring

Already set up! The CI/CD pipeline automatically monitors:

- ✅ Code quality (linting)
- ✅ Security vulnerabilities (Bandit)
- ✅ Test coverage
- ✅ Deployment success
- ✅ Post-deployment health check

**View Results:**
- https://github.com/matpng/ddd/actions

---

## 8. Database Monitoring

### Monitor PAK Database Health

Add to cron or GitHub Actions:

```python
# scripts/monitor_database.py
import os
from pak_database import PAKDatabase

def check_database_health():
    db = PAKDatabase('pak_intelligence.db')
    
    stats = db.get_statistics()
    
    health = {
        'total_goals': stats['total_goals'],
        'active_goals': sum(1 for g in db.get_active_goals() if g['status'] == 'active'),
        'total_discoveries': stats['total_goal_discoveries'],
        'db_size_mb': os.path.getsize('pak_intelligence.db') / (1024 * 1024)
    }
    
    # Alert if issues
    if health['db_size_mb'] > 100:
        print(f"WARNING: Database size is {health['db_size_mb']:.2f}MB")
    
    if health['active_goals'] == 0:
        print("WARNING: No active goals!")
    
    return health

if __name__ == '__main__':
    health = check_database_health()
    print(json.dumps(health, indent=2))
```

---

## 9. Alert Configuration

### Recommended Alert Thresholds

| Metric | Warning | Critical |
|--------|---------|----------|
| Response Time (p95) | > 1s | > 3s |
| Error Rate | > 1% | > 5% |
| Uptime | < 99% | < 95% |
| CPU Usage | > 70% | > 90% |
| Memory Usage | > 80% | > 95% |
| Discoveries per day | < 10 | < 5 |

### Notification Channels

1. **Email:** Primary alerts
2. **Slack:** Real-time notifications
3. **Discord:** Bot integration
4. **PagerDuty:** Critical only (paid)

---

## 10. Render-Specific Monitoring

### Native Render Features

1. **Metrics Tab:**
   - CPU usage
   - Memory usage
   - Request count
   - Response times

2. **Logs:**
   - Real-time log streaming
   - Search and filter
   - Export to external services

3. **Deploy Events:**
   - Email notifications
   - Webhook integration

**Configure Alerts:**
```bash
# Via Render Dashboard
Settings → Notifications
- Deploy Success/Failure
- Service Health
- Disk Usage (if using persistent disk)
```

---

## 11. Custom Monitoring Script

Create a monitoring script that runs weekly:

```yaml
# .github/workflows/weekly-health.yml
name: Weekly Health Check

on:
  schedule:
    - cron: '0 0 * * 0'  # Every Sunday at midnight
  workflow_dispatch:

jobs:
  health-check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Comprehensive Health Check
        run: |
          echo "🏥 Running comprehensive health check..."
          
          # Test all endpoints
          endpoints=(
            "/health"
            "/api/discoveries/status"
            "/api/daemon/health"
            "/api/ml/status"
          )
          
          for endpoint in "${endpoints[@]}"; do
            echo "Testing: $endpoint"
            curl -f "https://ddd-lwhl.onrender.com$endpoint" || exit 1
          done
          
          echo "✅ All endpoints healthy!"
      
      - name: Generate Report
        run: |
          echo "## Weekly Health Report" > report.md
          echo "Date: $(date)" >> report.md
          echo "" >> report.md
          echo "All systems operational ✅" >> report.md
      
      - name: Create Issue if Failed
        if: failure()
        uses: actions/github-script@v7
        with:
          script: |
            github.rest.issues.create({
              owner: context.repo.owner,
              repo: context.repo.repo,
              title: '🚨 Weekly Health Check Failed',
              body: 'The weekly health check has failed. Please investigate.',
              labels: ['bug', 'monitoring']
            })
```

---

## 12. Quick Setup Checklist

For immediate monitoring, do these in order:

- [ ] **5 min:** Set up UptimeRobot for https://ddd-lwhl.onrender.com/health
- [ ] **10 min:** Create Sentry account and add DSN to Render
- [ ] **5 min:** Enable Render email notifications
- [ ] **10 min:** Set up Papertrail for log aggregation
- [ ] **5 min:** Add GitHub Actions weekly health check
- [ ] **Optional:** Set up Grafana for Prometheus metrics

**Total Time:** ~30 minutes for essential monitoring

---

## 13. Next-Level Monitoring (Future)

### Advanced Features:
- **Distributed Tracing:** Jaeger/OpenTelemetry
- **Real User Monitoring (RUM):** Track actual user experience
- **Custom Dashboards:** Grafana with custom panels
- **Anomaly Detection:** ML-based alert thresholds
- **Performance Budgets:** Automated performance regression detection

---

## Contact & Support

**Monitoring Questions:**
- Sentry: https://docs.sentry.io
- UptimeRobot: https://uptimerobot.com/api
- Papertrail: https://papertrailapp.com/help

**App Monitoring Status:**
- Health: https://ddd-lwhl.onrender.com/health
- GitHub Actions: https://github.com/matpng/ddd/actions
- Render Dashboard: https://dashboard.render.com

---

**Last Updated:** 2025-12-16  
**Next Review:** After implementing Priority 2 items
