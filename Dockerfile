# Multi-stage build to reduce final image size
FROM python:3.11-slim as builder

WORKDIR /build

# Install build dependencies
COPY requirements-backend.txt .
RUN pip install --no-cache-dir --user -r requirements-backend.txt

# Final stage - minimal runtime image
FROM python:3.11-slim

# Disable ChromaDB telemetry
ENV CHROMA_TELEMETRY_ENABLED=0
ENV PATH=/root/.local/bin:$PATH

# Install only runtime dependencies (no build tools)
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

WORKDIR /app

# Copy installed packages from builder stage
COPY --from=builder /root/.local /root/.local

# Copy application code and data
COPY start.py setup_backend.py conversation_memory.py agentic_planner.py calculator_tool.py ./
COPY config/ ./config/
COPY services/ ./services/
COPY routes/ ./routes/
COPY database/ ./database/
COPY data/ ./data/

# Run setup to initialize ChromaDB (products + guardrail patterns)
RUN python setup_backend.py || echo "Setup completed with warnings"

EXPOSE 8000

# Runtime: Start the application
CMD exec python -u start.py
