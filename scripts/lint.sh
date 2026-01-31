#!/usr/bin/env bash

set -euo pipefail

# read the `--check` arg from the command line
check=false
if [ $# -gt 0 ] && [[ $1 == "--check" ]]; then
	check=true
fi

cd "$(dirname "${BASH_SOURCE[0]}")/.."

# Check or update README.md
if [[ "$check" == "true" ]]; then
	uv run python scripts/update_readme.py --check
else
	uv run python scripts/update_readme.py
fi

black_args=()
if [[ "$check" == "true" ]]; then
	black_args+=(--check --diff)
fi

# find all Python files
python_files=$(git ls-files | grep '\.py$' || true)

uv run black "${black_args[@]}" $python_files
uv run flake8 $python_files
