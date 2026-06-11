FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app/backend \
    PIP_EXTRA_INDEX_URL=https://download.pytorch.org/whl/cpu \
    GRAPHITE_PORT=8001 \
    PORT=8001

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    cmake \
    espeak-ng \
    ffmpeg \
    libsndfile1 \
    && ln -sf /usr/bin/espeak-ng /usr/local/bin/espeak \
    && rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt /app/backend/requirements.txt

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir torch==2.12.0+cpu && \
    pip install --no-cache-dir -r /app/backend/requirements.txt

COPY backend /app/backend
COPY frontend/build /app/frontend/build
COPY presentation.html /app/presentation.html

RUN mkdir -p /app/backend/data/audio /app/backend/data/model-cache /app/backend/data/models

CMD ["sh", "-c", "gunicorn --chdir /app/backend --bind 0.0.0.0:${PORT:-8001} server:app"]