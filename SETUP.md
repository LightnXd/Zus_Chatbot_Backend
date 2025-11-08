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

---

## ⚙️ Step 2: Configure Environment Variables

### 1. Create `.env.backend` File

create a file named `.env.backend`:

```bash
# Groq API 
GROQ_API_KEY=gsk_your_groq_api_key_here

# Supabase 
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your_supabase_anon_key_here

# CORS
CORS_ORIGINS=http://localhost:3000,http://localhost:5173

# Optional
PORT=8000
```

---

## 🔑 Step 3: Set Up Supabase Database

### 1. Create Supabase Project

1. Go to [supabase.com](https://supabase.com)
2. Click **"New Project"**
3. Wait for project to be provisioned (~2 minutes)

### 3. Create Outlets Table

1. In Supabase dashboard, go to **SQL Editor**
2. Click **"New Query"**
3. Paste this SQL schema:

```sql
-- Create outlets table
CREATE TABLE IF NOT EXISTS public.outlets (
    id BIGSERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    address TEXT,
    city TEXT,
    state TEXT,
    postal_code TEXT,
    phone TEXT,
    maps_url TEXT,
    location_category TEXT,
    hours TEXT,
    fetched_at TIMESTAMP WITH TIME ZONE,
    source TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create index for faster queries
CREATE INDEX IF NOT EXISTS idx_outlets_city ON public.outlets(city);
CREATE INDEX IF NOT EXISTS idx_outlets_state ON public.outlets(state);
CREATE INDEX IF NOT EXISTS idx_outlets_name ON public.outlets(name);

-- Enable Row Level Security (RLS)
ALTER TABLE public.outlets ENABLE ROW LEVEL SECURITY;

-- Create policy to allow public read access
CREATE POLICY "Allow public read access"
    ON public.outlets
    FOR SELECT
    USING (true);
```

4. Click **"Run"** or press `Ctrl+Enter`
5. Verify success: ✅ "Success. No rows returned"

### 4. Get Supabase Credentials

1. In Supabase dashboard, go to **Settings** > **API**
2. Copy these values to the .env.backend
   - **Project URL:** `https://xxxxx.supabase.co`
   - **Anon/Public Key:** `eyJhbG...` (long string)

---

## Step 4: Set Up Groq API

### 1. Get Groq API Key

1. Go to [console.groq.com](https://console.groq.com)
2. Go to **API Keys** section
3. Click **"Create API Key"**
4. Copy the API key to .env.backend

**Note:** Groq offers free tier with rate limits (perfect for testing)

---

## 🛠️ Step 5: Install Ollama and Dependencies

### 1. Install Ollama (for embeddings)

**Windows:**
1. Download from [ollama.com/download](https://ollama.com/download)
2. Run the installer
3. Verify installation:
   ```powershell
   ollama --version
   ```

**macOS/Linux:**
```bash
curl -fsSL https://ollama.com/install.sh | sh
```

### 2. Pull Embedding Model

```powershell
ollama pull mxbai-embed-large
```

This downloads the embedding model (~700MB). It will be used to create vector embeddings for product search.

### 3. Start Ollama Service

```powershell
ollama serve
```

Keep this terminal open! Ollama needs to be running when you set up the backend.

---

## 🐍 Step 6: Set Up Python Environment

### 1. Create Virtual Environment

```powershell
# Create virtual environment
python -m venv venv

# Activate it
.\venv\Scripts\Activate.ps1
```

**Note:** If you get execution policy error, run:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### 2. Install Dependencies

```powershell
pip install -r requirements-backend.txt
```
---

## 🚀 Step 7: Initialize Backend

### 1. Run Setup Script

With Ollama running in another terminal:

```powershell
python setup_backend.py
```

This will:
1. ✅ Verify data files exist
2. ✅ Connect to Ollama
3. ✅ Build Chroma vector database from products (35 products)
4. ✅ Connect to Supabase
5. ✅ Load outlets to Supabase (253 outlets)

**Expected Output:**
```
============================================================
  ZUS DRINKWARE BACKEND SETUP
============================================================

✅ Found data files:
   - data\products_drinkware.jsonl
   - data\outlets_kuala_lumpur_selangor.jsonl

Step 1: Building Chroma Vector Database...
------------------------------------------------------------
Connecting to Ollama (mxbai-embed-large)...
Creating Chroma collection: drinkware_collection
Loading products from data\products_drinkware.jsonl...
Adding 35 products to Chroma...
✅ Chroma DB created with 35 products

Step 2: Loading Outlets to Supabase...
------------------------------------------------------------
Connecting to Supabase...
Loading outlets from data\outlets_kuala_lumpur_selangor.jsonl...
Found 253 outlets
   Inserted 100/253 outlets
   Inserted 200/253 outlets
   Inserted 253/253 outlets
✅ Loaded 253 outlets to Supabase

============================================================
  SETUP COMPLETE
============================================================

Next steps:
1. Start Ollama: ollama serve
2. Start backend: python api_server_chroma.py
3. Test: curl http://localhost:8000/health
```

### 2. Troubleshooting Setup

**Error: "Ollama connection failed"**
- Make sure Ollama is running: `ollama serve`
- Check if model is pulled: `ollama list`

**Error: "Supabase connection failed"**
- Verify SUPABASE_URL and SUPABASE_KEY in `.env.backend`
- Check Supabase project is active

**Error: "Data files not found"**
- Verify data files are in `data/` folder
- Check file names match exactly

---

## 🏃 Step 8: Start the Backend Server

### 1. Make Sure Ollama is Running

In one terminal:
```powershell
ollama serve
```

### 2. Start FastAPI Server

In another terminal (with venv activated):
```powershell
python api_server_chroma.py
```

**Expected Output:**
```
INFO:     Started server process [12345]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
```

---

## ✅ Step 9: Test the Backend

### 1. Health Check

Open browser or use curl:
```powershell
curl http://localhost:8000/health
```

**Expected Response:**
```json
{
  "status": "healthy",
  "timestamp": "2025-11-08T12:00:00Z"
}
```

### 2. Test Chat Endpoint

```powershell
curl -X POST http://localhost:8000/api/chat `
  -H "Content-Type: application/json" `
  -d '{\"message\": \"Show me tumblers\"}'
```

**Expected Response:**
```json
{
  "response": "We have several tumblers available including...",
  "timestamp": "2025-11-08T12:00:00Z"
}
```

### 3. Check Database Stats

```powershell
curl http://localhost:8000/api/stats
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

### 4. List Outlets

```powershell
curl http://localhost:8000/api/outlets
```

Should return array of 253 outlets.

---

## 🎉 Success!

Your local backend is now running! You can:
- ✅ Chat with the AI about ZUS products
- ✅ Query product information
- ✅ Find nearby outlets
- ✅ Get product recommendations

---

## 🔄 Daily Development Workflow

```powershell
# 1. Activate virtual environment
.\venv\Scripts\Activate.ps1

# 2. Start Ollama (in separate terminal)
ollama serve

# 3. Start backend server
python api_server_chroma.py

# 4. Test endpoints
curl http://localhost:8000/health
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
