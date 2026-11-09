#!/bin/bash
# scripts/shots.sh spec...  (name:clip:time:view:focus[:cam:target])
source /home/pjasicek/github/OpenYAMM/level_generation/creatures/mm9_lizardorc_claude/scripts/env.sh
cd $REPO; exec python3 tools/run_creature_review.py --project level_generation/creatures/mm9_lizardorc_claude --token $TOKEN ${TIER:+--tier $TIER} shots "$@"
