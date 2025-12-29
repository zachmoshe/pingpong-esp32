FROM python:3.10-slim

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    UV_SYSTEM_PYTHON=1

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential curl \
    && rm -rf /var/lib/apt/lists/*

RUN pip install -U pip

# Install deps first for better layer caching
COPY pyproject.toml uv.lock ./
RUN python -m pip install --no-cache-dir uv \
    && uv sync --locked --no-dev

# App code
COPY backend ./backend

EXPOSE 12345

CMD ["uv", "run", "python", "backend/server.py"]

