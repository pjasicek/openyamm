#!/bin/bash
# viewer shots of the test build; TIERS, one Chrome at a time. Project folder.
G=/home/pjasicek/github/OpenYAMM/level_generation/creatures/claude_shared/gltf_venv/bin/python
export VIEWER=viewer_test
S=$($G scripts/hand_specs.py export/mm9_trellborg.glb 2>/dev/null | tr '\n' ' ')
Q="fbW:Walking:0.25:front:body:-1.15,1.25,2.05:-0.1,1.05,0.1 fbR:Running:0.15:front:body:-1.15,1.25,2.05:-0.1,1.05,0.1"
for t in ${TIERS:-a b c}; do mkdir -p review/shots/cuff$t; scripts/vs.sh trell_$t review/shots/cuff$t $S $Q | tail -1 | cut -c1-10; done
echo CSHOTS_DONE
