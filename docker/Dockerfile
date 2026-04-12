# ============================================
# Wukong AI Platform - Backend Dockerfile
# Multi-stage build for production optimization
# ============================================

# Stage 1: Builder - Install dependencies
FROM python:3.11-slim AS builder

WORKDIR /build

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt


# Stage 2: Runtime - Production image
FROM python:3.11-slim

LABEL maintainer="Wukong AI Team"
LABEL description="Wukong AI Platform - Enterprise AI Native Workspace"
LABEL version="1.0.0"

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# Install system dependencies for Python packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    # For sentence-transformers (RAG)
    libopenblas-dev \
    # For PDF processing
    poppler-utils \
    tesseract-ocr \
    # For image processing
    libjpeg62-turbo \
    # Network tools
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy from builder stage
COPY --from=builder /install /usr/local

# Create non-root user for security
RUN groupadd -r wukong && useradd -r -g wukong -d /app -s /sbin/nologin wukong \
    && mkdir -p /app/data/files /app/data/skills /app/logs \
    && chown -R wukong:wukong /app

USER wukong

# Copy application code
COPY backend/ .

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

EXPOSE 8000

# Gunicorn with Uvicorn workers
CMD ["gunicorn", "main:app", 
     "--bind", "0.0.0.0:8000",
     "--workers", "4",
     "--worker-class", "uvicorn.workers.UvicornWorker",
     "--worker-tmp-dir", "/dev/shm",
     "--access-logfile", "-",
     "--error-logfile", "-",
     "--log-level", "info"]
