#!/usr/bin/env bash
d=$(cd "$(dirname "$0")/.." && pwd)
for i in 0 1 2 3; do
  ( "$d/run_lane.sh" after "$d/lanes/after_$i.txt" > "$d/lanes/log_after_$i.txt" 2>&1
    "$d/run_lane.sh" before "$d/lanes/before_$i.txt" > "$d/lanes/log_before_$i.txt" 2>&1 ) &
done
wait
echo ALL_DONE > "$d/lanes/ALL_DONE"
