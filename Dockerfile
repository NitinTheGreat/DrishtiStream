# DrishtiStream Dockerfile
# =========================
# Cloud Run compatible container definition.
#
# Build: docker build -t drishti-stream .
# Run:   docker run -p 8000:8000 -v $(pwd)/data:/app/data drishti-stream

FROM python:3.11-slim

# Metadata
LABEL maintainer="Drishti Project"
LABEL description="Virtual camera abstraction layer for Drishti system"
LABEL version="1.0.0"

# Security: Run as non-root user
RUN useradd --create-home --shell /bin/bash appuser

# Set working directory
WORKDIR /app

# Install system dependencies for OpenCV
# (headless version, no GUI libraries needed)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for layer caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY src/ ./src/
COPY config.yaml .

# Create data directory (videos will be mounted here)
RUN mkdir -p /app/data

# Change ownership to non-root user
RUN chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Expose port (Cloud Run uses PORT env variable)
EXPOSE 8000

# Health check endpoint
HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:${PORT:-8000}/health || exit 1

# Run the application
# Cloud Run sets PORT environment variable
CMD ["sh", "-c", "uvicorn src.drishti_stream.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
