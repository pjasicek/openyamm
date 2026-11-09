#!/bin/bash
cd /home/pjasicek/github/OpenYAMM/level_generation/creatures/claude_shared/detached_parts_mm9/run_20261030
cat list.txt | xargs -P 9 -I{} sh -c 'n=$(basename {} .glb); python3 /home/pjasicek/github/OpenYAMM/level_generation/creatures/claude_shared/detached_parts_audit.py {} --crops /home/pjasicek/github/OpenYAMM/level_generation/creatures/claude_shared/detached_parts_mm9/root_rules --json json/$n.json > json/$n.txt 2>&1; echo "$n exit $?"'
echo all_done
