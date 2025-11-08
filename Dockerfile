# Use Python 3.11 slim image
FROM python:3.11-slim

# Install system dependencies for Ollama
RUN apt-get update && apt-get install -y \
    curl \
    ca-certificates \
    gnupg \
    && rm -rf /var/lib/apt/lists/*

# Install Ollama with retry logic and verification
RUN set -e; \
    for i in 1 2 3; do \
        curl -fsSL https://ollama.com/install.sh | sh && break || \
        (echo "Attempt $i failed, retrying..." && sleep 5); \
    done && \
    which ollama && ollama --version

# Set working directory
WORKDIR /app

# Copy requirements
COPY requirements-minimal.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements-minimal.txt && \
    pip install --no-cache-dir langchain langchain-groq langchain-chroma langchain-ollama chromadb

# Copy application code
COPY api_server_chroma.py .
COPY setup_backend.py .
COPY database/ ./database/
COPY data/ ./data/

# Pull Ollama model and run setup with better error handling
RUN set -e; \
    ollama serve > /tmp/ollama.log 2>&1 & \
    OLLAMA_PID=$!; \
    sleep 10; \
    echo "Pulling embedding model..."; \
    ollama pull mxbai-embed-large || (cat /tmp/ollama.log && exit 1); \
    echo "Running setup script..."; \
    python setup_backend.py || (cat /tmp/ollama.log && exit 1); \
    kill $OLLAMA_PID || true

# Expose port
EXPOSE 8000

# Start Ollama in background and run FastAPI
CMD ollama serve & sleep 3 && python api_server_chroma.py
