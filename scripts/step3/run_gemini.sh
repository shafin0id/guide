#!/bin/zsh
# Protocol v9g: Gemini 3.1 Flash-Lite replication (free-tier quota of 500 requests/day/model). Resumable.
cd "$(dirname "$0")/../.." || exit 1
export PYTHONPATH=src
.venv/bin/python -m guide_agentdojo.run_v9 --provider gemini --agent default --conditions none,strict,cred,flexI_cred \
  --attack important_instructions --set sample200 --limit 6 --tag gemini
echo "GEMINI BLOCK EXIT $?"
