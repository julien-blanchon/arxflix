SHELL := /bin/bash

# Configurable variables
PYTHON ?= python3
PIP    ?= $(PYTHON) -m pip
PORT   ?= 7860
IMAGE  ?= arxflix
ENV_FILE ?= .env
GENERATED_VIDEOS_DIR ?= $(CURDIR)/generated_videos

.PHONY: help gradio mac-gradio pc-gradio gradio-docker frontend-deps mac-sys-deps pc-sys-deps install run mac-install pc-install mac-run pc-run

help:
	@echo "Available targets:"
	@echo "  make gradio         - Run Gradio app (assumes deps already installed)"
	@echo "  make mac-gradio     - macOS: Install backend deps (backend/requirements.txt), frontend deps, then run Gradio"
	@echo "  make pc-gradio      - Linux/PC: Install backend deps (requirements-docker.txt), frontend deps, then run Gradio"
	@echo "  make gradio-docker  - Build & run Docker container serving Gradio"
	@echo "  make install        - Detect OS; install appropriate backend + frontend dependencies"
	@echo "  make run            - Detect OS; run Gradio app"

gradio:
	$(PYTHON) arxflix_gradio.py

# ----- Cross-platform convenience -----
install:
	@OS=$$(uname -s); \
	if [ "$$OS" = "Darwin" ]; then \
	  echo "Detected macOS. Running mac-install..."; \
	  $(MAKE) mac-install; \
	else \
	  echo "Detected non-macOS. Running pc-install..."; \
	  $(MAKE) pc-install; \
	fi

run:
 	@OS=$$(uname -s); \
	if [ "$$OS" = "Darwin" ]; then \
	  echo "Detected macOS. Running mac-run..."; \
	  $(MAKE) mac-run; \
	else \
	  echo "Detected non-macOS. Running pc-run..."; \
	  $(MAKE) pc-run; \
	fi

# ----- macOS workflow -----
mac-gradio: mac-sys-deps
	$(PIP) install --upgrade pip setuptools wheel
	$(PIP) install -r backend/requirements.txt
	$(MAKE) frontend-deps
	$(PYTHON) arxflix_gradio.py

mac-install: mac-sys-deps
	$(PIP) install --upgrade pip setuptools wheel
	$(PIP) install -r backend/requirements.txt
	$(MAKE) frontend-deps

mac-run:
	$(PYTHON) arxflix_gradio.py

mac-sys-deps:
	@if [ "$$(uname -s)" != "Darwin" ]; then \
	  echo "This target is intended for macOS (Darwin). Current: $$(uname -s)"; \
	fi
	@if command -v brew >/dev/null 2>&1; then \
	  echo "Installing macOS system dependencies via Homebrew..."; \
	  brew install node pnpm ffmpeg libsndfile || true; \
	else \
	  echo "Homebrew not found. Please install Node.js, pnpm, ffmpeg, and libsndfile manually."; \
	fi

# ----- Linux/PC workflow -----
pc-gradio: pc-sys-deps
	$(PIP) install --upgrade pip setuptools wheel
	$(PIP) install -r requirements-docker.txt
	$(MAKE) frontend-deps
	$(PYTHON) arxflix_gradio.py

pc-install: pc-sys-deps
	$(PIP) install --upgrade pip setuptools wheel
	$(PIP) install -r requirements-docker.txt
	$(MAKE) frontend-deps

pc-run:
	$(PYTHON) arxflix_gradio.py

pc-sys-deps:
	@if command -v apt-get >/dev/null 2>&1; then \
	  echo "Installing Linux system dependencies via apt-get..."; \
	  sudo apt-get update; \
	  sudo apt-get install -y ffmpeg libsndfile1 nodejs npm; \
	  sudo npm i -g pnpm@9; \
	else \
	  echo "apt-get not found. Please install Node.js, npm, pnpm, ffmpeg, and libsndfile1 manually."; \
	fi

# ----- Frontend deps -----
frontend-deps:
	@echo "Installing frontend dependencies..."
	@if ! command -v pnpm >/dev/null 2>&1; then \
	  if command -v npm >/dev/null 2>&1; then \
	    echo "pnpm not found. Installing pnpm globally via npm..."; \
	    npm i -g pnpm@9; \
	  else \
	    echo "npm not found. Please install Node.js (which includes npm) and pnpm."; \
	    exit 1; \
	  fi; \
	fi
	cd frontend && pnpm install

# ----- Docker workflow -----
gradio-docker:
	@[ -d "$(GENERATED_VIDEOS_DIR)" ] || mkdir -p "$(GENERATED_VIDEOS_DIR)"
	@echo "Building Docker image $(IMAGE)..."
	docker build -t $(IMAGE) .
	@echo "Running Docker container on port $(PORT)..."
	@set -e; \
	ENV_ARG=""; \
	if [ -f "$(ENV_FILE)" ]; then \
	  ENV_ARG="--env-file $(ENV_FILE)"; \
	  echo "Using env file: $(ENV_FILE)"; \
	else \
	  echo "Env file $(ENV_FILE) not found. Continuing without it."; \
	fi; \
	docker run --rm -it \
	  -p $(PORT):7860 \
	  $$ENV_ARG \
	  -v "$(GENERATED_VIDEOS_DIR):/app/generated_videos" \
	  $(IMAGE)


