#!/bin/bash
# DD-06: playtest x4 and playtest_hostility x4 (two lanes, one game each at a time)
OYR="$(cd "$(dirname "$(readlink -f "$0")")/../../../.." && pwd)"   # the repository root
X=$OYR/output/studio_cal/dd06
( for i in 1 2 3 4; do $OYR/level_generation/projects/xeen/dd06/play.sh playtest _$i; done ) > $X/four_a.out 2>&1 &
a=$!
( for i in 1 2 3 4; do $OYR/level_generation/projects/xeen/dd06/play.sh playtest_hostility _$i; done ) > $X/four_b.out 2>&1 &
b=$!
while kill -0 $a 2>/dev/null || kill -0 $b 2>/dev/null; do sleep 3; done
cat $X/four_a.out $X/four_b.out
