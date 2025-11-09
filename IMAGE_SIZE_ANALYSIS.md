# 📊 Docker Image Size Analysis & Optimization

## Current Image Size Breakdown

### Estimated Sizes:

| Component | Size | Notes |
|-----------|------|-------|
| **Base Image** (`python:3.11-slim`) | ~120 MB | Minimal Python install |
| **System packages** (curl, ca-certificates) | ~15 MB | Build dependencies |
| **Ollama binary** | ~600-800 MB | Main embedding service |
| **Ollama model** (`mxbai-embed-large`) | ~700 MB | Embedding model weights |
| **Python packages** | ~400-600 MB | LangChain, Chroma, FastAPI, etc. |
| **Chroma DB** (generated) | ~5-10 MB | Vector database with 35 products |
| **Application code + data** | ~1 MB | Your Python files + JSON data |

### **Total Estimated Size: ~1.8-2.3 GB**

---

## 🎯 Optimization Strategies

### Option 1: Remove Build-Time Setup (Save ~700 MB in image)

**Current:** Model is downloaded during build  
**Optimized:** Download model at runtime

**New Dockerfile:**
```dockerfile
FROM python:3.11-slim

# Install dependencies
RUN apt-get update && apt-get install -y \
    curl ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Install Ollama
RUN for i in 1 2 3; do \
        curl -fsSL https://ollama.com/install.sh | sh && break || sleep 5; \
    done && ollama --version

WORKDIR /app

# Install Python packages
COPY requirements-backend.txt .
RUN pip install --no-cache-dir -r requirements-backend.txt && \
    pip install --no-cache-dir langchain langchain-groq langchain-chroma langchain-ollama chromadb supabase

# Copy app files
COPY . .

EXPOSE 8000

# Runtime setup (model downloads on first start)
CMD ollama serve & \
    sleep 8 && \
    ollama pull mxbai-embed-large && \
    python setup_backend.py && \
    python api_server_chroma.py
```

**Savings:** ~700 MB (model not in image)  
**Trade-off:** First startup takes 3-5 min (downloads model)  
**Image size:** ~1.1-1.6 GB

---

### Option 2: Use Smaller Embedding Model (Save ~400 MB)

Replace `mxbai-embed-large` (700MB) with smaller alternatives:

| Model | Size | Quality | Speed |
|-------|------|---------|-------|
| `mxbai-embed-large` | 700 MB | Excellent | Slower |
| **`nomic-embed-text`** | 274 MB | Very Good | Fast |
| `all-minilm` | 45 MB | Good | Very Fast |

**Changes needed:**

1. In `setup_backend.py`:
```python
embeddings = OllamaEmbeddings(model="nomic-embed-text")  # Changed
```

2. In Dockerfile:
```dockerfile
RUN ollama pull nomic-embed-text  # Changed
```

**Savings:** ~400 MB  
**Trade-off:** Slightly lower embedding quality  
**Recommended:** `nomic-embed-text` (best balance)

---

### Option 3: Multi-Stage Build (Save ~500 MB)

Use multi-stage Docker build to exclude build tools:

```dockerfile
# Stage 1: Builder
FROM python:3.11-slim as builder

RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Ollama
RUN curl -fsSL https://ollama.com/install.sh | sh

# Install Python deps
COPY requirements-backend.txt .
RUN pip install --no-cache-dir --target=/app/deps -r requirements-backend.txt && \
    pip install --no-cache-dir --target=/app/deps \
    langchain langchain-groq langchain-chroma langchain-ollama chromadb supabase

# Stage 2: Runtime
FROM python:3.11-slim

RUN apt-get update && apt-get install -y ca-certificates && rm -rf /var/lib/apt/lists/*

# Copy Ollama from builder
COPY --from=builder /usr/local/bin/ollama /usr/local/bin/ollama
COPY --from=builder /usr/share/ollama /usr/share/ollama

# Copy Python packages from builder
COPY --from=builder /app/deps /usr/local/lib/python3.11/site-packages

WORKDIR /app
COPY . .

EXPOSE 8000

CMD ollama serve & \
    sleep 8 && \
    ollama pull nomic-embed-text && \
    python setup_backend.py && \
    python api_server_chroma.py
```

**Savings:** ~500 MB (removes build artifacts)  
**Complexity:** Higher  
**Image size:** ~1.0-1.5 GB

---

### Option 4: Alpine Linux Base (Save ~100 MB)

Switch from Debian-based `python:slim` to Alpine:

```dockerfile
FROM python:3.11-alpine

RUN apk add --no-cache curl bash

# Rest of Dockerfile...
```

