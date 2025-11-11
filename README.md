# ZUS Drinkware Chatbot - Backend

## 🚀 Quick Setup

**Optional:**
- Scrape and import newest ZUS product and outlet information using https://github.com/LightnXd/Zus_Scraper

### Option 1: Railway Deployment (Production)

**Prerequisites:**
- Railway account ([railway.app](https://railway.app))
- GitHub repository connected to Railway

**Optional:**
- Scrape and import newest ZUS product and outlet information using https://github.com/LightnXd/Zus_Scraper

**Steps:**

1. **Push code to GitHub:**
   ```bash
   git push origin main
   ```

2. **Create Railway project:**
   - Go to [railway.app](https://railway.app)
   - Click "New Project" → "Deploy from GitHub repo"
   - Select your repository

3. **Configure environment variables:**
   ```env
   GROQ_API_KEY=your_groq_api_key_here
   SUPABASE_URL=your_supabase_url
   SUPABASE_KEY=your_supabase_anon_key
   PORT=8000
   CORS_ORIGINS=add all domain that able to access backend seperated by (,) (example: https://your-frontend.vercel.app,http://localhost:3000)
   ```

4. **Railway auto-detects:**
   - `Dockerfile` for containerized deployment
   - `railway.json` for build configuration
   - Automatic HTTPS and domain provisioning

5. **Deploy:**
   - Railway automatically builds and deploys
   - Get your deployment URL: `https://your-app.up.railway.app`

**Railway Configuration (`railway.json`):**
```json
{
  "build": {
    "builder": "DOCKERFILE",
    "dockerfilePath": "Dockerfile"
  },
  "deploy": {
    "restartPolicyType": "ON_FAILURE",
    "restartPolicyMaxRetries": 10
  }
}
```

---

### Option 2: Local Development

**Prerequisites:**
- Python 3.11+
- pip or virtualenv

**Setup Steps:**

1. **Clone repository:**
   ```bash
   git clone https://github.com/LightnXd/Zus_Chatbot_Backend.git
   cd Zus_Chatbot_Backend
   ```

2. **Create virtual environment:**
   ```bash
   python -m venv venv
   
   # Windows
   venv\Scripts\activate
   
   # macOS/Linux
   source venv/bin/activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements-backend.txt
   ```

4. **Configure environment variables:**
   
   Create `.env.backend` file:
   ```env
   GROQ_API_KEY=your_groq_api_key_here
   SUPABASE_URL=your_supabase_url
   SUPABASE_KEY=your_supabase_anon_key
   API_HOST=0.0.0.0
   API_PORT=8000
   CORS_ORIGINS=add all domain that able to access backend seperated by (,) (example: https://your-frontend.vercel.app,http://localhost:3000)
   ```

5. **Setup ChromaDB (first-time only):**
   ```bash
   python setup_backend.py
   ```
   
   This will:
   - Load 35 drinkware products into ChromaDB
   - Create local vector embeddings
   - Initialize `chroma_db/` directory

6. **Start development server:**
   ```bash
   python start.py
   ```

7. **Verify backend is running:**
   ```bash
   # Health check
   curl http://localhost:8000/health
   
   # Or visit in browser
   http://localhost:8000/health
   ```

**Expected Output:**
```json
{
  "status": "online",
  "groq_available": true,
  "chroma_available": true,
  "supabase_available": true
}
```

---

## 📦 Project Structure

```
Zus_Chatbot_Backend/
├── start.py                    # FastAPI entry point
├── setup_backend.py            # ChromaDB initialization
├── requirements-backend.txt    # Python dependencies
├── Dockerfile                  # Multi-stage Docker build
├── railway.json                # Railway deployment config
│
├── config/
│   └── app_config.py          # LLM, embeddings, DB initialization
│
├── routes/
│   ├── chat_routes.py         # Main chat endpoint
│   ├── product_routes.py      # Product search endpoint
│   ├── outlet_routes.py       # Outlet search endpoint
│   ├── calculator_routes.py   # Calculator endpoint
│   └── utility_routes.py      # Health, stats endpoints
│
├── services/
│   ├── product_service.py     # Product retrieval + sorting
│   ├── outlet_service.py      # Text-to-SQL outlet search
│   └── search_routing.py      # Legacy routing logic
│
├── database/
│   ├── text_to_sql.py         # SQL generation from NL
│   ├── outlet_queries.py      # Supabase query wrapper
│   └── supabase_schema.py     # Database schema definition
│
├── agentic_planner.py         # Decision-making engine
├── conversation_memory.py     # Session management
├── calculator_tool.py         # Arithmetic operations
│
├── data/
│   └── products.json          # 35 drinkware products
│
└── chroma_db/                 # Local vector database (generated)
```

---