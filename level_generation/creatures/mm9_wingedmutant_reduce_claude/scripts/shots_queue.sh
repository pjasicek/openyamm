#!/bin/bash
# Viewer shots for every model of the reduction viewer, one shot script at a time. -> review/shots_<model>/
cd /home/pjasicek/github/OpenYAMM
P=level_generation/creatures/mm9_wingedmutant_reduce_claude; TOKEN=$(cat $P/work/lease_token)
for t in ${MODELS:-a_installed a_q82 b_installed b_q82 c_installed c_q82}; do
  python3 tools/run_creature_review.py --project $P --token $TOKEN --tier wmut_$t shots \
    st_front:Standing:0:front:body st_q:Standing:0:quarter:body st_back:Standing:0:back:body \
    walk_q:Walking:0.2:quarter:body atk_q:AttackMelee:0.4:quarter:body death_q:Death:1.4:quarter:body \
    head_front:Standing:0:front:shoulders head_q:Standing:0:quarter:shoulders > $P/work/shots_$t.log 2>&1
  mv -T $P/review/shots $P/review/shots_$t || echo "MOVE FAILED $t"
done
echo SHOTSDONE
