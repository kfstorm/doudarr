FROM python:3.12-alpine

# Install uv
RUN --mount=type=cache,target=/root/.cache/pip pip install uv

# Copy dependency files first for better caching
COPY pyproject.toml uv.lock ./

# Install dependencies before copying source code
RUN --mount=type=cache,target=/root/.cache/uv uv sync --frozen --no-dev

# Create UV cache directory with proper permissions for non-root users
RUN mkdir -p /.cache/uv && chmod 777 /.cache/uv

# Copy application code and scripts
COPY src/ /app/doudarr/
COPY run.sh /run.sh

# Set working directory
WORKDIR /app

# Create cache volume
VOLUME "/app/cache"

# Expose port
EXPOSE 8000

# Run application
ENTRYPOINT ["/run.sh"]
