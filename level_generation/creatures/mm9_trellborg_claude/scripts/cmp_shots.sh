#!/bin/bash
# viewer side of the MM9 comparison
cd /home/pjasicek/github/OpenYAMM; P=level_generation/creatures/mm9_thrall_claude; T=$(cat $P/work/token)
for t in a b c; do python3 tools/run_creature_review.py --project $P --token $T --tier thrall_$t shots s${t}_front:Standing:0.5:front:body s${t}_back:Standing:0.5:back:body s${t}_quarter:Standing:0.5:quarter:body s${t}_fh:Standing:0.5:front:head s${t}_qh:Standing:0.5:quarter:head s${t}_bh:Standing:0.5:back:head 2>&1 | tail -1; done
python3 tools/run_creature_review.py --project $P --token $T --tier thrall_a shots k0:Walking:0.4:quarter:body k1:Running:0.3:quarter:body k2:AttackMelee:0.73:quarter:body k3:AttackMelee2:0.95:quarter:body k4:AttackRanged:0.68:quarter:body k5:Hit:0.25:quarter:body k6:Death:1.0:quarter:body k7:Dead:0.5:quarter:body 2>&1 | tail -1
