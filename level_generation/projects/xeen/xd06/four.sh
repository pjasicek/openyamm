#!/bin/bash
# four.sh: the main playtest (own mount) and the exit playtest (combined play mount) four times each, two games at once
OYR="$(cd "$(dirname "$(readlink -f "$0")")/../../../.." && pwd)"   # the repository root
X=$OYR/output/studio_cal/xd06
for n in 1 2 3 4; do
  $OYR/level_generation/projects/xeen/xd06/play.sh playtest.yml four_$n & $OYR/level_generation/projects/xeen/xd06/play_exit.sh exit_$n & wait
done
