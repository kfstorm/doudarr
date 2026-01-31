FROM python:3.12-alpine

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Set working directory
WORKDIR /app

# Copy dependency files
COPY pyproject.toml uv.lock ./

# Install dependencies
RUN uv sync --frozen --no-dev

# Copy application code
COPY src/ /app/doudarr/

# Create cache volume
VOLUME "/app/cache"

# Expose port
EXPOSE 8000

# Run application
ENTRYPOINT ["uv", "run", "uvicorn", "doudarr.main:app", "--host", "0.0.0.0"]
