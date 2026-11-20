#!/bin/bash
# comparison and strip shots. scripts/shots_all.sh  (project folder)
cd /home/pjasicek/github/OpenYAMM; P=level_generation/creatures/mm9_thrall_claude; T=$(cat $P/work/token)
for t in a b c; do python3 tools/run_creature_review.py --project $P --token $T --tier thrall_$t shots s${t}_front:Standing:0.5:front:body s${t}_back:Standing:0.5:back:body s${t}_quarter:Standing:0.5:quarter:body s${t}_rear:Standing:0.5:rear:body s${t}_fh:Standing:0.5:front:head s${t}_qh:Standing:0.5:quarter:head s${t}_sk:Standing:0.5:quarter:skirt 2>&1 | tail -1; done
