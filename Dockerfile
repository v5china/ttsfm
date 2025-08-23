FROM python:3.11-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8000

# Install dependencies
RUN apt-get update && apt-get install -y gcc curl git && rm -rf /var/lib/apt/lists/*

# Copy source code first
COPY ttsfm/ ./ttsfm/
COPY ttsfm-web/ ./ttsfm-web/
COPY pyproject.toml ./
COPY requirements.txt ./
COPY .git/ ./.git/

# Install the TTSFM package with web dependencies
RUN pip install --no-cache-dir -e .[web]

# Install additional web dependencies
RUN pip install --no-cache-dir python-dotenv>=1.0.0 flask-socketio>=5.3.0 python-socketio>=5.10.0 eventlet>=0.33.3

# Create non-root user
RUN useradd --create-home ttsfm && chown -R ttsfm:ttsfm /app
USER ttsfm

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/api/health || exit 1

WORKDIR /app/ttsfm-web
# Use run.py for proper eventlet initialization
CMD ["python", "run.py"]
