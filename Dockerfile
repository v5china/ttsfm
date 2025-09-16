FROM python:3.11-slim AS builder

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml ./
COPY README.md ./
COPY requirements.txt ./
COPY ttsfm/ ./ttsfm/

ARG VERSION=0.0.0
ENV SETUPTOOLS_SCM_PRETEND_VERSION=${VERSION}

RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir --prefix /install .[web]

FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8000

WORKDIR /app

RUN useradd --create-home --shell /usr/sbin/nologin ttsfm

COPY --from=builder /install /usr/local
ENV PATH="/usr/local/bin:$PATH"

COPY --chown=ttsfm:ttsfm ttsfm-web/ ./ttsfm-web/

USER ttsfm

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD ["python", "-c", "import urllib.request; urllib.request.urlopen('http://localhost:8000/api/health', timeout=5)"]

WORKDIR /app/ttsfm-web
CMD ["python", "run.py"]
