#!/bin/bash
# One model at a time through shots.sh, each started only while fewer than 2 viewer shot scripts run on the machine.
cd "$(dirname "$0")/.."
for m in ${1:-inst_a red_a inst_b red_b inst_c red_c}; do
  while [ "$(ps -eo args | grep -c '^node .*viewer_shots.mjs')" -ge 2 ]; do sleep 5; done
  echo "== $m"; scripts/shots.sh $m
done
echo QUEUEDONE
