#!/bin/bash
. scripts/env.sh
scripts/gates.sh
$G scripts/plate_gate.py export/mm9_lizardorc.glb review/gates/plate.txt > /dev/null 2>&1
$G ../claude_shared/texture_quality.py export/mm9_lizardorc.glb > review/gates/texq.txt 2>&1
(cd $REPO; $G level_generation/creatures/claude_shared/floor/floor_audit.py --world mm9 --match 'MM9 Lizard*' > $P/review/gates/floor.txt 2>&1)
for t in a b c; do scripts/strips.sh $t liz_$t > /dev/null 2>&1; done
N=-.11,1.42,.15; G0=-.667,1.103,.111
for t in a b c; do TIER=liz_$t scripts/vshots.sh n1$t:Standing:0.3:front:body:-.12,1.45,1.0:$N n2$t:Standing:0.3:left:body:.8,1.45,.2:$N n3$t:Standing:0.3:quarter:body:-.15,.95,.95:$N n4$t:Standing:0.3:front:body:-.1,1.2,.95:-.1,1.2,.1 g1$t:Standing:0.3:quarter:body:-.95,1.0,.7:$G0 t1$t:AttackMelee:0.167:quarter:body:-.6,.8,1.5:-.09,.75,0 q$t:Standing:0.3:quarter:body:-1.6,1.3,3.2:0,.95,0 > /dev/null 2>&1; done
python3 scripts/sheet.py review/sheet_fix_tiers.png 7 330 n1a n2a n3a n4a g1a t1a qa n1b n2b n3b n4b g1b t1b qb n1c n2c n3c n4c g1c t1c qc
python3 scripts/sheet.py review/sheet_tiers.png 3 480 qa qb qc
(cd $REPO; timeout 300 ./build/game/openyamm --world mm9 --headless-run-regression-suite actors > $P/work/regression.log 2>&1)
(cd $REPO; python3 tools/run_creature_review.py --project level_generation/creatures/mm9_lizardorc_claude check > $P/work/check.log 2>&1)
echo D > work/deliver.done
