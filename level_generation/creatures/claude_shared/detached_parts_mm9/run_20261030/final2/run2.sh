#!/bin/bash
cd /home/pjasicek/github/OpenYAMM/level_generation/creatures/claude_shared/detached_parts_mm9/run_20261030/final2
cat list2.txt | xargs -P 9 -I{} sh -c 'n=$(basename {} .glb); python3 /home/pjasicek/github/OpenYAMM/level_generation/creatures/claude_shared/detached_parts_audit.py {} --crops /home/pjasicek/github/OpenYAMM/level_generation/creatures/claude_shared/detached_parts_mm9/run_20261030/final2/crops --json $n.json > $n.txt 2>&1; echo "$n exit $?"'
echo all_done2
