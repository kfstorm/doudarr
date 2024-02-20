#!/usr/bin/env bash

set -euo pipefail

# read the `--check` arg from the command line
check=false
if [ $# -gt 0 ] && [[ $1 == "--check" ]]; then
  check=true
fi

black_args=()
if [[ "$check" == "true" ]]; then
  black_args+=(--check --diff)
fi

cd $(git rev-parse --show-toplevel)

# find all Python files
python_files=$(git ls-files | grep '\.py$' || true)

black "${black_args[@]}" $python_files
flake8 $python_files
