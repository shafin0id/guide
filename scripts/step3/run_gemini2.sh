#!/bin/zsh
# Protocol v9g-2 lane: run_gemini2.sh <lane 1-4>; resumable.
cd "$(dirname "$0")/../.." || exit 1
V="scripts/step3/v9.sh --provider gemini --agent default --tag gemini"
A="--attack important_instructions --set sample200 --limit 20"
case "$1" in
  1) $=V --conditions none,strict $=A ;;
  2) $=V --conditions cred,flexI_cred $=A ;;
  3) $=V --conditions tool_filter,spotlighting $=A ;;
  4) $=V --conditions repeat_user_prompt $=A
     $=V --conditions none,strict,cred,flexI_cred --attack none --set benign_all ;;
esac
echo "GEMINI LANE $1 FINISHED"
