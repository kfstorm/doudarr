#!/usr/bin/env bash

set -euo pipefail

# read the `--check` arg from the command line
check=false
if [ $# -gt 0 ] && [[ $1 == "--check" ]]; then
	check=true
fi

cd "$(dirname "${BASH_SOURCE[0]}")/.."

# Determine which command to use (uv run or direct)
if command -v uv &> /dev/null; then
	PYTHON_CMD="uv run python"
	BLACK_CMD="uv run black"
	FLAKE8_CMD="uv run flake8"
else
	PYTHON_CMD="python"
	BLACK_CMD="black"
	FLAKE8_CMD="flake8"
fi

# Check or update README.md
if [[ "$check" == "true" ]]; then
	$PYTHON_CMD scripts/update_readme.py --check
else
	$PYTHON_CMD scripts/update_readme.py
fi

black_args=()
if [[ "$check" == "true" ]]; then
	black_args+=(--check --diff)
fi

# find all Python files
python_files=$(git ls-files | grep '\.py$' || true)

$BLACK_CMD "${black_args[@]}" $python_files
$FLAKE8_CMD $python_files
