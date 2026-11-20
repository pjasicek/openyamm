#!/usr/bin/env bash
# Acceptance shots from the review viewer, both tiers, and the sheets in review/sheets/. Args: <lease token>
set -euo pipefail
T=$1; cd "$(dirname "$0")/../../../.."; P=level_generation/creatures/mm9_mouse_claude
S=$P/review/shots
for t in a c; do
  python3 tools/run_creature_review.py --project $P --token $T --tier mouse_$t shots \
    ${t}_stand_q:Standing:0:quarter:body ${t}_stand_r:Standing:1.2:right:body ${t}_stand_l:Standing:0.6:left:feet \
    ${t}_rear:Standing:0:rear:body ${t}_head_f:Standing:0:front:head ${t}_head_q:Fidget:0.6:quarter:head \
    ${t}_fid_q:Fidget:1.3:quarter:body ${t}_hit_q:Hit:0.15:quarter:body ${t}_run_r:Running:0.03:right:feet \
    ${t}_run_r2:Running:0.09:right:feet ${t}_run_q:Running:0.15:quarter:arms ${t}_walk_q:Walking:0.2:quarter:feet \
    ${t}_walk_r:Walking:0.32:right:feet ${t}_back:Walking:0.1:back:body ${t}_death_r:Death:0.3:right:body \
    ${t}_death_q:Death:0.5:quarter:body ${t}_dead_r:Dead:0:right:body ${t}_dead_q:Dead:0:quarter:body | tail -1
  $P/scripts/close_shots.sh mouse_$t ${t}c | tail -1
done
python3 $P/scripts/shot_sheet.py $P/review/sheets/mouse_a_body.png 4 $S/a_stand_q.png $S/a_stand_r.png $S/a_rear.png $S/a_head_f.png $S/a_head_q.png $S/a_hit_q.png $S/a_fid_q.png $S/a_death_r.png $S/a_death_q.png $S/a_dead_r.png $S/a_dead_q.png $S/a_stand_l.png
python3 $P/scripts/shot_sheet.py $P/review/sheets/mouse_a_legs.png 4 $S/a_run_r.png $S/a_run_r2.png $S/a_run_q.png $S/a_walk_q.png $S/a_walk_r.png $S/a_back.png $S/ac_below.png $S/ac_below_run.png
python3 $P/scripts/shot_sheet.py $P/review/sheets/mouse_a_closeup.png 3 $S/ac_ear.png $S/ac_earback.png $S/ac_face.png $S/ac_rump.png $S/a_stand_l.png $S/a_head_f.png
python3 $P/scripts/shot_sheet.py $P/review/sheets/mouse_c_tier.png 4 $S/c_stand_q.png $S/c_stand_r.png $S/c_head_f.png $S/cc_face.png $S/c_run_r.png $S/c_rear.png $S/c_death_q.png $S/c_dead_q.png
