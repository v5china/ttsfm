FROM python:3.11-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8000

# Install dependencies
RUN apt-get update && apt-get install -y gcc curl && rm -rf /var/lib/apt/lists/*

# Copy source code first
COPY ttsfm/ ./ttsfm/
COPY ttsfm-web/ ./ttsfm-web/
COPY pyproject.toml ./
COPY requirements.txt ./

# Install the TTSFM package with web dependencies
RUN pip install --no-cache-dir -e .[web]

# Install additional web dependencies
RUN pip install --no-cache-dir python-dotenv>=1.0.0

# Create non-root user
RUN useradd --create-home ttsfm && chown -R ttsfm:ttsfm /app
USER ttsfm

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/api/health || exit 1

WORKDIR /app/ttsfm-web
CMD ["python", "-m", "waitress", "--host=0.0.0.0", "--port=8000", "app:app"]
