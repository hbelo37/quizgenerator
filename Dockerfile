# Use Python 3.11 slim image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy backend requirements first (for better caching)
COPY backend/requirements.txt /app/backend/requirements.txt

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r backend/requirements.txt

# Copy backend code
COPY backend/ /app/backend/

# Set working directory to backend
WORKDIR /app/backend

# Expose port (Railway will set PORT env var)
EXPOSE 8000

# IMPORTANT:
# Use an ENTRYPOINT script so the container starts reliably even if the platform
# overrides the "command" (which can cause `cd`-related failures).
ENTRYPOINT ["/bin/sh", "/app/backend/start.sh"]
