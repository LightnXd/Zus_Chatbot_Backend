# Optimized Dockerfile - Reduced from 2.3GB to 1.1GB
FROM python:3.11-slim

# Disable ChromaDB telemetry
ENV CHROMA_TELEMETRY_ENABLED=0

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
COPY requirements-backend.txt .
RUN pip install --no-cache-dir -r requirements-backend.txt && \
    pip install --no-cache-dir \
        langchain \
        langchain-groq \
        langchain-chroma \
        langchain-ollama \
        chromadb \
        supabase

# Copy application code and data
COPY start.py .
COPY setup_backend.py .
COPY config/ ./config/
COPY services/ ./services/
COPY routes/ ./routes/
COPY database/ ./database/
COPY data/ ./data/
COPY conversation_memory.py .
COPY agentic_planner.py .
COPY calculator_tool.py .

EXPOSE 8000

# Runtime setup: Pull smaller model and initialize
# Skip setup_backend.py for now - will run manually after deployment
CMD set -e; \
    echo "Starting Ollama service..."; \
    ollama serve > /tmp/ollama.log 2>&1 & \
    OLLAMA_PID=$!; \
    sleep 10; \
    echo "Pulling embedding model (nomic-embed-text - 274MB)..."; \
    ollama pull nomic-embed-text 2>&1 || (echo "❌ Model pull failed!" && cat /tmp/ollama.log && exit 1); \
    echo "⚠️  Skipping backend setup (will run manually)"; \
    echo "Starting API server..."; \
    exec python -u start.py
