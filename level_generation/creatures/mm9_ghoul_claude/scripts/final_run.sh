#!/bin/bash
# everything on the final build, in order. Logs to work/final.log
cd /home/pjasicek/github/OpenYAMM/level_generation/creatures/mm9_ghoul_claude
scripts/gates.sh > work/gates.log 2>&1
echo GATES
scripts/closeups.sh a; scripts/closeups.sh b; scripts/closeups.sh c
echo CLOSE
scripts/strips_run.sh
(cd ../../..; python3 tools/run_creature_review.py --project level_generation/creatures/mm9_ghoul_claude --token 07199b41f5724e878af69fda14b4361c playback 2>&1 | tail -2)
echo FINAL DONE
