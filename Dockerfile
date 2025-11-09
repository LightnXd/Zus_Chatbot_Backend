# Optimized Dockerfile - Minimal build size
FROM python:3.11-slim

# Disable ChromaDB telemetry
ENV CHROMA_TELEMETRY_ENABLED=0

# Install minimal system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy and install Python dependencies (leverage Docker cache)
COPY requirements-backend.txt .
RUN pip install --no-cache-dir -r requirements-backend.txt \
    && pip cache purge \
    && rm -rf /root/.cache/pip

# Copy application code and data in fewer layers
COPY start.py setup_backend.py conversation_memory.py agentic_planner.py calculator_tool.py ./
COPY config/ ./config/
COPY services/ ./services/
COPY routes/ ./routes/
COPY database/ ./database/
COPY data/ ./data/
COPY chroma_db ./chroma_db

EXPOSE 8000

# Runtime setup: Model will download on first use (~80MB, cached in Railway volume)
CMD echo "🚀 Using HuggingFace embeddings (downloads on first use)"; \
    echo "✅ Using pre-built ChromaDB with 35 products"; \
    exec python -u start.py
