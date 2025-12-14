# Blueprint Deployment Fix Guide

## Issue
The deployment failed because `SECRET_KEY` was not generated during Blueprint deployment.

## Root Cause
When using Render Blueprint with `generateValue: true`, the SECRET_KEY should auto-generate, but if the service already exists or was created manually before, it might not have this value.

## Solution: Fix Existing Blueprint Deployment

### Step 1: Delete and Redeploy (Recommended)

1. **Go to Render Dashboard**: https://dashboard.render.com
2. **Delete the existing service**:
   - Click on `orion-octave-cubes` service
   - Go to **Settings** → Scroll to bottom
   - Click **Delete Web Service**
   - Confirm deletion

3. **Redeploy with Blueprint**:
   - Click **New** → **Blueprint**
   - Connect your GitHub repository `matpng/ddd`
   - Render will detect `render.yaml`
   - Click **Apply**
   - This time, `SECRET_KEY` will auto-generate properly

### Step 2: OR Add SECRET_KEY Manually (Quick Fix)

If you don't want to delete the service:

1. **Generate a SECRET_KEY**:
   ```bash
   python generate_secret_key.py
   ```
   
   Or manually:
   ```bash
   python3 -c 'import secrets; print(secrets.token_hex(32))'
   ```

2. **Add to Render**:
   - Go to https://dashboard.render.com
   - Select `orion-octave-cubes` service
   - Click **Environment** tab
   - Click **Add Environment Variable**
   - Key: `SECRET_KEY`
   - Value: (paste the generated secret)
   - Click **Save Changes**

3. **Trigger Manual Deploy**:
   - Go to **Manual Deploy** → **Deploy latest commit**

## Verification

After deployment completes, verify:

```bash
# Check if the service is running
curl https://your-app.onrender.com/health

# Should return:
# {"success": true, "status": "ok"}
```

## Why This Happened

The `render.yaml` has `generateValue: true` which should work, but:
- If service was created manually first, then Blueprint applied, values don't auto-generate
- Blueprint must create the service fresh for `generateValue` to work

## Updated render.yaml

The `render.yaml` has been fixed to properly use `generateValue: true` for Blueprint deployments.

## Next Steps

1. Choose either **Delete & Redeploy** (clean) or **Manual Fix** (quick)
2. Follow the steps above
3. Monitor deployment logs for success
4. Test the `/health` endpoint

## Support

If issues persist:
- Check Render logs for specific error messages
- Verify all environment variables are set correctly
- Ensure FLASK_ENV=production is set
- Contact Render support if Blueprint issues continue
