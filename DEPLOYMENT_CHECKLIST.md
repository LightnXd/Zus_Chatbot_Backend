# ✅ Railway Deployment Checklist

## Before Pushing to GitHub

- [ ] Data files copied from scraping repo
  - [ ] `data/products_drinkware.jsonl` (35 products)
  - [ ] `data/outlets_kuala_lumpur_selangor.jsonl` (253 outlets)
  - [ ] `data/outlets_metadata.json`

- [ ] Required files present
  - [ ] `Dockerfile`
  - [ ] `railway.json`
  - [ ] `requirements-backend.txt`
  - [ ] `requirements-backend.txt`
  - [ ] `api_server_chroma.py`
  - [ ] `setup_backend.py`
  - [ ] `database/` folder

- [ ] Git configuration
  - [ ] `.gitignore` set up correctly
  - [ ] `data/` folder NOT ignored (should be committed)
  - [ ] `chroma_db/` IS ignored
  - [ ] `.env.backend` IS ignored

- [ ] Push to GitHub
  ```bash
  git add .
  git commit -m "Ready for Railway deployment"
  git push origin main
  ```

---

## Railway Setup

- [ ] Create new Railway project
- [ ] Connect GitHub repository
- [ ] Select `zus-backend` repo
- [ ] Railway auto-detects Dockerfile ✅

---

## Environment Variables (Railway Dashboard)

Copy these to Railway environment variables:

```bash
GROQ_API_KEY=your_groq_api_key_here
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your_supabase_anon_key
CORS_ORIGINS=http://localhost:3000
```

**Note:** Update `CORS_ORIGINS` after frontend is deployed!

---

## After Deployment

- [ ] Wait for build to complete (~5-10 minutes)
- [ ] Copy Railway URL: `https://________.up.railway.app`
- [ ] Test health endpoint:
  ```bash
  curl https://your-app.up.railway.app/health
  ```
- [ ] Test chat endpoint:
  ```bash
  curl -X POST https://your-app.up.railway.app/api/chat \
    -H "Content-Type: application/json" \
    -d '{"message": "Show me tumblers"}'
  ```
- [ ] Test stats endpoint:
  ```bash
  curl https://your-app.up.railway.app/api/stats
  ```

---

## Update Frontend

After backend is deployed:

1. [ ] Copy Railway URL
2. [ ] Update frontend `.env.production`:
   ```bash
   VITE_API_URL=https://your-app.up.railway.app
   ```
3. [ ] Deploy frontend to Vercel
4. [ ] Copy Vercel URL
5. [ ] Update Railway `CORS_ORIGINS`:
   ```bash
   CORS_ORIGINS=http://localhost:3000,https://your-app.vercel.app
   ```

---

## Verification

Expected responses:

### `/health`
```json
{
  "status": "healthy",
  "timestamp": "2025-11-08T..."
}
```

### `/api/stats`
```json
{
  "total_products": 35,
  "total_outlets": 253,
  "vector_db": "chroma",
  "embedding_model": "mxbai-embed-large"
}
```

### `/api/chat`
```json
{
  "response": "We have several tumblers available...",
  "timestamp": "2025-11-08T..."
}
```

---

## 🎉 Done!

If all checks pass, your backend is successfully deployed to Railway!

See `RAILWAY_SETUP.md` for detailed troubleshooting.
