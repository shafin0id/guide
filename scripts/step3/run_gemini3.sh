#!/bin/zsh
cd "$(dirname "$0")/../.." || exit 1
for i in 1 2 3; do
  scripts/step3/v9.sh --provider gemini --agent default --tag gemini --conditions none,strict,cred,flexI_cred \
    --attack important_instructions --set sample200 --limit 5 && break
  sleep 60
done
echo "GEMINI3 FINISHED"
