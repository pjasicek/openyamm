#!/bin/bash
# MM9 vs ours: MM9 Blender renders (work/mm9/p_*, work/flat) beside viewer shots of the same clip keys. Project folder.
mkdir -p review/compare
scripts/vs.sh dook_a review/compare o_stand:Standing:0.03:quarter:body o_walk:Walking:0.2:quarter:body o_run:Running:0.1:quarter:body o_atk:AttackMelee2:0.3:quarter:body o_rng:AttackRanged:0.5:quarter:body o_die:Death:1.0:quarter:body
python3 scripts/sheet.py review/sheet_mm9_vs_ours.png 6 420 work/mm9/p_stand@1_q34.png work/mm9/p_walk@6_q34.png work/mm9/p_run@3_q34.png work/mm9/p_Hattack2@9_q34.png work/mm9/p_Rattack1@15_q34.png work/mm9/p_die1@30_q34.png review/compare/o_stand.png review/compare/o_walk.png review/compare/o_run.png review/compare/o_atk.png review/compare/o_rng.png review/compare/o_die.png work/flat/ma_front.png work/flat/oa_front.png work/flat/mb_front.png work/flat/ob_front.png work/flat/mc_front.png work/flat/oc_front.png
