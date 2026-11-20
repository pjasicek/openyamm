#!/bin/bash
# all tiers: strips of every clip, joint close-ups (project folder). In order: scripts/final_shots.sh
G=/home/pjasicek/github/OpenYAMM/level_generation/creatures/claude_shared/gltf_venv/bin/python
for t in a b c; do
  S=$($G scripts/strips.py export/mm9_thrall.glb 6 2>/dev/null | tr '\n' ' ')
  scripts/vs.sh thrall_$t review/strips_$t $S
  scripts/closeups.sh thrall_$t c$t
done
echo FINALSHOTS
