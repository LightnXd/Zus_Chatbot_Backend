# Optimized Dockerfile - Reduced from 2.3GB to ~800MB (removed Ollama)
FROM python:3.11-slim

# Disable ChromaDB telemetry
ENV CHROMA_TELEMETRY_ENABLED=0

# Install minimal system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy and install Python dependencies
COPY requirements-backend.txt .
RUN pip install --no-cache-dir -r requirements-backend.txt

# Copy application code and data
COPY start.py .
COPY setup_backend.py .
COPY config/ ./config/
COPY services/ ./services/
COPY routes/ ./routes/
COPY database/ ./database/
COPY data/ ./data/
# Copy pre-built ChromaDB with 35 embedded products (3.5MB)
COPY chroma_db ./chroma_db
RUN ls -laR chroma_db/ || echo "❌ chroma_db directory not found in image"
COPY conversation_memory.py .
COPY agentic_planner.py .
COPY calculator_tool.py .

EXPOSE 8000

# Runtime setup: Start API server
# Using HuggingFace embeddings (no Ollama needed)
CMD echo "🚀 Using HuggingFace embeddings (fast and reliable)"; \
    echo "✅ Using pre-built ChromaDB with 35 products"; \
    echo "Starting API server..."; \
    exec python -u start.py
