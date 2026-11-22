#!/bin/bash
# DD-11A/B/C: every playtest of a pocket four times, two games at a time. four.sh <key> <name> [<name> ...]
OYR="$(cd "$(dirname "$(readlink -f "$0")")/../../../.." && pwd)"   # the repository root
K=$1; shift
X=$OYR/output/studio_cal
out=$X/$K/four.out; : > $out
for n in "$@"; do
  ( for i in 1 2; do $X/dd11/play.sh $K $n _$i; done ) >> $out 2>&1 &
  a=$!
  ( for i in 3 4; do $X/dd11/play.sh $K $n _$i; done ) >> $out 2>&1 &
  b=$!
  while kill -0 $a 2>/dev/null || kill -0 $b 2>/dev/null; do sleep 3; done
done
cat $out
