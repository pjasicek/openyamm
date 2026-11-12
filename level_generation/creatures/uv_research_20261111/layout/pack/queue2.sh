#!/usr/bin/env bash
cd /home/pjasicek/github/OpenYAMM/level_generation/creatures/uv_research_20261111
SP=/home/pjasicek/github/OpenYAMM/level_generation/creatures/claude_shared/sparrow_venv
one(){ $SP/py/bin/python scripts/layout/sparrow_pack.py layout/pack/$1.npz layout/pack/$1_sparrow.npz --sparrow $SP/bin/sparrow --sep 4 --rotation continuous --seconds 60 --runs 5 > layout/pack/sparrow_$1.log 2>&1; }
until grep -q "QUEUE DONE" layout/pack/queue.log; do sleep 5; done
one m620_headw_base_fast & one m620_headw_seam6s125_fast & wait
echo QUEUE2 DONE
