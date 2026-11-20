#!/bin/bash
# runtime + viewer + gates (no heat). scripts/cycle2.sh <rev> [--install]
cd /home/pjasicek/github/OpenYAMM/level_generation/creatures/mm9_troglodyte_claude
rm -f review/gates/done.txt
scripts/rebuild.sh $2 2>&1 | grep -v -E '^ {3}|^  --|^$|^Operations|^--raise' | tail -24 | cut -c1-170
scripts/viewer_update.sh $1
. scripts/env.sh; $G scripts/head_ref.py 2>&1 | tail -1
scripts/gates.sh
echo CYCLEDONE
