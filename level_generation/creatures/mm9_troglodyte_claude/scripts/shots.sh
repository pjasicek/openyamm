#!/bin/bash
# scripts/shots.sh spec...  (name:clip:time:view:focus[:cam:target])
cd /home/pjasicek/github/OpenYAMM; exec python3 tools/run_creature_review.py --project level_generation/creatures/mm9_troglodyte_claude --token be3ecdfca5fa4ec5b09123d1327bc520 ${TIER:+--tier $TIER} shots "$@"
