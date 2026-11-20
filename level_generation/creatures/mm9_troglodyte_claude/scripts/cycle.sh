#!/bin/bash
# rig (heat, weights), runtime, viewer. Project folder. scripts/cycle.sh <rev> [--install]
cd /home/pjasicek/github/OpenYAMM/level_generation/creatures/mm9_troglodyte_claude
scripts/rig.sh 2>&1 | tail -3 | cut -c1-100
scripts/rebuild.sh $2 2>&1 | grep -v -E '^ {3}|^  --|^$|^Operations|^--raise' | tail -22 | cut -c1-170
scripts/viewer_update.sh $1
echo CYCLEDONE
