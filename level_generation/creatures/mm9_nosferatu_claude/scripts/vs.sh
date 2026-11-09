#!/bin/bash
# scripts/vs.sh <tier> spec...  : viewer shots with the lease. Spec name:clip:time:view:focus[:camera:target]
. scripts/env.sh
t=$1; shift
cd ../../..
python3 tools/run_creature_review.py --project level_generation/creatures/mm9_nosferatu_claude --token $TOKEN --tier $t shots "$@" 2>&1 | tail -2 | cut -c1-200
