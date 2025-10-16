# RentFlow Production Dockerfile
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p instance logs uploads && \
    chmod 755 instance logs uploads

# Create non-root user
RUN useradd -m -u 1000 rentflow && \
    chown -R rentflow:rentflow /app

# Switch to non-root user
USER rentflow

# Set environment variables
ENV FLASK_APP=main.py \
    PYTHONUNBUFFERED=1 \
    FLASK_ENV=production

# Expose port
EXPOSE 8000

# Health check using Python's built-in urllib
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health', timeout=5)" || exit 1

# Run gunicorn with configurable workers
CMD gunicorn \
     --bind 0.0.0.0:8000 \
     --workers ${GUNICORN_WORKERS:-4} \
     --threads ${GUNICORN_THREADS:-2} \
     --timeout ${GUNICORN_TIMEOUT:-120} \
     --access-logfile logs/access.log \
     --error-logfile logs/error.log \
     --log-level info \
     --worker-class sync \
     main:app
