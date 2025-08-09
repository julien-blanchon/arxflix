# syntax=docker/dockerfile:1.7

# Unified image that installs frontend and backend requirements
# and serves the Gradio app defined in `arxflix_gradio.py`.

FROM python:3.11-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    DEBIAN_FRONTEND=noninteractive

WORKDIR /app

# 1) System dependencies
#  - ffmpeg: required by whisper / video pipeline
#  - libsndfile1: required by python-soundfile
#  - build-essential, git, curl, ca-certificates: build & tooling
RUN apt-get update && apt-get install -y --no-install-recommends \
      ffmpeg \
      libsndfile1 \
      build-essential \
      git \
      curl \
      ca-certificates \
      # Chrome/Chromium headless dependencies required by Remotion renderer
      libnss3 \
      libnspr4 \
      libxss1 \
      libasound2 \
      libatk1.0-0 \
      libatk-bridge2.0-0 \
      libcups2 \
      libdrm2 \
      libgbm1 \
      libxkbcommon0 \
      libxcomposite1 \
      libxdamage1 \
      libxrandr2 \
      libatspi2.0-0 \
      libgtk-3-0 \
      libx11-6 \
      libx11-xcb1 \
      libxcb1 \
      libxext6 \
      libxfixes3 \
      libpangocairo-1.0-0 \
      libpango-1.0-0 \
      libcairo2 \
      libfontconfig1 \
      fonts-liberation \
      fonts-dejavu-core \
    && rm -rf /var/lib/apt/lists/*

# 2) Node + pnpm for frontend dependencies
#    (We install NodeJS and pnpm globally then run `pnpm install` in frontend.)
RUN curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get update && apt-get install -y --no-install-recommends nodejs \
    && npm i -g pnpm@9 \
    && rm -rf /var/lib/apt/lists/*

# 3) Install Python backend requirements first for better layer caching
# Prefer the Docker-friendly requirements if present
COPY requirements-docker.txt ./requirements-docker.txt
RUN pip install --no-cache-dir -r requirements-docker.txt

# 4) Install frontend dependencies using pnpm
WORKDIR /app/frontend
COPY frontend/pnpm-lock.yaml ./pnpm-lock.yaml
COPY frontend/package.json ./package.json
RUN pnpm install --frozen-lockfile

# 5) Copy application source
WORKDIR /app
COPY . .

# 6) Runtime env for Gradio
ENV GRADIO_SERVER_NAME=0.0.0.0 \
    GRADIO_SERVER_PORT=7860

EXPOSE 7860

# 7) Start the Gradio UI
CMD ["python", "-u", "arxflix_gradio.py"]


