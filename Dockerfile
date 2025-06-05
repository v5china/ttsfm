FROM python:3.11-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8000

# Install dependencies
RUN apt-get update && apt-get install -y gcc curl && rm -rf /var/lib/apt/lists/*

# Copy and install requirements
COPY requirements.txt ttsfm-web/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY ttsfm/ ./ttsfm/
COPY ttsfm-web/ ./ttsfm-web/
COPY pyproject.toml ./

# Install package
RUN pip install -e .

# Create non-root user
RUN useradd --create-home ttsfm && chown -R ttsfm:ttsfm /app
USER ttsfm

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/api/health || exit 1

CMD ["python", "-m", "waitress", "--host=0.0.0.0", "--port=8000", "ttsfm-web.app:app"]
