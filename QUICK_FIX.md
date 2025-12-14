# Quick Fix: Render Blueprint Deployment

## Problem
Your Render deployment is failing with:
```
ValueError: SECRET_KEY environment variable must be set in production
```

## Solution: Use Blueprint Fresh Deploy

### Step 1: Delete Existing Service (if any)

1. Go to https://dashboard.render.com
2. Find your `orion-octave-cubes` service
3. Click on it → **Settings** (scroll to bottom)
4. Click **Delete Web Service**
5. Confirm deletion

### Step 2: Deploy with Blueprint

1. Click **New** → **Blueprint**
2. Connect your GitHub repository: `matpng/ddd`
3. Render will automatically detect `render.yaml`
4. Review the configuration
5. Click **Apply**

### Step 3: Wait for Deployment

Blueprint will automatically:
- Create a new web service called `orion-octave-cubes`
- **AUTO-GENERATE** the `SECRET_KEY` (no manual setup needed!)
- Configure all environment variables from `render.yaml`
- Build the Docker image
- Start the application

Deployment usually takes 2-5 minutes.

### Step 4: Verify

Once deployed, test your application:

```bash
curl https://your-app.onrender.com/health
```

Expected response:
```json
{"success": true, "status": "ok"}
```

## Why This Works

- `render.yaml` has `generateValue: true` for `SECRET_KEY`
- When Blueprint creates a **new** service, it automatically generates secure random values
- If you manually create a service first, then apply Blueprint, it doesn't generate the value
- That's why deleting and redeploying fresh is the cleanest solution

## Alternative: Manual Fix (If You Don't Want to Delete)

If you prefer not to delete the existing service:

1. Run: `python deploy_blueprint.py`
2. Choose option **[2] UPDATE EXISTING SERVICE**
3. Follow the instructions to manually add `SECRET_KEY`

## Files Updated

- ✅ `render.yaml` - Fixed to use `generateValue: true` for Blueprint
- ✅ `deploy_blueprint.py` - Interactive deployment helper
- ✅ `BLUEPRINT_DEPLOY_FIX.md` - Detailed troubleshooting guide
- ✅ `generate_secret_key.py` - Standalone secret key generator

## Next Steps

1. Delete service in Render Dashboard
2. Deploy with Blueprint (New → Blueprint)
3. Monitor deployment logs
4. Test `/health` endpoint
5. Done! 🎉

## Need Help?

- **Full guide**: See `BLUEPRINT_DEPLOY_FIX.md`
- **Interactive helper**: Run `python deploy_blueprint.py`
- **Generate key only**: Run `python generate_secret_key.py`
