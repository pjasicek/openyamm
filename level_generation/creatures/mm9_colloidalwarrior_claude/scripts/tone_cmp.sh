#!/bin/bash
# MM9 vs ours under the same viewer light (review/viewer_cmp): Standing, quarter and front, per tier. Writes review/tone_cmp.png
for m in mm9_1 mm9_2 mm9_3 cw_a cw_b cw_c; do scripts/vsr_cmp.sh $m review/shots tc_${m}_q:Standing:0.5:front:body:-2.4,1.6,3.6:0,1.0,0 tc_${m}_f:Standing:0.5:front:body:0,1.2,4.2:0,1.0,0; done
python3 scripts/sheet.py review/tone_cmp.png 4 450 tc_mm9_1_q tc_cw_a_q tc_mm9_1_f tc_cw_a_f tc_mm9_2_q tc_cw_b_q tc_mm9_2_f tc_cw_b_f tc_mm9_3_q tc_cw_c_q tc_mm9_3_f tc_cw_c_f
