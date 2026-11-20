#!/bin/bash
# Viewer shots for every model of the reduction viewer, one shot script at a time (any folder). -> review/shots_<model>/
cd /home/pjasicek/github/OpenYAMM
P=level_generation/creatures/mm9_dwarf_reduce_claude; TOKEN=$(cat $P/work/lease_token)
for t in ${MODELS:-a_r100 a_r71 b_r100 b_r71 c_r100 c_r71}; do
  python3 tools/run_creature_review.py --project $P --token $TOKEN --tier $t shots \
    st_front:Standing:0:front:body st_q:Standing:0:quarter:body st_back:Standing:0:back:body \
    walk_q:Walking:0.5:quarter:body run_l:Running:0.25:left:body atk_q:AttackMelee:0.5:quarter:body \
    head_front:Standing:0:front:head head_q:Standing:0:quarter:head head_side:Standing:0:right:head \
    hands_q:Standing:0:quarter:skirt arms_atk:AttackMelee:0.5:quarter:arms death_q:Death:1.4:quarter:body > $P/work/shots_$t.log 2>&1
  mv -T $P/review/shots $P/review/shots_$t || echo "MOVE FAILED $t"
done
echo SHOTSDONE
