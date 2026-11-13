#!/bin/zsh
# Protocol v9a lanes (resumable: re-running skips completed cells). Usage: run_v9a.sh <lane 1-4>
cd "$(dirname "$0")/../.." || exit 1
V=scripts/step3/v9.sh
G=none,strict,cred,flexI_cred
B=tool_filter,spotlighting,repeat_user_prompt
case "$1" in
  1) $V --provider deepseek --conditions $G --attack none --set benign_all --agent default --tag main
     $V --provider deepseek --conditions $G --attack none --set benign_all --agent default --tag rep2
     $V --provider deepseek --conditions $G --attack none --set benign_all --agent default --tag rep3 ;;
  2) $V --provider deepseek --conditions $B --attack none --set benign_all --agent default --tag main
     [ -f "$HOME/.cache/huggingface/.v9_detector_ok" ] && $V --provider deepseek --conditions pi_detector --attack none --set benign_all --agent default --tag main ;;
  3) for a in direct important_instructions guide_aware; do
       $V --provider deepseek --conditions $G --attack $a --set sample200 --agent weak --tag main
     done ;;
  4) for a in direct important_instructions; do
       $V --provider deepseek --conditions $B --attack $a --set sample200 --agent weak --tag main
     done
     [ -f "$HOME/.cache/huggingface/.v9_detector_ok" ] && for a in direct important_instructions; do
       $V --provider deepseek --conditions pi_detector --attack $a --set sample200 --agent weak --tag main
     done ;;
esac
echo "LANE $1 FINISHED"