**Savings:** ~100 MB  
**Trade-off:** 
- More complex to install Ollama (not officially supported on Alpine)
- Some Python packages may need compilation
- **NOT RECOMMENDED** for Ollama

---

### Option 5: External Model Storage (Save ~700 MB)

Store model in Railway volume, not in image:

**railway.toml:**
```toml
[[volumes]]
name = "ollama-models"
mountPath = "/root/.ollama"
```

**Dockerfile:**
```dockerfile
# Don't pull model during build
# Model will be in persistent volume
```

**Startup script:**
```bash
ollama serve &
if [ ! -f "/root/.ollama/models/manifests/registry.ollama.ai/library/nomic-embed-text" ]; then
    ollama pull nomic-embed-text
fi
python setup_backend.py
python api_server_chroma.py
```

**Savings:** ~700 MB (model in volume)  
**Benefits:** 
- Faster builds
- Model persists across deployments
- Can update model without rebuilding

---

## 🏆 Recommended Optimizations

### Immediate (Easy Wins):

1. **Switch to `nomic-embed-text` model** → Save 400 MB
2. **Move model pull to runtime** → Save 700 MB from image
3. **Use Railway volume for models** → Faster deploys

### Combined Approach (Best):

```dockerfile
FROM python:3.11-slim

# Install minimal dependencies
RUN apt-get update && apt-get install -y \
    curl ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Install Ollama
RUN for i in 1 2 3; do \
        curl -fsSL https://ollama.com/install.sh | sh && break || sleep 5; \
    done

WORKDIR /app

# Install Python packages (smaller set)
COPY requirements-backend.txt .
RUN pip install --no-cache-dir -r requirements-backend.txt && \
    pip install --no-cache-dir \
    langchain langchain-groq langchain-chroma langchain-ollama chromadb supabase

# Copy app
COPY . .

EXPOSE 8000

# Runtime setup with smaller model
CMD ollama serve & \
    sleep 8 && \
    ollama pull nomic-embed-text && \
    python setup_backend.py && \
    python api_server_chroma.py
```

**Final Image Size:** ~1.1 GB (down from 2.3 GB)  
**Savings:** ~1.2 GB (52% reduction)

---

## Size Comparison

| Approach | Image Size | Build Time | First Start | Complexity |
|----------|------------|------------|-------------|------------|
| **Current** | 2.3 GB | 10-15 min | 2 min | Low |
| **Runtime setup** | 1.6 GB | 5-8 min | 5 min | Low |
| **Smaller model** | 1.9 GB | 8-12 min | 2 min | Low |
| **Both (Recommended)** | **1.1 GB** | **5-8 min** | **5 min** | Low |
| **Multi-stage** | 1.0 GB | 12-18 min | 5 min | High |
| **With volume** | 0.4 GB | 3-5 min | 6 min (first) | Medium |

---

## 💡 Additional Tips

### 1. Clean up pip cache:
```dockerfile
RUN pip install --no-cache-dir ...  # Already doing this ✅
```

### 2. Combine RUN commands:
```dockerfile
RUN apt-get update && apt-get install -y curl \
    && rm -rf /var/lib/apt/lists/*  # Already doing this ✅
```

### 3. Remove unnecessary packages:
```dockerfile
# Don't install beautifulsoup4 if not used in backend
```

### 4. Use .dockerignore:
```
__pycache__
*.pyc
.git
.env*
venv/
.vscode/
*.md
tests/
```

---

## 🎯 Action Items

### Quick Win (5 minutes):
1. Create `.dockerignore` file
2. Switch to `nomic-embed-text` model
3. Move model pull to runtime

### Medium (30 minutes):
1. Implement multi-stage build
2. Set up Railway volume for models
3. Test deployment

### Impact:
- **Image size:** 2.3 GB → 1.1 GB (52% reduction)
- **Build time:** 10-15 min → 5-8 min (faster)
- **Deploy time:** Faster (smaller image to push)
- **Cost:** Potentially lower (less storage)

---

## ⚠️ Trade-offs to Consider

| Optimization | Pro | Con |
|--------------|-----|-----|
| Runtime setup | Smaller image | Slower first start (one-time) |
| Smaller model | Much smaller | Slightly lower quality |
| Multi-stage | Smallest image | More complex Dockerfile |
| Volume storage | Very small image | Requires Railway volume setup |

---

## 🚀 Next Steps

1. Review recommended approach
2. Test with smaller model locally first
3. Update Dockerfile
4. Push and redeploy to Railway
5. Monitor performance and quality

**Recommendation:** Start with runtime setup + smaller model (1.1 GB, easy to implement)
