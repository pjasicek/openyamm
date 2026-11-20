#!/bin/bash
# Final review sheets, from viewer shots and MM9 renders. Project folder.
S=review/shots; M=review/mm9
python3 scripts/sheet.py review/sheet_mm9_vs_ours.png 6 400 $M/es1_front.png:MM9_A_rest $S/ta_f.png:ours_A $M/es2_front.png:MM9_B $S/tb_f.png:ours_B $M/es3_front.png:MM9_C $S/tc_f.png:ours_C $M/es1_back.png:MM9_A $S/ta_b.png:ours_A $M/es2_back.png:MM9_B $S/tb_b.png:ours_B $M/es3_back.png:MM9_C $S/tc_b.png:ours_C review/mm9_pose/walk_q34.png:MM9_walk $S/mv_walk.png:ours review/mm9_pose/rAttack1_q34.png:MM9_rAttack $S/mv_atk.png:ours review/mm9_pose/die1_q34.png:MM9_die $S/mv_die.png:ours review/mm9_pose/fidget2_q34.png:MM9_fidget2 $S/mv_fid.png:ours
python3 scripts/sheet.py review/sheet_tiers.png 3 560 $S/ta_f.png $S/tb_f.png $S/tc_f.png $S/ta_q.png $S/tb_q.png $S/tc_q.png $S/ta_b.png $S/tb_b.png $S/tc_b.png
for t in a b c; do python3 scripts/sheet.py review/sheet_close_$t.png 4 450 $S/t${t}_h.png $S/t${t}_hf.png $S/t${t}_sh.png $S/t${t}_sk.png $S/t${t}_ft.png $S/c${t}st0.png $S/c${t}st1.png $S/c${t}st3.png; (cd $S; python3 ../../scripts/sheet.py ../sheet_joints_$t.png 7 300 $(ls c${t}cr*.png c${t}ra*.png c${t}fi*.png c${t}de*.png c${t}dd*.png | sed 's/\(.*\)\.png/\1.png:\1/')); done
python3 scripts/strip_sheet.py stb review/strips_b_1.png 300 7 Standing Walking Running Backpedal BackpedalRun Fidget
python3 scripts/strip_sheet.py stb review/strips_b_2.png 300 7 Fidget2 Fidget3 Taunt AttackMelee AttackRanged AttackRanged2
python3 scripts/strip_sheet.py stb review/strips_b_3.png 300 7 ResurrectSpell Hit Hit2 Death Death2 Dead
for t in a c; do python3 scripts/strip_sheet.py st$t review/strips_${t}_1.png 240 7 Standing Walking Running Backpedal BackpedalRun Fidget Fidget2 Fidget3 Taunt; python3 scripts/strip_sheet.py st$t review/strips_${t}_2.png 240 7 AttackMelee AttackRanged AttackRanged2 ResurrectSpell Hit Hit2 Death Death2 Dead; done
python3 scripts/sheet.py review/sheet_ingame.png 4 460 review/ingame/f01.png review/ingame/f03.png review/ingame/f04.png review/ingame/f06.png review/ingame/h02.png review/ingame/h04.png review/ingame/h06.png review/ingame/h07.png
