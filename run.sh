#!/usr/bin/env sh

set -e

# Run the application
# Use --no-dev to ensure uv only uses the already installed runtime dependencies
exec uv run --no-dev uvicorn doudarr.main:app --host 0.0.0.0
