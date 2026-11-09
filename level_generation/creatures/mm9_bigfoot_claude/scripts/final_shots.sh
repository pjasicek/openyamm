#!/bin/bash
# strips of every clip for every tier, joint close-ups (project folder). One viewer at a time.
G=/home/pjasicek/github/OpenYAMM/level_generation/creatures/claude_shared/gltf_venv/bin/python
for t in a b c; do
  S=$($G scripts/strips.py export/mm9_bigfoot.glb 6 2>/dev/null | sed 's/-2.6,2.0,4.0:0,1.1,0/-3.0,1.9,5.2:0,1.1,0.2/' | tr '\n' ' ')
  scripts/vsr.sh bf_$t review/strips_$t $S
  scripts/closeups.sh bf_$t c$t
done
echo FINALSHOTS
