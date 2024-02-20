#!/usr/bin/env bash

set -euo pipefail

cd $(git rev-parse --show-toplevel)

rm -f .git/hooks/pre-commit
ln -s ../../scripts/hooks/pre-commit .git/hooks/pre-commit
