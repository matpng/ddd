# Deploying to Render.com

## 📋 Quick Setup Guide

### 1. **Render.com Configuration**

Fill in the Render web service form with these exact values:

```
Name: orion-octave-cubes
(or your preferred name)

Runtime: Python 3

Branch: main

Root Directory: 
(leave empty - uses repository root)

Build Command:
chmod +x build.sh && ./build.sh

Start Command:
chmod +x start.sh && ./start.sh
```

### 2. **Environment Variables**

Click "Advanced" and add these environment variables:

```
FLASK_ENV=production
SECRET_KEY=<generate-a-secure-random-key>
FLASK_HOST=0.0.0.0
PORT=10000
MAX_DISTANCE_PAIRS=50000
MAX_DIRECTION_PAIRS=25000
LOG_LEVEL=INFO
```

**To generate SECRET_KEY:**
```bash
python3 -c 'import secrets; print(secrets.token_hex(32))'
```

### 3. **Instance Type**

- **Free tier**: 512 MB RAM, 0.1 CPU (good for testing)
- **Starter ($7/month)**: 512 MB RAM, 0.5 CPU (recommended)
- **Standard ($25/month)**: 2 GB RAM, 1 CPU (for production)

**Recommendation**: Start with Free tier for testing, upgrade to Starter for production use.

### 4. **Auto-Deploy**

✅ Enable "Auto-Deploy" - Your app will redeploy automatically when you push to the main branch.

---

## 🔧 Detailed Configuration

### Build Process

The `build.sh` script will:
1. Upgrade pip
2. Install all dependencies from requirements.txt
3. Install gunicorn (production WSGI server)

### Start Process

The `start.sh` script will:
1. Start gunicorn with optimal settings
2. Bind to Render's PORT environment variable
3. Use 2 workers with 4 threads each
4. Configure logging for Render's log viewer

### Production Settings

Your app automatically detects production mode via `FLASK_ENV=production`:
- Debug mode: OFF ✓
- Caching: Enabled (LRU, max 100 items)
- Error details: Hidden from users
- Logging: INFO level
- Security: SECRET_KEY required

---

## 🚀 Deployment Steps

### Step 1: Connect Repository

1. Go to https://dashboard.render.com/
2. Click "New +" → "Web Service"
3. Connect your GitHub account (if not already)
4. Select repository: `matpng/ddd`

### Step 2: Configure Service

**Name**: `orion-octave-cubes`

**Language**: `Python 3`

**Branch**: `main`

**Build Command**:
```bash
chmod +x build.sh && ./build.sh
```

**Start Command**:
```bash
chmod +x start.sh && ./start.sh
```

### Step 3: Environment Variables

Click "Advanced" then "Add Environment Variable" for each:

| Key | Value |
|-----|-------|
| FLASK_ENV | production |
| SECRET_KEY | (generate with command above) |
| FLASK_HOST | 0.0.0.0 |
| PORT | 10000 |
| MAX_DISTANCE_PAIRS | 50000 |
| MAX_DIRECTION_PAIRS | 25000 |
| LOG_LEVEL | INFO |
| CACHE_MAX_SIZE | 100 |

### Step 4: Select Instance Type

- Free: Good for testing
- Starter ($7/mo): Recommended for light production use
- Standard ($25/mo): For heavy production use

### Step 5: Create Web Service

Click "Create Web Service" - Render will:
1. Clone your repository
2. Run build.sh (install dependencies)
3. Run start.sh (start gunicorn)
4. Assign a URL: `https://orion-octave-cubes.onrender.com`

⏱️ First deployment takes 2-5 minutes.

---

## ✅ Verify Deployment

Once deployed, visit your URL and check:

1. **Home page loads**: `https://your-app.onrender.com/`
2. **API works**: 
   - Open browser DevTools
   - Fill in parameters
   - Click "Run Analysis"
   - Check Network tab for `/api/analyze` response

3. **Logs are clean**:
   - Go to Render Dashboard → Your Service → Logs
   - Should see: "Starting Orion Octave Cubes..."
   - No error messages

---

## 🔍 Monitoring

### View Logs
Dashboard → Your Service → Logs

Look for:
```
Starting Orion Octave Cubes web application...
Environment: production
[INFO] Running analysis: side=2.0, angle=60.0
[INFO] Cache hit for 2.0_60.0_20000_8000
```

### Performance Metrics
Dashboard → Your Service → Metrics

Monitor:
- Response times
- Memory usage
- CPU usage
- Request counts

---

## 🐛 Troubleshooting

### Issue: Build fails

**Check**: requirements.txt has all dependencies
```bash
git log --oneline -1  # Verify latest commit pushed
```

**Solution**: Ensure gunicorn is in requirements.txt (already added)

### Issue: App crashes on start

**Check**: Environment variables are set correctly

**Solution**: 
1. Verify SECRET_KEY is set
2. Check FLASK_ENV=production
3. Review logs for specific error

### Issue: Import errors

**Check**: All Python files committed

**Solution**:
```bash
git status
git add <missing-files>
git commit -m "Add missing files"
git push origin main
```

### Issue: Slow performance

**Upgrade**: Consider Starter or Standard instance

**Optimize**: Reduce MAX_DISTANCE_PAIRS and MAX_DIRECTION_PAIRS

---

## 📊 Performance Tips

1. **Enable Caching**: Already configured (CACHE_MAX_SIZE=100)
2. **Adjust Sample Sizes**: Lower values = faster computation
3. **Monitor Memory**: Use Render metrics
4. **Scale Up**: Upgrade instance type if needed

---

## 🔄 Updating Your App

When you push to GitHub:
```bash
git add .
git commit -m "Update app"
git push origin main
```

Render automatically:
1. Detects push
2. Runs build.sh
3. Restarts with start.sh
4. Zero-downtime deployment ✓

---

## 💰 Costs

- **Free**: $0 (sleeps after 15 min inactivity, 750 hours/month)
- **Starter**: $7/month (always on, better performance)
- **Standard**: $25/month (production-grade)

---

## 🎯 Production Checklist

Before going live:

- [ ] SECRET_KEY set to secure random value
- [ ] FLASK_ENV=production
- [ ] Auto-deploy enabled
- [ ] Instance type selected (Starter recommended)
- [ ] Environment variables verified
- [ ] Test API endpoints work
- [ ] Check logs for errors
- [ ] Monitor first few requests
- [ ] Set up custom domain (optional)

---

## 🌐 Custom Domain (Optional)

1. Dashboard → Your Service → Settings → Custom Domains
2. Add your domain
3. Update DNS records as shown
4. Wait for SSL certificate (automatic, ~5 minutes)

---

## 📞 Support

- **Render Docs**: https://render.com/docs
- **Your App Logs**: Render Dashboard → Logs
- **Issues**: https://github.com/matpng/ddd/issues

---

**Your production URL will be**: `https://orion-octave-cubes.onrender.com`
(or your chosen name)

🚀 **Ready to deploy!**
