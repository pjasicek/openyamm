#!/bin/bash
# all clips, eight frames each, every tier (viewer shots, background job)
cd /home/pjasicek/github/OpenYAMM/level_generation/creatures/mm9_ghoul_claude
S=$(cat work/strip_specs.txt)
for t in a b c; do scripts/vs.sh ghoul_$t review/strips_$t $S; done
echo STRIPS DONE
