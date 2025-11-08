# Optimized Dockerfile - Reduced from 2.3GB to 1.1GB
FROM python:3.11-slim

# Install minimal system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Install Ollama with retry logic
RUN set -e; \
    for i in 1 2 3; do \
        curl -fsSL https://ollama.com/install.sh | sh && break || \
        (echo "Attempt $i failed, retrying..." && sleep 5); \
    done && \
    which ollama && ollama --version

WORKDIR /app

# Copy and install Python dependencies
COPY requirements-minimal.txt .
RUN pip install --no-cache-dir -r requirements-minimal.txt && \
    pip install --no-cache-dir \
        langchain \
        langchain-groq \
        langchain-chroma \
        langchain-ollama \
        chromadb \
        supabase

# Copy application code and data
COPY api_server_chroma.py .
COPY setup_backend.py .
COPY database/ ./database/
COPY data/ ./data/

EXPOSE 8000

# Runtime setup: Pull smaller model and initialize
# This keeps the image size smaller (model not included in image)
CMD set -e; \
    echo "Starting Ollama service..."; \
    ollama serve > /tmp/ollama.log 2>&1 & \
    OLLAMA_PID=$!; \
    sleep 10; \
    echo "Pulling embedding model (nomic-embed-text - 274MB)..."; \
    ollama pull nomic-embed-text 2>&1 || (echo "❌ Model pull failed!" && cat /tmp/ollama.log && exit 1); \
    echo "Running backend setup..."; \
    python -u setup_backend.py 2>&1 || (echo "❌ Setup failed! Check logs above" && exit 1); \
    echo "Starting API server..."; \
    exec python -u api_server_chroma.py
