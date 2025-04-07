# Use Python 3.13 slim image as base
FROM python:3.13-slim

# Install Redis
RUN apt-get update && \
    apt-get install -y redis-server && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first to leverage Docker cache
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY . .

# Create directory for Redis data
RUN mkdir -p /data/redis

# Set default environment variables
ENV HOST=0.0.0.0 \
    PORT=7000 \
    VERIFY_SSL=true \
    MAX_QUEUE_SIZE=100 \
    FLASK_ENV=production \
    FLASK_APP=app.py \
    CELERY_BROKER_URL=redis://localhost:6379/0 \
    CELERY_RESULT_BACKEND=redis://localhost:6379/0

# Expose ports for Flask and Redis
EXPOSE 7000 6379

# Copy the startup script
COPY docker-entrypoint.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/docker-entrypoint.sh

# Set the entrypoint
ENTRYPOINT ["docker-entrypoint.sh"] 