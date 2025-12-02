# ZUS Drinkware Chatbot - Backend

## 🚀 Quick Setup

**Optional:**
- Scrape and import newest ZUS product and outlet information using https://github.com/LightnXd/Zus_Scraper

### Option 1: Render Deployment (Production)

**Prerequisites:**
- Render account ([render.com](https://render.com))
- GitHub repository with your code

**Steps:**

1. **Push code to GitHub:**
   ```bash
   git push origin main
   ```

2. **Create a new Web Service on Render:**
   - Go to [render.com](https://render.com)
   - Click "New Web Service"
   - Connect your GitHub repository

3. **Configure environment variables:**
   - Add the following environment variables in the Render dashboard:
     - `GROQ_API_KEY=your_groq_api_key_here`
     - `SUPABASE_URL=your_supabase_url`
     - `SUPABASE_KEY=your_supabase_anon_key`
     - `PORT=8000`
     - `CORS_ORIGINS=add all domain that able to access backend separated by (,) (example: https://your-frontend.vercel.app,http://localhost:3000)`

4. **Set build and start commands:**
   - **Build Command:**
     ```bash
     pip install -r requirements-backend.txt
     ```
   - **Start Command:**
     ```bash
     python start.py
     ```

5. **Deploy:**
   - Render will automatically build and deploy your service
   - Get your deployment URL from the Render dashboard

**Note:**
- Make sure you have a `Procfile` with the following content (already included):
  ```
  web: python start.py
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
   - Load 38+ malicious question patterns for guardrail protection
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
├── Procfile                    # Render deployment config
├── .env.backend                # Environment variables (local)
├── .dockerignore               # Docker ignore rules
├── .gitignore                  # Git ignore rules
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
│   ├── guardrail_service.py   # Malicious content detection
│   └── search_routing.py      # Legacy routing logic
│
├── database/
│   ├── text_to_sql.py         # SQL generation from NL
│   ├── outlet_queries.py      # Supabase query wrapper
│   ├── supabase_schema.py     # Database schema definition
│   ├── docker-compose.yml     # Docker setup for local PostgreSQL
│   └── SETUP.md               # Database setup instructions
│
├── agentic_planner.py         # Decision-making engine
├── conversation_memory.py     # Session management
├── calculator_tool.py         # Arithmetic operations
│
├── data/
│   ├── products_drinkware.jsonl           # 35 drinkware products (JSONL)
│   ├── outlets_kuala_lumpur_selangor.jsonl  # 253 outlets (JSONL)
│   ├── outlets_metadata.json              # Outlet metadata
│   └── malicious_questions.jsonl          # 38+ malicious patterns for guardrail
│
├── chroma_db/                 # Local vector database (generated)
│   └── [Generated files]
│
├── commands/                  # Custom commands (empty/unused)
│
└── venv/                      # Python virtual environment
```

---