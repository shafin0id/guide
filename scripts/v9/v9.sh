#!/bin/zsh
# Thin launcher: v9.sh <args to run_v9>. Runs from the repo root with the project venv.
cd "$(dirname "$0")/../.." || exit 1
export PYTHONPATH=src
exec .venv/bin/python -m guide_agentdojo.run_v9 "$@"
