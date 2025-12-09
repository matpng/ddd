# API Documentation - AGI Integration Endpoints

## Overview

The Discovery System exposes several API endpoints specifically for AGI integration. These endpoints provide metrics, health status, and code access for autonomous monitoring and improvement.

**Base URL**: `http://localhost:5000` (development) or configured host in production

---

## Endpoints

### 1. GET `/api/agi/metrics`

**Purpose**: Retrieve runtime and business metrics for monitoring

**Authentication**: None (add in production)

**Rate Limit**: Applied via `@rate_limit` decorator

**Response**:
```json
{
  "runtime_metrics": {
    "error_rate": 0.01,
    "avg_latency_ms": 250,
    "requests_per_min": 60,
    "cache_size": 42,
    "cache_max": 100
  },
  "business_metrics": {
    "total_discoveries": 156,
    "discoveries_last_hour": 3,
    "active_daemon": true,
    "daemon_discoveries_today": 12
  },
  "timestamp": "2025-12-09T00:00:00.000000"
}
```

**Use Cases**:
- Monitor system performance
- Detect performance degradation
- Trigger optimization when error rate high

---

### 2. GET `/api/agi/health`

**Purpose**: Detailed health check with component status

**Response**:
```json
{
  "status": "healthy",
  "timestamp": "2025-12-09T00:00:00.000000",
  "components": {
    "flask": {
      "status": "healthy"
    },
    "cache": {
      "status": "healthy",
      "size": 42
    },
    "discovery_manager": {
      "status": "healthy",
      "total_discoveries": 156
    },
    "daemon": {
      "status": "running",
      "discoveries": 12
    }
  },
  "version": "1.0.0"
}
```

**Status Values**:
- `healthy`: All components operational
- `degraded`: Some components have issues
- `unhealthy`: Critical failures

---

### 3. GET `/api/agi/code/<path:filepath>`

**Purpose**: Retrieve source code files for analysis

**Parameters**:
- `filepath` (path): Relative path to file from project root

**Security**:
- ✅ Directory traversal protection
- ✅ Project directory boundary enforcement
- ✅ Binary file detection

**Example Request**:
```
GET /api/agi/code/orion_octave_test.py
```

**Success Response** (200):
```json
{
  "filepath": "orion_octave_test.py",
  "content": "#!/usr/bin/env python3\n...",
  "size_bytes": 28456,
  "lines": 887
}
```

**Error Responses**:
- 403: Access denied (path outside project)
- 404: File not found
- 400: Not a file (directory) or binary file

---

## AGI Integration Services

### MetricsService (TypeScript)

```typescript
import { MetricsService } from './integrations/metricsService';

const metrics = new MetricsService();

// Get runtime metrics
const runtime = await metrics.getRuntimeMetrics();
console.log('Error rate:', runtime.errorRate);

// Get health status
const health = await metrics.getHealthStatus();
console.log('System status:', health.status);
```

**Features**:
- Automatic retry (3 attempts with exponential backoff)
- 30-second caching
- Graceful fallback if Discovery offline

---

## Usage Examples

### Monitor Discovery System

```typescript
async function monitorDiscovery() {
    const metrics = new MetricsService();
    
    // Check every 60 seconds
    setInterval(async () => {
        const runtime = await metrics.getRuntimeMetrics();
        
        if (runtime.errorRate > 0.05) {
            console.warn('⚠️ High error rate detected!');
            // Trigger analysis and potential fixes
        }
        
        if (runtime.avgLatencyMs > 500) {
            console.warn('⚠️ High latency detected!');
            // Analyze performance bottlenecks
        }
    }, 60000);
}
```

### Analyze Code for Improvements

```typescript
async function analyzeCode() {
    const metrics = new MetricsService();
    
    // Get code file
    const response = await fetch('http://localhost:5000/api/agi/code/app.py');
    const data = await response.json();
    
    // Analyze code
    const issues = analyzeForIssues(data.content);
    
    // Create PR if issues found
    if (issues.length > 0) {
        const git = new GitService();
        await git.createPatchAndPR(
            diff,
            'agi-fix-issues',
            'AGI: Fix detected issues',
            'Automated fixes for code quality issues'
        );
    }
}
```

---

## Security Considerations

**⚠️ Current Status**: Endpoints are **not authenticated**

**Production Requirements**:
1. Add API key authentication
2. Implement rate limiting per client
3. Add request logging
4. Use HTTPS only
5. Implement IP whitelist if possible

**Recommended Auth Header**:
```
Authorization: Bearer <agi-api-key>
```

---

## Testing

### Manual Testing

```bash
# Test metrics endpoint
curl http://localhost:5000/api/agi/metrics | jq

# Test health endpoint
curl http://localhost:5000/api/agi/health | jq

# Test code retrieval
curl http://localhost:5000/api/agi/code/README.md | jq
```

### Integration Tests

```bash
cd agi-proto-system
npm test -- integration-services.test.ts
```

---

## Troubleshooting

**Issue**: `Connection refused`  
**Fix**: Ensure Discovery System is running on port 5000

**Issue**: `403 Access denied`  
**Fix**: File path must be relative and within project directory

**Issue**: `Stale metrics`  
**Fix**: Metrics are cached for 30s, clear cache with `clearCache()`

---

## Future Enhancements

- [ ] Add authentication middleware
- [ ] OpenAPI/Swagger documentation
- [ ] Webhook support for events
- [ ] Streaming metrics via WebSocket
- [ ] GraphQL endpoint for complex queries
