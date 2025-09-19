# Stage 1: Builder for dependencies
FROM python:3.11-slim as builder

WORKDIR /app

# Install build tools for some Python packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc g++ \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

# Stage 2: Production image
FROM python:3.11-slim

# Environment settings
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH=/home/appuser/.local/bin:$PATH \
    TZ=UTC

# Install runtime tools
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN useradd -m -u 1000 appuser && mkdir -p /app && chown -R appuser:appuser /app

WORKDIR /app

# Copy installed Python deps from builder
COPY --from=builder /root/.local /home/appuser/.local

# Copy app files
COPY --chown=appuser:appuser . .

# Create logs/data dirs
RUN mkdir -p /app/logs /app/data && chown -R appuser:appuser /app/logs /app/data

USER appuser

# Expose FastAPI port
EXPOSE 8000

# Healthcheck (check /health endpoint in your FastAPI)
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Start FastAPI with uvicorn
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
