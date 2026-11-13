#!/bin/zsh
# pi_detector lane (local DeBERTa, ~1 GB RAM): benign, then both attacks; resumable.
cd "$(dirname "$0")/../.." || exit 1
V=scripts/step3/v9.sh
$V --provider deepseek --conditions pi_detector --attack none --set benign_all --agent default --tag main
for a in direct important_instructions; do
  $V --provider deepseek --conditions pi_detector --attack $a --set sample200 --agent weak --tag main
done
echo "PI LANE FINISHED"
