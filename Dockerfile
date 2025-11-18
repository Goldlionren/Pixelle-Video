# Pixelle-Video Docker Image
# Based on Python 3.11 slim for smaller image size

FROM python:3.11-slim

# Build arguments for mirror configuration
# USE_CN_MIRROR: whether to use China mirrors (true/false)
# UV_INDEX_URL: Python package index URL (defaults to Tsinghua when USE_CN_MIRROR=true)
ARG USE_CN_MIRROR=false
ARG UV_INDEX_URL=https://pypi.tuna.tsinghua.edu.cn/simple

# Set working directory
WORKDIR /app

# Replace apt sources with China mirrors if needed
# Debian 12 uses DEB822 format in /etc/apt/sources.list.d/debian.sources
RUN if [ "$USE_CN_MIRROR" = "true" ]; then \
    sed -i 's|deb.debian.org|mirrors.aliyun.com|g' /etc/apt/sources.list.d/debian.sources && \
    sed -i 's|security.debian.org|mirrors.aliyun.com|g' /etc/apt/sources.list.d/debian.sources; \
    fi

# Install system dependencies
# - curl: for health checks and downloads
# - ffmpeg: for video/audio processing
# - chromium: for html2image rendering
# - fonts-noto-cjk: for CJK character support
RUN apt-get update && apt-get install -y \
    curl \
    ffmpeg \
    chromium \
    chromium-driver \
    fonts-noto-cjk \
    && rm -rf /var/lib/apt/lists/*

# Install uv package manager
# For China: use pip to install uv from mirror (faster and more stable)
# For International: use official installer script
RUN if [ "$USE_CN_MIRROR" = "true" ]; then \
        pip install --no-cache-dir -i https://pypi.tuna.tsinghua.edu.cn/simple/ uv; \
    else \
        curl -LsSf https://astral.sh/uv/install.sh | sh; \
    fi
ENV PATH="/root/.local/bin:$PATH"
RUN uv --version

# Copy dependency files and source code for building
# Note: pixelle_video is needed for hatchling to build the package
COPY pyproject.toml uv.lock README.md ./
COPY pixelle_video ./pixelle_video

# Install Python dependencies using uv with configurable index URL
# Auto-select China mirror when USE_CN_MIRROR=true and UV_INDEX_URL is default
# Set longer timeout and use --default-index parameter to replace PyPI
# Note: --default-index replaces PyPI as the default source
RUN if [ "$USE_CN_MIRROR" = "true" ] && [ "$UV_INDEX_URL" = "https://pypi.tuna.tsinghua.edu.cn/simple" ]; then \
        export UV_HTTP_TIMEOUT=300 && \
        uv sync --frozen --no-dev --default-index https://pypi.tuna.tsinghua.edu.cn/simple; \
    else \
        export UV_HTTP_TIMEOUT=300 && \
        uv sync --frozen --no-dev --default-index $UV_INDEX_URL; \
    fi

# Copy rest of application code
COPY api ./api
COPY web ./web
COPY bgm ./bgm
COPY templates ./templates
COPY workflows ./workflows
COPY resources ./resources

# Create output and data directories
RUN mkdir -p /app/output /app/data

# Set environment variables for html2image to use chromium
ENV BROWSER_EXECUTABLE_PATH=/usr/bin/chromium
ENV CHROME_BIN=/usr/bin/chromium

# Expose ports
# 8000: API service
# 8501: Web UI service
EXPOSE 8000 8501

# Default command (can be overridden in docker-compose)
CMD ["uv", "run", "python", "api/app.py"]

