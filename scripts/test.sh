#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

# Run pytest
pytest "$@"
