# 🚀 Railway Deployment Guide - ZUS Backend

Complete guide to deploy the ZUS Drinkware chatbot backend to Railway.

---

## 📋 Prerequisites

- Railway account ([railway.app](https://railway.app))
- GitHub account
- Groq API key ([console.groq.com](https://console.groq.com))
- Supabase project ([supabase.com](https://supabase.com))

---

## 🔧 Step 1: Prepare Data Files

### Option A: Copy from Scraping Repo (Recommended)

```bash
# Clone scraping repository
git clone https://github.com/YOUR_USERNAME/zus-scraping.git

# Copy data files to backend
cd backend
cp -r ../zus-scraping/data/ ./data/

# Verify files
ls data/
# Should show:
# - products_drinkware.jsonl
# - outlets_kuala_lumpur_selangor.jsonl
# - outlets_metadata.json
```

### Option B: Download Data Manually

1. Download from scraping repo:
   - `data/products_drinkware.jsonl`
   - `data/outlets_kuala_lumpur_selangor.jsonl`
   - `data/outlets_metadata.json`

2. Place in `backend/data/` folder

### ✅ Verify Data Structure

```
backend/
├── data/
│   ├── products_drinkware.jsonl                ✅ 35 products
│   ├── outlets_kuala_lumpur_selangor.jsonl     ✅ 253 outlets (JSONL format)
│   └── outlets_metadata.json                   ✅ Metadata
```

---

## 📦 Step 2: Prepare Backend Repository

### 1. Create `.gitignore` (Already exists)

Make sure these are **INCLUDED** (not ignored):
- ✅ `data/` folder (committed to git)
- ✅ `data/*.jsonl` files
- ✅ `data/*.json` files

Make sure these are **IGNORED**:
- ❌ `chroma_db/` (regenerated from data)
- ❌ `.env.backend` (secrets)
- ❌ `venv/` (dependencies)

### 2. Commit and Push to GitHub

```bash
cd backend

# Initialize git (if not already)
git init

# Add all files
git add .

# Commit
git commit -m "Initial backend with data files"

# Create GitHub repo and push
git remote add origin https://github.com/YOUR_USERNAME/zus-backend.git
git branch -M main
git push -u origin main
```

**Important:** Make sure `data/` folder is pushed to GitHub!

---

## 🚂 Step 3: Deploy to Railway

### 1. Create New Project

1. Go to [railway.app](https://railway.app/new)
2. Click **"New Project"**
3. Select **"Deploy from GitHub repo"**
4. Choose your `zus-backend` repository
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

### 4. Deploy

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

## 🔄 Step 5: Update Data (When Needed)

When scraping new data:

### 1. Update Data in Git

```bash
# In scraping repo - generate new data
cd scraping
python generate_data_files.py

# Copy to backend repo
cd ../backend
cp -r ../scraping/data/ ./data/

# Commit and push
git add data/
git commit -m "Update scraped data $(date +%Y-%m-%d)"
git push
```

### 2. Redeploy on Railway

Railway will auto-deploy when you push to GitHub.

The Dockerfile will:
- ✅ Copy new data files
- ✅ Rebuild Chroma DB with new data
- ✅ Reload Supabase with new outlets
- ✅ Restart server

**Note:** Chroma DB is rebuilt from `data/` files on every deployment.

---

## 📊 Railway Resource Usage

### Expected Usage:
- **Memory:** 1-2 GB
- **CPU:** 0.5-1 vCPU
- **Storage:** 2-3 GB (Ollama model + dependencies)
- **Build Time:** 5-10 minutes
- **Cost:** ~$10-20/month (Hobby plan)

### Volume Setup (Optional):

If you want persistent Chroma DB across deployments:

1. Create Railway volume
2. Mount at `/app/chroma_db`
3. Update `railway.json`:
   ```json
   {
     "deploy": {
       "volumes": [
         {
           "mountPath": "/app/chroma_db",
           "name": "chroma-db"
         }
       ]
     }
   }
   ```

**Note:** Not needed since we rebuild from data/ on each deploy.

---

## 🛠️ Troubleshooting

### Issue: Build fails - "Ollama not found"

**Solution:** Increase build timeout in Railway settings
```bash
Settings > Deploy > Build timeout: 20 minutes
```

### Issue: "Data files not found"

**Cause:** `data/` folder not committed to git

**Solution:**
```bash
# Check .gitignore doesn't ignore data/
git add data/ -f
git commit -m "Add data files"
git push
```

### Issue: "Chroma DB build failed"

**Cause:** Ollama service not ready

**Solution:** Increase sleep time in Dockerfile:
```dockerfile
RUN ollama serve & sleep 10 && ollama pull mxbai-embed-large && python setup_backend.py
```

### Issue: CORS errors in frontend

**Solution:** Update `CORS_ORIGINS` environment variable:
```bash
CORS_ORIGINS=http://localhost:3000,https://your-frontend.vercel.app
```

### Issue: "Supabase connection failed"

**Solution:** Check environment variables:
```bash
# Verify in Railway dashboard
echo $SUPABASE_URL
echo $SUPABASE_KEY
```

---

## 📝 Environment Variables Reference

| Variable | Required | Example | Description |
|----------|----------|---------|-------------|
| `GROQ_API_KEY` | ✅ Yes | `gsk_...` | Groq API key for LLM |
| `SUPABASE_URL` | ✅ Yes | `https://xxx.supabase.co` | Supabase project URL |
| `SUPABASE_KEY` | ✅ Yes | `eyJh...` | Supabase anon/service key |
| `CORS_ORIGINS` | ✅ Yes | `https://app.vercel.app` | Allowed frontend origins |
| `PORT` | ⚠️ Auto | `8000` | Railway auto-assigns |

---

## 🔐 Security Checklist

- ✅ Never commit `.env.backend` to git
- ✅ Use Railway environment variables for secrets
- ✅ Set proper CORS_ORIGINS (not `*`)
- ✅ Use Supabase Row Level Security (RLS)
- ✅ Rotate API keys periodically

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

## 📖 Additional Resources

- [Railway Docs](https://docs.railway.app)
- [Dockerfile Reference](https://docs.docker.com/engine/reference/builder/)
- [Ollama Docs](https://ollama.ai/docs)
- [FastAPI Deployment](https://fastapi.tiangolo.com/deployment/)

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
