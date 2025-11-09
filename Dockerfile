# Optimized Dockerfile - Target <2GB final image
FROM python:3.11-slim

# Disable ChromaDB telemetry
ENV CHROMA_TELEMETRY_ENABLED=0

# Set environment variables to reduce model cache size
ENV HF_HOME=/tmp/huggingface
ENV TRANSFORMERS_CACHE=/tmp/transformers
ENV SENTENCE_TRANSFORMERS_HOME=/tmp/sentence-transformers

# Install minimal system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy and install Python dependencies (leverage Docker cache)
COPY requirements-backend.txt .
RUN pip install --no-cache-dir -r requirements-backend.txt \
    && pip cache purge

# Pre-download the embedding model to a temporary location and clean up cache
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')" \
    && rm -rf /root/.cache/huggingface \
    && rm -rf /tmp/*

# Copy application code and data in fewer layers
COPY start.py setup_backend.py conversation_memory.py agentic_planner.py calculator_tool.py ./
COPY config/ ./config/
COPY services/ ./services/
COPY routes/ ./routes/
COPY database/ ./database/
COPY data/ ./data/
COPY chroma_db ./chroma_db

EXPOSE 8000

# Runtime setup: Start API server
CMD echo "🚀 Using HuggingFace embeddings (fast and reliable)"; \
    echo "✅ Using pre-built ChromaDB with 35 products"; \
    exec python -u start.py
