#!/bin/bash
# all tiers: strips of every clip, joint close-ups (project folder). One viewer at a time.
G=/home/pjasicek/github/OpenYAMM/level_generation/creatures/claude_shared/gltf_venv/bin/python
for t in ${1:-a b c}; do
  S=$($G scripts/strips.py export/mm9_gezzampt.glb 6 2>/dev/null | tr '\n' ' ')
  timeout 900 scripts/vs.sh gezz_$t review/strips_$t $S
  timeout 600 scripts/closeups.sh gezz_$t c$t
done
echo FINALSHOTS
