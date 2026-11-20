#!/bin/bash
cd /home/pjasicek/github/OpenYAMM/level_generation/creatures/mm9_troglodyte_claude; . scripts/env.sh
for w in body head cutoff; do F='^(USE|UVDONE)' W=300 scripts/run_b.sh uv_trog.py $P/work/joined.npz $P/work/cutoff.npz $P/work/uv $w; done
echo ALLDONE
