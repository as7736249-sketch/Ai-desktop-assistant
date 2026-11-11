# ─────────────────────────────────────────────────────────────
#  Jarvis AI Desktop Assistant — server/container image
#  Runs the real FastAPI + uvicorn server (works on Render,
#  Railway, Fly.io, Koyeb, or any Docker host). Free tiers exist.
# ─────────────────────────────────────────────────────────────
FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    AUTO_OPEN_BROWSER=False \
    API_HOST=0.0.0.0

WORKDIR /app

# Install dependencies first (better layer caching)
COPY backend/requirements.txt backend/requirements.txt
RUN pip install --upgrade pip && pip install -r backend/requirements.txt

# App code + static frontend
COPY backend backend
COPY frontend frontend

WORKDIR /app/backend

EXPOSE 8000
# Bind to the host's $PORT (Render/Railway set it), default 8000
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
