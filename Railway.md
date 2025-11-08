# 🚀 Setup Guide

## 🔧 Step 1: Prepare Data Files

### Option A: Use Available Data

1. Download from scraping repo: (https://github.com/LightnXd/Zus_Scraper)
   - `data/products_drinkware.jsonl`
   - `data/outlets_kuala_lumpur_selangor.jsonl`
   - `data/outlets_metadata.json`

2. Place in `root/data/` folder

### Option B: Generate new Data

1. Clone scraping repo
2. Run the project
3. Copy the new data folder to `root/data/`

### ✅ Verify Data Structure

```
root/
├── data/
│   ├── products_drinkware.jsonl                ✅ 35 products
│   ├── outlets_kuala_lumpur_selangor.jsonl     ✅ 253 outlets (JSONL format)
│   └── outlets_metadata.json                   ✅ Metadata
```

## 🚂 Step 2: Deploy to Railway

### 1. Create New Project

1. Go to [railway.app](https://railway.app/new)
2. Click **"New Project"**
3. Select **"Deploy from GitHub repo"**
4. Choose your repository that have this project
5. Railway will auto-detect the Dockerfile

### 2. Configure Environment Variables

In Railway dashboard, add these variables:

```bash
# Groq API (Required)
GROQ_API_KEY=your_groq_api_key_here

# Supabase (Required)
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your_supabase_anon_key

# CORS (Update after frontend deployed)
CORS_ORIGINS=http://localhost:3000,https://your-frontend.vercel.app

# Port (Railway auto-assigns)
PORT=8000
```

### 3. Configure Deployment Settings

Railway should auto-detect from `railway.json`:

```json
{
  "build": {
    "builder": "DOCKERFILE",
    "dockerfilePath": "Dockerfile"
  },
  "deploy": {
    "startCommand": "ollama serve & sleep 3 && python api_server_chroma.py",
    "restartPolicyType": "ON_FAILURE",
    "restartPolicyMaxRetries": 10
  }
}
```

### 3. Deploy

1. Railway will automatically start building
2. Build process (~5-10 minutes):
   - ✅ Pull Python 3.11 image
   - ✅ Install Ollama
   - ✅ Install Python dependencies
   - ✅ Copy data files
   - ✅ Pull Ollama embedding model (`mxbai-embed-large`)
   - ✅ Run `setup_backend.py` (builds Chroma DB)
   - ✅ Start API server

3. Once deployed, Railway will show your URL:
   ```
   https://your-app-name.up.railway.app
   ```

---

## ✅ Step 4: Verify Deployment

### 1. Health Check

```bash
curl https://your-app-name.up.railway.app/health
```

**Expected Response:**
```json
{
  "status": "healthy",
  "timestamp": "2025-11-08T12:00:00Z"
}
```

### 2. Test Chat Endpoint

```bash
curl -X POST https://your-app-name.up.railway.app/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Show me tumblers"}'
```

**Expected Response:**
```json
{
  "response": "We have several tumblers available...",
  "timestamp": "2025-11-08T12:00:00Z"
}
```

### 3. Check Stats

```bash
curl https://your-app-name.up.railway.app/api/stats
```

**Expected Response:**
```json
{
  "total_products": 35,
  "total_outlets": 253,
  "vector_db": "chroma",
  "embedding_model": "mxbai-embed-large"
}
```
---

## 📚 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check |
| `/api/chat` | POST | Chat with AI |
| `/api/stats` | GET | Database statistics |
| `/api/outlets` | GET | List all outlets |
| `/api/outlets/nearby` | GET | Find nearby outlets |

---

## 🎯 Next Steps After Deployment

1. ✅ Copy Railway URL: `https://your-app-name.up.railway.app`
2. ✅ Update frontend `.env.production`:
   ```bash
   VITE_API_URL=https://your-app-name.up.railway.app
   ```
3. ✅ Update backend `CORS_ORIGINS` with Vercel URL
4. ✅ Deploy frontend to Vercel
5. ✅ Test end-to-end chat functionality

---

## 🛠️ Troubleshooting

### Issue: Ollama Installation Fails (Connection Reset / Timeout)

**Error you might see:**
```
curl: (55) Send failure: Connection reset by peer
tar: Unexpected EOF in archive
ERROR: failed to build: exit code: 2
```

**Cause:** Network timeout during Ollama download in Railway's build environment

**Solution 1: Retry the deployment (Recommended)**
- Railway's network can be unstable during builds
- The Dockerfile now has automatic retry logic (3 attempts)
- Simply click **"Redeploy"** in Railway dashboard
- Most builds succeed on 2nd or 3rd attempt

**Solution 2: Increase build timeout**
1. Go to Railway project **Settings**
2. Navigate to **Deploy** > **Build timeout**
3. Increase to `30 minutes` (default is 20)
4. Redeploy

**Solution 3: Use runtime setup (more reliable but slower first start)**

If builds keep failing, use this alternative approach:

1. Create new file `Dockerfile.railway` in your repo:

```dockerfile
# Use Python 3.11 slim image
FROM python:3.11-slim

# Install system dependencies with retries
RUN apt-get update && apt-get install -y \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Install Ollama with multiple retry attempts
RUN set -e; \
    MAX_RETRIES=5; \
    for i in $(seq 1 $MAX_RETRIES); do \
        echo "Attempt $i of $MAX_RETRIES..."; \
        curl -fsSL https://ollama.com/install.sh | sh && break || \
        if [ $i -eq $MAX_RETRIES ]; then \
            echo "Failed after $MAX_RETRIES attempts"; \
            exit 1; \
        fi; \
        sleep 10; \
    done && \
    which ollama && ollama --version

WORKDIR /app

# Copy requirements and install dependencies
COPY requirements-minimal.txt .
RUN pip install --no-cache-dir -r requirements-minimal.txt && \
    pip install --no-cache-dir langchain langchain-groq langchain-chroma langchain-ollama chromadb supabase

# Copy application code
COPY . .

# Expose port
EXPOSE 8000

# Runtime setup: Pull model and initialize on first start
CMD set -e; \
    echo "Starting Ollama service..."; \
    ollama serve > /tmp/ollama.log 2>&1 & \
    OLLAMA_PID=$!; \
    sleep 8; \
    echo "Pulling embedding model..."; \
    ollama pull mxbai-embed-large || (cat /tmp/ollama.log && exit 1); \
    echo "Running backend setup..."; \
    python setup_backend.py || (cat /tmp/ollama.log && exit 1); \
    echo "Starting API server..."; \
    exec python api_server_chroma.py
```

2. In Railway dashboard:
   - Go to **Settings** > **Deploy**
   - Change **Dockerfile Path** to `Dockerfile.railway`
   - Click **"Redeploy"**

**Trade-off:** First startup takes ~5 minutes (model download + setup), but more reliable builds

---

### Issue: "Data files not found"

**Cause:** `data/` folder not committed to git

**Solution:**
```bash
# Verify .gitignore doesn't ignore data/
git add data/ -f
git commit -m "Add data files for deployment"
git push
```

---

### Issue: "Chroma DB build failed"

**Cause:** Ollama service not ready when setup runs

**Solution:** The improved Dockerfile now waits longer (10 seconds). If still failing:
1. Check Railway logs for specific error
2. Verify data files are valid JSON/JSONL
3. Try redeploying

---

### Issue: CORS errors in frontend

**Cause:** Frontend URL not in allowed origins

**Solution:** Update `CORS_ORIGINS` environment variable in Railway:
```bash
CORS_ORIGINS=http://localhost:3000,https://your-frontend.vercel.app
```

---

### Issue: 500 Internal Server Error

**Check these in order:**

1. **Railway logs** - Click on deployment > View logs
2. **Environment variables** - Verify all are set correctly
3. **Supabase connection** - Check SUPABASE_URL and SUPABASE_KEY
4. **Groq API key** - Verify it's valid
5. **Data files** - Ensure committed to repo

---

### Issue: Build succeeds but app crashes on startup

**Common causes:**
- Missing environment variable
- Supabase credentials invalid
- Groq API key invalid

**Solution:**
1. Check Railway logs: **Deployments** > Click latest > **View Logs**
2. Look for error messages
3. Verify all env vars are set correctly

---

## 📊 Expected Railway Resource Usage

- **Memory:** 1-2 GB
- **CPU:** 0.5-1 vCPU  
- **Storage:** 2-3 GB (Ollama model + dependencies)
- **Build Time:** 8-15 minutes (with retries)
- **First Start:** 2-3 minutes
- **Cost:** ~$10-20/month (Hobby plan)

---

## 🆘 Need Help?

1. Check Railway build logs
2. Check Railway deploy logs
3. Check application logs in Railway dashboard
4. Verify environment variables are set
5. Verify data files are in git repository

---

**Deployment Status:** Ready to deploy! 🚀

All required files are configured correctly.
