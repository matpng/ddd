# Force Render Deployment

## Current Status

Render is deploying **OLD CODE** (commit `3360102`) instead of the fixed version (commit `867cfb2`).

## Evidence
- Logs show error at line 2558: `@app.route('/api/agi/health')` causing decorator conflict
- This is the OLD code - the fix changed it to `@rate_limit()` with parentheses
- Commit `867cfb2` was pushed successfully to GitHub

## Possible Causes

1. **Auto-deploy not triggered** - Render didn't detect the push
2. **Cached build** - Render is using cached Docker image
3. **Wrong branch** - Render configured to deploy from wrong branch
4. **Deployment paused** - Manual intervention required

## Solutions to Try

###  Option 1: Manual Deploy in Render Dashboard (RECOMMENDED)

1. Go to https://dashboard.render.com
2. Select your `orion-octave-cubes` service (or `ddd-lwhl`)
3. Click **Manual Deploy** dropdown
4. Select **Deploy latest commit** or **Clear build cache & deploy**
5. Monitor logs for the new deployment

### Option 2: Force Push (Bypass Cache)

```bash
# Make a trivial change to force new deployment
git commit --allow-empty -m "Force Render redeploy with fixes"
git push origin main
```

### Option 3: Check Render Configuration

In Render Dashboard:
1. Go to service Settings
2. Verify:
   - **Branch**: Should be `main`
   - **Auto-Deploy**: Should be `Yes`
   - **Build Command**: Should use Dockerfile
3. If auto-deploy is OFF, turn it ON and trigger manual deploy

## Verification

After redeployment, you should see in logs:
```
✓ Security middleware initialized
✓ Prometheus metrics configured
✓ Autonomous daemon started
[INFO] Booting worker with pid: X
```

NO MORE:
```
AssertionError: View function mapping is overwriting...
```

## Next Steps

1. **Try Manual Deploy first** (quickest)
2. If that fails, clear build cache
3. If still failing, check branch configuration
4. Monitor deployment logs carefully
