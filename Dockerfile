FROM python:3.10-slim

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    UV_SYSTEM_PYTHON=1

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential curl \
    && rm -rf /var/lib/apt/lists/*

# Install deps first for better layer caching
COPY pyproject.toml uv.lock ./
RUN python -m pip install --no-cache-dir uv \
    && uv sync --locked --no-dev --frozen --system

# App code
COPY backend ./backend

EXPOSE 12345

CMD ["uvicorn", "backend.server:app", "--host", "0.0.0.0", "--port", "12345"]

