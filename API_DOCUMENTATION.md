# Orion Octave Cubes - API Documentation

## Base URL
- **Local Development:** `http://localhost:5000`
- **Production:** `https://your-app-url.com`

## Table of Contents
1. [Analysis Endpoints](#analysis-endpoints)
2. [Discovery Endpoints](#discovery-endpoints)
3. [Status Endpoints](#status-endpoints)
4. [Download Endpoints](#download-endpoints)

---

## Analysis Endpoints

### POST /api/analyze
Run geometric analysis on two interpenetrating cubes.

**Request Body:**
```json
{
  "side": 2.0,
  "angle": 30.0,
  "max_distance_pairs": 20000,
  "max_direction_pairs": 8000
}
```

**Parameters:**
- `side` (float, required): Cube side length (0.01 - 100)
- `angle` (float, required): Rotation angle in degrees (0 - 360)
- `max_distance_pairs` (int, optional): Maximum distance pairs to analyze
- `max_direction_pairs` (int, optional): Maximum direction pairs to analyze

**Response:** (200 OK)
```json
{
  "success": true,
  "cache_key": "2.0_30.0_20000_8000",
  "summary": {
    "configuration": {
      "side_length": 2.0,
      "rotation_angle_degrees": 30.0,
      "rotation_axis": "z"
    },
    "point_counts": {
      "unique_points": 24,
      "edge_face_intersections": 16,
      "edge_edge_intersections": 0
    },
    "distance_stats": {
      "unique_distances": 15,
      "min": 0.5,
      "max": 3.5,
      "mean": 2.1,
      "std": 0.8
    },
    "golden_ratio": {
      "candidate_count": 2,
      "candidates": [[1.0, 1.618, 1.618]]
    },
    "special_angles": {
      "30.0": {"count": 45, "description": "30° angles"},
      "60.0": {"count": 38, "description": "60° angles"},
      "90.0": {"count": 52, "description": "90° angles"}
    },
    "icosahedral_check": {
      "has_icosahedral_symmetry": false,
      "confidence": 0.0
    }
  }
}
```

**Error Responses:**
- `400 Bad Request`: Invalid parameters
```json
{
  "success": false,
  "error": "Parameter validation error",
  "details": "side must be between 0.01 and 100"
}
```

- `500 Internal Server Error`: Computation error
```json
{
  "success": false,
  "error": "Analysis failed"
}
```

---

## Discovery Endpoints

### GET /api/discoveries/status
Get autonomous discovery daemon status.

**Response:** (200 OK)
```json
{
  "success": true,
  "status": {
    "running": true,
    "discoveries_today": 5,
    "last_discovery": "2025-12-07T10:30:00.000Z",
    "total_discoveries": 142,
    "started_at": "2025-12-07T08:00:00.000Z"
  }
}
```

### GET /api/discoveries/latest
Get latest autonomous discoveries.

**Query Parameters:**
- `count` (int, optional, default=10): Number of discoveries to return

**Example:** `GET /api/discoveries/latest?count=5`

**Response:** (200 OK)
```json
{
  "success": true,
  "count": 5,
  "discoveries": [
    {
      "id": "autonomous_angle_sweep_103045",
      "type": "autonomous_angle_sweep",
      "timestamp": "2025-12-07T10:30:45.123Z",
      "date": "2025-12-07",
      "summary": {
        "unique_points": 26,
        "golden_ratio_candidates": 3,
        "exceptional": "Multiple golden ratio candidates"
      }
    }
  ]
}
```

### GET /api/discoveries/all
Get all discoveries with pagination.

**Query Parameters:**
- `limit` (int, optional, default=50): Number of results per page
- `offset` (int, optional, default=0): Pagination offset

**Example:** `GET /api/discoveries/all?limit=20&offset=40`

**Response:** (200 OK)
```json
{
  "success": true,
  "total": 142,
  "limit": 20,
  "offset": 40,
  "discoveries": [...]
}
```

### GET /api/discoveries/{discovery_id}
Get a specific discovery by ID.

**Example:** `GET /api/discoveries/autonomous_angle_sweep_103045`

**Response:** (200 OK)
```json
{
  "success": true,
  "discovery": {
    "id": "autonomous_angle_sweep_103045",
    "type": "autonomous_angle_sweep",
    "timestamp": "2025-12-07T10:30:45.123Z",
    "date": "2025-12-07",
    "data": {
      "angle": 45,
      "summary": {...},
      "full_results": {...}
    }
  }
}
```

**Error:** (404 Not Found)
```json
{
  "success": false,
  "error": "Discovery not found"
}
```

### GET /api/discoveries/stats
Get discovery statistics.

**Response:** (200 OK)
```json
{
  "success": true,
  "stats": {
    "total_discoveries": 142,
    "discoveries_by_type": {
      "autonomous_angle_sweep": 50,
      "golden_ratio_sweep": 30,
      "symmetry_sweep": 35,
      "parameter_sweep": 27
    },
    "discoveries_by_date": {
      "2025-12-07": 5,
      "2025-12-06": 12,
      "2025-12-05": 15
    },
    "latest_discovery": {...},
    "last_updated": "2025-12-07T10:30:45.000Z"
  }
}
```

### GET /api/discoveries/search
Search discoveries with filters.

**Query Parameters:**
- `q` (string, optional): Search query
- `type` (string, optional): Discovery type filter
- `date` (string, optional): Date filter (YYYY-MM-DD)

**Example:** `GET /api/discoveries/search?type=golden_ratio_sweep&date=2025-12-07`

**Response:** (200 OK)
```json
{
  "success": true,
  "count": 3,
  "discoveries": [...]
}
```

### GET /api/discoveries/exceptional
Get discoveries with exceptional patterns.

**Response:** (200 OK)
```json
{
  "success": true,
  "count": 8,
  "discoveries": [
    {
      "id": "...",
      "summary": {
        "exceptional": "Multiple golden ratio candidates",
        "golden_ratio_candidates": 5,
        "unique_points": 48
      }
    }
  ]
}
```

---

## Status Endpoints

### GET /
Main dashboard page (HTML).

### GET /discoveries
Discoveries dashboard page (HTML).

---

## Download Endpoints

### GET /api/download/{cache_key}
Download analysis results as JSON.

**Example:** `GET /api/download/2.0_30.0_20000_8000`

**Response:** (200 OK)
- Content-Type: `application/json`
- Content-Disposition: `attachment; filename="analysis_2.0_30.0.json"`

**Body:** Complete analysis JSON

### GET /api/plot/{plot_type}/{cache_key}
Generate and download plot as PNG.

**Plot Types:**
- `3d`: 3D scatter plot of interference points
- `distance`: Distance spectrum histogram
- `angle`: Angle distribution scatter plot
- `summary`: Combined summary plot

**Example:** `GET /api/plot/3d/2.0_30.0_20000_8000`

**Response:** (200 OK)
- Content-Type: `image/png`

---

## Rate Limiting

Currently not implemented. Future versions may include:
- 60 requests per minute per IP
- 1000 requests per hour per IP

---

## Error Codes

| Code | Meaning |
|------|---------|
| 200 | Success |
| 400 | Bad Request - Invalid parameters |
| 404 | Not Found - Resource doesn't exist |
| 500 | Internal Server Error - Computation failed |

---

## Response Format

All JSON responses follow this pattern:
```json
{
  "success": true/false,
  "data": {...},          // On success
  "error": "message",     // On failure
  "details": "..."        // Optional error details (dev mode only)
}
```

---

## Examples

### Python
```python
import requests

# Run analysis
response = requests.post('http://localhost:5000/api/analyze', json={
    'side': 2.0,
    'angle': 45.0,
    'max_distance_pairs': 10000,
    'max_direction_pairs': 5000
})

result = response.json()
cache_key = result['cache_key']

# Download results
download_response = requests.get(f'http://localhost:5000/api/download/{cache_key}')
with open('analysis.json', 'wb') as f:
    f.write(download_response.content)

# Get latest discoveries
discoveries = requests.get('http://localhost:5000/api/discoveries/latest?count=10')
print(discoveries.json())
```

### JavaScript
```javascript
// Run analysis
const response = await fetch('http://localhost:5000/api/analyze', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    side: 2.0,
    angle: 45.0,
    max_distance_pairs: 10000,
    max_direction_pairs: 5000
  })
});

const result = await response.json();
console.log(result.summary);

// Get daemon status
const status = await fetch('http://localhost:5000/api/discoveries/status');
const statusData = await status.json();
console.log('Discoveries today:', statusData.status.discoveries_today);
```

### cURL
```bash
# Run analysis
curl -X POST http://localhost:5000/api/analyze \
  -H "Content-Type: application/json" \
  -d '{"side": 2.0, "angle": 30.0}'

# Get latest discoveries
curl "http://localhost:5000/api/discoveries/latest?count=5"

# Download plot
curl "http://localhost:5000/api/plot/3d/2.0_30.0_20000_8000" -o plot.png
```

---

## Changelog

### v1.0.0 (2025-12-07)
- Initial API release
- Analysis endpoint
- Discovery endpoints
- Plot generation
- Download functionality
