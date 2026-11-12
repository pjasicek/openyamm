#!/usr/bin/env bash
# sparrow packs, two at a time (each run uses many threads; the time limit is wall clock)
cd /home/pjasicek/github/OpenYAMM/level_generation/creatures/uv_research_20261111
SP=/home/pjasicek/github/OpenYAMM/level_generation/creatures/claude_shared/sparrow_venv
one(){ $SP/py/bin/python scripts/layout/sparrow_pack.py layout/pack/$1.npz layout/pack/$1_sparrow.npz --sparrow $SP/bin/sparrow --sep 4 --rotation continuous --seconds 60 --runs 5 > layout/pack/sparrow_$1.log 2>&1; }
while pgrep -f "sparrow_pack.py layout/pack/magreeb" > /dev/null; do sleep 5; done
one m620_body_base_fast & one m620_body_seam6s125_fast & wait
one hyd_body_base_fast & one hyd_body_seam6s125_fast & wait
one hyd_heads_base_fast & one hyd_heads_seam6s125_fast & wait
echo QUEUE DONE
