# syntax=docker/dockerfile:1
FROM python:3.11-slim

# Prevent Python from writing .pyc files and buffering stdout.
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install build dependencies required by Prophet (pystan/Cython).
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code.
COPY . .

# Non-root user for security.
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Default port; override via SERVICE_PORT if needed.
EXPOSE 8000

# Use uvicorn with a single worker (Prophet training is CPU-bound).
# All configuration (host, port) is read from environment variables.
CMD ["sh", "-c", "uvicorn main:app --host ${SERVICE_HOST:-0.0.0.0} --port ${SERVICE_PORT:-8000}"]
