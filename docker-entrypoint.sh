#!/bin/bash
set -e

# Start Redis server in the background
redis-server --daemonize yes

# Wait for Redis to be ready
until redis-cli ping; do
  echo "Waiting for Redis to be ready..."
  sleep 1
done

# Start Celery worker in the background
celery -A celery_worker.celery worker --pool=solo -l info &

# Wait for Celery to initialize
sleep 2

# Start Flask application with Waitress
waitress-serve --host=$HOST --port=$PORT app:app 