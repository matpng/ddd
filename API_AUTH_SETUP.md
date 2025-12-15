# API Authentication Setup Guide

## Quick Setup for Render

### 1. Generate API Token

Run locally:
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

**Copy the output** - this is your API token.

### 2. Add to Render Environment

1. Go to https://dashboard.render.com
2. Select your `orion-octave-cubes` service (or `ddd-lwhl`)
3. Click **Environment** tab
4. Click **Add Environment Variable**
5. Set:
   - **Key:** `AGI_API_TOKEN`
   - **Value:** (paste your generated token)
6. Click **Save Changes**

Render will auto-redeploy with the new token.

### 3. Test Authentication

#### Without Token (Should Fail)
```bash
curl https://ddd-lwhl.onrender.com/api/agi/health
```

**Expected Response:**
```json
{
  "error": "Missing Authorization header",
  "message": "Include: Authorization: Bearer <token>"
}
```

#### With Token (Should Succeed)
```bash
export AGI_API_TOKEN="your-token-here"

curl -H "Authorization: Bearer $AGI_API_TOKEN" \
     https://ddd-lwhl.onrender.com/api/agi/health
```

**Expected Response:**
```json
{
  "status": "healthy",
  "timestamp": "2025-12-15T...",
  "components": {...},
  "version": "1.0.0"
}
```

## Protected Endpoints

All AGI integration endpoints now require authentication:

| Endpoint | Permission | Purpose |
|----------|------------|---------|
| `/api/agi/metrics` | `read` | Runtime metrics |
| `/api/agi/health` | `read` | Health status |
| `/api/agi/system/stats` | `read` | System statistics |
| `/api/agi/code/<path>` | `admin` | Source code access |

## Token Permissions

The default token has all permissions:
- `read` - Access metrics and health data
- `write` - Modify settings (not currently used)
- `admin` - Access source code and system internals

## For AGI System Integration

Update your AGI system's `.env` file:

```bash
# AGI Proto-System .env
AGI_API_TOKEN=your-token-here
DISCOVERY_API_URL=https://ddd-lwhl.onrender.com
```

Then in your AGI code:
```typescript
const response = await fetch(`${process.env.DISCOVERY_API_URL}/api/agi/health`, {
  headers: {
    'Authorization': `Bearer ${process.env.AGI_API_TOKEN}`
  }
});
```

## Security Notes

- ⚠️ **Keep tokens secret** - Never commit to version control
- 🔄 **Rotate regularly** - Generate new tokens periodically
- 📝 **Log access** - API calls are logged for security audit
- 🚫 **Limit permissions** - Use minimal required permissions

## Troubleshooting

### 401 Unauthorized
- Check Authorization header format: `Bearer <token>`
- Verify token is set in Render environment

### 403 Forbidden
- Token is valid but lacks required permission
- `/api/agi/code/*` requires `admin` permission

### Token Not Working
1. Check token is correctly set in Render
2. Verify no extra spaces in token value
3. Redeploy service after adding token
