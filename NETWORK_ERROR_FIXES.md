# Network Error Troubleshooting & Fixes

## Issues Identified and Fixed (December 7, 2025)

### 1. ✅ Frontend Network Error - FIXED

**Problem:**
- JavaScript trying to access `/api/discoveries/status` before server fully initialized
- Undefined/null property access causing crashes
- No graceful degradation for offline state

**Root Cause:**
```javascript
// Old code - crashed if health object was undefined
icon.textContent = status.running && health.heartbeat_healthy ? '🟢' : '🔴';
```

**Fix Applied:**
- Added null/undefined checks for all health properties
- Added HTTP response status validation
- Improved error handling with visual feedback
- Graceful fallback to "Offline - Retrying..." state

**New Code:**
```javascript
const status = data.status || {};
const health = data.health || {};
const isHealthy = status.running && (health.heartbeat_healthy !== false);
icon.textContent = isHealthy ? '🟢' : '🔴';
```

---

### 2. ✅ Server-Side Error Handling - FIXED

**Problem:**
- `/api/discoveries/status` endpoint crashed if daemon_monitor not initialized
- No fallback for monitor status failures
- 500 errors returned without useful data

**Root Cause:**
```python
# Old code - failed if monitor not ready
monitor_status = daemon_monitor.get_status()  # Could raise exception
```

**Fix Applied:**
- Added try-catch for monitor status retrieval
- Fallback health object with safe defaults
- Still returns partial data even on error (500 with fallback health)

**New Code:**
```python
try:
    monitor_status = daemon_monitor.get_status()
except Exception as monitor_error:
    logger.warning(f"Could not get monitor status: {monitor_error}")
    monitor_status = {
        'is_running': False,
        'health_score': 0,
        'heartbeat_healthy': False,
        # ... safe defaults
    }
```

---

### 3. ✅ Auto-Refresh Network Resilience - FIXED

**Problem:**
- Fetch errors stopped auto-refresh polling
- No retry mechanism
- Silent failures (errors only in console)

**Fix Applied:**
- Errors don't stop the polling interval
- Visual feedback when offline (🔴 + "Offline - Retrying...")
- Detailed console logging for debugging
- HTTP status code checking

**Behavior:**
- Polls every 10 seconds regardless of errors
- Shows offline state visually
- Automatically recovers when server comes back online

---

## Common Network Issues & Solutions

### Issue: "Failed to fetch" Error

**Symptoms:**
- Console shows: `TypeError: Failed to fetch`
- Status shows "Offline - Retrying..."
- Red dot (🔴) indicator

**Causes:**
1. Server not running
2. Wrong port (should be 5000)
3. CORS issues (if accessing from different origin)
4. Firewall blocking connection

**Solutions:**

```bash
# 1. Check if server is running
# Look for: "Running on http://0.0.0.0:5000"
python app.py

# 2. Check if port 5000 is accessible
netstat -an | findstr :5000

# 3. Access from correct URL
http://localhost:5000  # ✅ Correct
http://127.0.0.1:5000  # ✅ Also correct
```

---

### Issue: 500 Internal Server Error

**Symptoms:**
- HTTP 500 response
- Error in server logs
- Status endpoint failing

**Causes:**
1. Missing dependencies (psutil, flask, etc.)
2. Import errors
3. Database/file permission issues

**Solutions:**

```bash
# 1. Install all dependencies
pip install -r requirements.txt

# 2. Check for import errors
python -c "from daemon_monitor import daemon_monitor; print('OK')"
python -c "from discovery_manager import DiscoveryManager; print('OK')"

# 3. Create required directories
mkdir autonomous_discoveries test_results logs
```

---

### Issue: Status Updates Not Working

**Symptoms:**
- Counts stay at "-" or 0
- No health score updates
- Green/red dot not changing

**Causes:**
1. Daemon not started
2. JavaScript polling not active
3. DOM elements not found

**Debug Steps:**

```javascript
// Open browser console (F12)
// You should see every 10 seconds:
// "Updating autonomous status..." (if working)
// or error messages (if failing)

// Manual test:
fetch('/api/discoveries/status')
  .then(r => r.json())
  .then(d => console.log(d));
```

**Solutions:**

```bash
# 1. Verify daemon is enabled
export ENABLE_AUTONOMOUS=true
python app.py

# 2. Check server logs
# Should see: "Autonomous daemon thread started"
# Should see: "Starting autonomous discovery daemon..."

# 3. Test endpoint directly
curl http://localhost:5000/api/discoveries/status
```

---

### Issue: CORS Errors (Cross-Origin)

**Symptoms:**
- Browser console: "CORS policy" error
- Accessing from different domain/port

**Cause:**
Accessing app from different origin (e.g., loading HTML file locally)

**Solution:**

```python
# Add to app.py (if needed for development)
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes
```

Or just access directly: `http://localhost:5000`

---

## Testing Network Connectivity

### 1. Test Server is Running

```bash
# Windows PowerShell
Test-NetConnection localhost -Port 5000

# Or use curl
curl http://localhost:5000
```

### 2. Test Specific Endpoints

```bash
# Status endpoint
curl http://localhost:5000/api/discoveries/status

# Health endpoint
curl http://localhost:5000/api/daemon/health

# Should return JSON with success: true
```

### 3. Test from Browser Console

```javascript
// F12 to open console, then:

// Test fetch
fetch('/api/discoveries/status')
  .then(r => {
    console.log('Status:', r.status);
    return r.json();
  })
  .then(d => console.log('Data:', d))
  .catch(e => console.error('Error:', e));

// Test auto-refresh is working
console.log('Interval ID:', statusUpdateInterval);
```

---

## Network Error Prevention Checklist

- ✅ All fetch calls wrapped in try-catch
- ✅ HTTP status codes checked before parsing JSON
- ✅ Null/undefined checks for all object properties
- ✅ Fallback values for missing data
- ✅ Visual feedback for offline state
- ✅ Server-side error handling with fallbacks
- ✅ Detailed error logging (console + server)
- ✅ Auto-retry mechanism (polling continues)
- ✅ Graceful degradation (partial data on errors)

---

## Quick Fix Summary

1. **Frontend**: Added null checks, HTTP validation, offline indicators
2. **Backend**: Added try-catch, fallback health object, better logging
3. **Polling**: Resilient to errors, visual feedback, auto-recovery
4. **Error Messages**: Detailed console logs for debugging

All network errors are now handled gracefully with automatic recovery!
