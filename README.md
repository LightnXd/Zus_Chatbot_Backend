# ZUS Drinkware Chatbot - Backend

> AI-powered conversational agent for ZUS Coffee drinkware products and outlet information

[![FastAPI](https://img.shields.io/badge/FastAPI-0.104.1-009688?logo=fastapi)](https://fastapi.tiangolo.com/)
[![Python](https://img.shields.io/badge/Python-3.11-3776AB?logo=python)](https://www.python.org/)
[![LangChain](https://img.shields.io/badge/LangChain-0.3.13-121212)](https://www.langchain.com/)
[![Groq](https://img.shields.io/badge/Groq-Llama_3.3_70B-FF6B00)](https://groq.com/)

---

## 🚀 Quick Setup

### Option 1: Railway Deployment (Production)

**Prerequisites:**
- Railway account ([railway.app](https://railway.app))
- GitHub repository connected to Railway

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
   CORS_ORIGINS=https://your-frontend.vercel.app,http://localhost:5173
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
   CORS_ORIGINS=http://localhost:5173,http://localhost:5174
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

## 🏗️ Architecture Overview

### System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     FastAPI Backend                         │
│  ┌────────────────────────────────────────────────────────┐ │
│  │              Agentic Planning Layer                    │ │
│  │  (Decides: Products? Outlets? Calculate? Clarify?)     │ │
│  └────────────┬──────────────┬──────────────┬─────────────┘ │
│               │              │              │                │
│    ┌──────────▼─────┐  ┌────▼─────┐  ┌────▼──────┐        │
│    │ Product Search │  │  Outlet   │  │Calculator │        │
│    │   (ChromaDB)   │  │ (Supabase)│  │   Tool    │        │
│    └────────┬───────┘  └────┬──────┘  └────┬──────┘        │
│             │               │              │                │
│    ┌────────▼───────────────▼──────────────▼─────┐         │
│    │         Groq LLM (Llama 3.3 70B)            │         │
│    │  + Conversation Memory (3-turn context)     │         │
│    └─────────────────────────────────────────────┘         │
└─────────────────────────────────────────────────────────────┘
         │                    │                    │
         ▼                    ▼                    ▼
  HuggingFace           Supabase DB         In-Memory
  Embeddings           (PostgreSQL)          Sessions
(all-MiniLM-L6-v2)    253 Outlets           (per user)
  35 Products
```

### Component Breakdown

#### 1. **Entry Point** (`start.py`)
- FastAPI application initialization
- CORS middleware for frontend communication
- Service initialization (LLM, Vector DB, SQL DB)
- Route registration

#### 2. **Agentic Planner** (`agentic_planner.py`)
- **Purpose:** Intelligent decision-making layer
- **Actions:** `SEARCH_PRODUCTS`, `SEARCH_OUTLETS`, `CALCULATE`, `HYBRID_SEARCH`, `CLARIFY`
- **Features:**
  - Multi-criteria decision scoring
  - Confidence thresholds
  - Clarification question generation
  - Execution plan creation

#### 3. **Conversation Memory** (`conversation_memory.py`)
- **Session Management:** UUID-based sessions
- **Context Window:** Last 3 conversation turns
- **Metadata Tracking:** Search history, user preferences
- **Storage:** In-memory (cleared on restart)

#### 4. **Product Search Service** (`services/product_service.py`)
- **Vector Database:** ChromaDB (local storage)
- **Embeddings:** HuggingFace `sentence-transformers/all-MiniLM-L6-v2` (384-dim)
- **Features:**
  - Semantic similarity search
  - Smart sorting (price: cheapest/expensive, capacity: largest/smallest)
  - Intent detection (via keywords)
- **Data:** 35 drinkware products

#### 5. **Outlet Search Service** (`services/outlet_service.py`)
- **Database:** Supabase PostgreSQL
- **Technology:** LangChain Text-to-SQL
- **Features:**
  - Natural language → SQL conversion
  - Count query detection
  - Map URL inclusion for multiple results
  - Fallback error handling
- **Data:** 253 ZUS Coffee outlets (Kuala Lumpur, Selangor)

#### 6. **Calculator Tool** (`calculator_tool.py`)
- **Purpose:** Arithmetic operations from natural language
- **Supports:** Basic math (+, -, *, /, %, **)
- **Security:** Expression validation (numbers/operators only)
- **Examples:**
  - "what is 15% of 250?" → 37.5
  - "calculate 45 plus 30" → 75

#### 7. **Configuration** (`config/app_config.py`)
- **LLM:** Groq API (Llama 3.3 70B, 32K context, 8K output)
- **Embeddings:** HuggingFace local model
- **ChromaDB:** Local persistent storage
- **Supabase:** Cloud PostgreSQL connection
- **CORS:** Frontend origin management

---

## 🔑 Key Trade-offs

### 1. **Groq vs OpenAI**

| Aspect | Groq (Current) | OpenAI (Alternative) |
|--------|----------------|---------------------|
| **Cost** | ✅ Free tier (30 RPM) | ❌ Pay-per-token |
| **Speed** | ✅ Ultra-fast (LPU architecture) | 🟡 Moderate |
| **Model** | Llama 3.3 70B | GPT-4 Turbo |
| **Quality** | 🟡 Good (open-source) | ✅ Best-in-class |
| **Rate Limits** | ⚠️ 30 requests/min | ✅ Higher limits |

**Decision:** Groq chosen for cost-effectiveness and speed in MVP phase.

---

### 2. **ChromaDB (Local) vs Pinecone/Weaviate (Cloud)**

| Aspect | ChromaDB (Current) | Pinecone/Weaviate |
|--------|-------------------|-------------------|
| **Cost** | ✅ Free (local storage) | ❌ Subscription required |
| **Latency** | ✅ ~100ms (local I/O) | 🟡 ~200-300ms (network) |
| **Scalability** | ⚠️ Limited to single instance | ✅ Auto-scaling |
| **Persistence** | ✅ Local disk | ✅ Cloud backup |
| **Setup** | ✅ Zero config | 🟡 API key required |

**Decision:** ChromaDB for 35 products is sufficient; local storage eliminates external dependencies.

**Migration Path:** If product catalog grows >1000 items, consider Pinecone/Weaviate.

---

### 3. **Supabase vs Self-Hosted PostgreSQL**

| Aspect | Supabase (Current) | Self-Hosted |
|--------|-------------------|-------------|
| **Setup** | ✅ Instant (cloud) | 🟡 Manual setup |
| **Cost** | ✅ Free tier (500MB) | ✅ Free (hosting cost) |
| **Scaling** | ✅ Auto-scaling | ❌ Manual scaling |
| **Backups** | ✅ Automatic | ❌ Manual backups |
| **Control** | 🟡 Limited | ✅ Full control |

**Decision:** Supabase provides managed PostgreSQL with zero maintenance.

---

### 4. **In-Memory Sessions vs Redis/Database**

| Aspect | In-Memory (Current) | Redis/Database |
|--------|---------------------|----------------|
| **Speed** | ✅ Instant access | 🟡 Network latency |
| **Cost** | ✅ Free | ❌ Hosting cost |
| **Persistence** | ❌ Lost on restart | ✅ Survives restarts |
| **Scalability** | ❌ Single instance | ✅ Distributed |
| **Setup** | ✅ Zero config | 🟡 External service |

**Decision:** In-memory for MVP; acceptable to lose sessions on restart.

**Migration Path:** If multi-instance deployment needed, use Redis for shared session state.

---

### 5. **HuggingFace Embeddings vs OpenAI Embeddings**

| Aspect | HuggingFace (Current) | OpenAI |
|--------|-----------------------|--------|
| **Cost** | ✅ Free (local model) | ❌ $0.0001/1K tokens |
| **Speed** | 🟡 ~200ms (CPU) | ✅ ~50ms (API) |
| **Quality** | 🟡 Good (384-dim) | ✅ Excellent (1536-dim) |
| **Offline** | ✅ Works offline | ❌ Requires internet |
| **Setup** | 🟡 Model download (90MB) | ✅ API key only |

**Decision:** HuggingFace `all-MiniLM-L6-v2` provides good quality at zero cost.

**Trade-off:** Slightly lower quality vs OpenAI, but acceptable for 35 product catalog.

---

### 6. **Docker Multi-Stage Build**

**Optimization:** Image size reduced from **8GB → 1.5GB**

| Stage | Purpose | Size Impact |
|-------|---------|-------------|
| **Builder** | Install dependencies | Temporary |
| **Runtime** | Copy only needed files | Final (1.5GB) |

**Benefits:**
- ✅ Faster deployment on Railway
- ✅ Reduced bandwidth costs
- ✅ Quicker cold starts

**Trade-off:** Slightly longer build time (~3-5 min vs 2 min).

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

## 🔧 Environment Variables

| Variable | Required | Description | Example |
|----------|----------|-------------|---------|
| `GROQ_API_KEY` | ✅ Yes | Groq API key | `gsk_...` |
| `SUPABASE_URL` | ✅ Yes | Supabase project URL | `https://xxx.supabase.co` |
| `SUPABASE_KEY` | ✅ Yes | Supabase anon key | `eyJhb...` |
| `PORT` | 🟡 Railway only | Server port | `8000` (Railway auto) |
| `API_HOST` | ❌ Optional | Bind host | `0.0.0.0` |
| `API_PORT` | ❌ Optional | Local port | `8000` |
| `CORS_ORIGINS` | ❌ Optional | Allowed origins | `http://localhost:5173` |

---

## 🧪 Testing

### Health Check
```bash
curl http://localhost:8000/health
```

### Chat Endpoint
```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"question": "What tumblers do you have?"}'
```

### Product Search
```bash
curl -X POST http://localhost:8000/api/products/search \
  -H "Content-Type: application/json" \
  -d '{"query": "insulated bottle", "limit": 5}'
```

### Statistics
```bash
curl http://localhost:8000/api/stats
```

---

## 📊 Performance Metrics

| Metric | Value | Notes |
|--------|-------|-------|
| **Average Response Time** | ~1.5s | Including LLM inference |
| **Vector Search** | ~100ms | ChromaDB local lookup |
| **Text-to-SQL** | ~200ms | Supabase query execution |
| **LLM Inference** | ~800ms | Groq LPU acceleration |
| **Cold Start (Railway)** | ~15s | Docker image pull + init |
| **Memory Usage** | ~800MB | Including embeddings model |
| **Docker Image Size** | 1.5GB | Multi-stage optimized |

---

## 🚨 Common Issues & Solutions

### Issue 1: ChromaDB Collection Empty

**Symptom:**
```
⚠️ ChromaDB collection is empty!
```

**Solution:**
```bash
python setup_backend.py
```

### Issue 2: Groq API Rate Limit

**Symptom:**
```
Error: Rate limit exceeded (30 requests/min)
```

**Solution:**
- Wait 1 minute before retrying
- Upgrade to Groq paid tier
- Implement request queuing

### Issue 3: Supabase Connection Error

**Symptom:**
```
❌ Setup failed: Could not connect to Supabase
```

**Solution:**
1. Check `SUPABASE_URL` and `SUPABASE_KEY` in `.env.backend`
2. Verify Supabase project is active
3. Check network connectivity

### Issue 4: CORS Errors

**Symptom:**
```
Access-Control-Allow-Origin header missing
```

**Solution:**
Add frontend URL to `CORS_ORIGINS`:
```env
CORS_ORIGINS=http://localhost:5173,https://your-frontend.vercel.app
```

---

## 📚 API Documentation

See [API_DOCUMENTATION.md](../API_DOCUMENTATION.md) for complete endpoint reference.

---

## 🔄 Deployment Workflow

### Railway Continuous Deployment

```
Code Push → GitHub → Railway Auto-Deploy
    ↓
  Build Dockerfile (multi-stage)
    ↓
  Run start.py
    ↓
  Health check passes
    ↓
  Service live at https://your-app.up.railway.app
```

**Automatic:**
- ✅ HTTPS certificate
- ✅ Custom domain support
- ✅ Auto-restart on crashes (max 10 retries)
- ✅ Environment variable management

---

## 🛠️ Tech Stack Summary

| Layer | Technology | Version |
|-------|-----------|---------|
| **Framework** | FastAPI | 0.104.1 |
| **Runtime** | Python | 3.11 |
| **LLM** | Groq (Llama 3.3 70B) | - |
| **Vector DB** | ChromaDB | 0.5.0 |
| **SQL DB** | Supabase PostgreSQL | - |
| **Embeddings** | HuggingFace Transformers | sentence-transformers/all-MiniLM-L6-v2 |
| **Orchestration** | LangChain | 0.3.13 |
| **Server** | Uvicorn | 0.24.0 |
| **Deployment** | Railway (Docker) | - |

---

## 📝 License

MIT License - See LICENSE file for details

---

## 👨‍💻 Author

**LightnXd**  
GitHub: [@LightnXd](https://github.com/LightnXd)

---

## 🤝 Contributing

Pull requests welcome! For major changes, please open an issue first.

---

**Last Updated:** November 10, 2025
