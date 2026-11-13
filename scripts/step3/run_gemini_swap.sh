#!/bin/zsh
# Runs the frozen v9g Gemini block, swapping API keys (from .env.gemini_keys) when a key's daily quota is exhausted.
cd "$(dirname "$0")/../.." || exit 1
while read -r K; do
  [ -z "$K" ] && continue
  export GEMINI_API_KEY="$K"
  for try in 1 2 3; do
    out=$(scripts/step3/v9.sh --provider gemini --agent default --tag gemini --conditions none,strict,cred,flexI_cred \
          --attack important_instructions --set sample200 --limit 5 2>&1); rc=$?
    echo "$out" | grep -E "^(DONE|STOP)"
    [ $rc -eq 3 ] && { echo "KEY ...${K: -4} EXHAUSTED"; break; }
    echo "$out" | grep -q "failed=0" && { echo "GEMINI BLOCK COMPLETE"; exit 0; }
    sleep 30
  done
done < .env.gemini_keys
echo "ALL KEYS EXHAUSTED"
