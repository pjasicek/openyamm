#!/usr/bin/env bash
cd /home/pjasicek/github/OpenYAMM/level_generation/creatures/uv_research_20261111
SP=/home/pjasicek/github/OpenYAMM/level_generation/creatures/claude_shared/sparrow_venv
until grep -q "QUEUE2 DONE" layout/pack/queue2.log; do sleep 5; done
$SP/py/bin/python scripts/layout/sparrow_pack.py layout/pack/magreeb_seam6s125.npz layout/pack/magreeb_seam6s125_sparrow_long.npz --sparrow $SP/bin/sparrow --sep 4 --rotation continuous --seconds 90 --runs 7 --k0 1.095 > layout/pack/sparrow_magreeb_seam6s125_long.log 2>&1 &
$SP/py/bin/python scripts/layout/sparrow_pack.py layout/pack/magreeb_production.npz layout/pack/magreeb_sparrow_long.npz --sparrow $SP/bin/sparrow --sep 4 --rotation continuous --seconds 90 --runs 7 --k0 1.13 > layout/pack/sparrow_magreeb_long.log 2>&1 &
wait
echo QUEUE3 DONE
