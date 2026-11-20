#!/bin/bash
# run 2 delivery sheets (r16, r17) from the published viewer (no gates, no regression): strips of every clip per tier, close-ups, tiers, MM9 vs ours. Project folder.
. scripts/env.sh
VIEWER=viewer scripts/viewer_update.sh ${1:-r16} > /dev/null
for t in a b c; do scripts/strips.sh $t liz_$t > /dev/null 2>&1; done
TIER=liz_a scripts/vshots.sh $($G scripts/closeups2.py 2>/dev/null) > work/close.log 2>&1
for t in a b c; do TIER=liz_$t scripts/vshots.sh t${t}_q:Standing:0.3:quarter:body:-1.6,1.3,3.2:0,.95,0 t${t}_f:Standing:0.3:front:body:0,1,3.6:0,.95,0 t${t}_b:Standing:0.3:back:body:0,1.2,-3.6:0,.95,0 t${t}_h:Standing:0.3:quarter:body:-.75,1.6,1.3:-.15,1.5,.3 > /dev/null 2>&1; done
sed -n '/^\$G - <<.P.$/,/^P$/p' scripts/deliver.sh | sed '1d;$d' > work/_sheets.py
$G work/_sheets.py
(cd $REPO; python3 tools/run_creature_review.py --project level_generation/creatures/mm9_lizardorc_claude check > $P/work/check.log 2>&1)
echo DELIVERDONE > work/deliver.done
