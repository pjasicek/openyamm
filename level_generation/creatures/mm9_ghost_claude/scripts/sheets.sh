#!/bin/bash
# all viewer sheets (repo root)
P=level_generation/creatures/mm9_ghost_claude; R=$P/review
for t in ghost_a ghost_b ghost_c; do python3 $P/scripts/vshot.py $R/sheet_tier_$t.png 4 --tier $t ${t}_f:Standing:0:0:4:3:0.9 ${t}_q:Standing:0:35:4:3:0.9 ${t}_s:Standing:0:90:4:3:0.9 ${t}_b:Standing:0:180:4:3:0.9 ${t}_h:Standing:0:0:3:0.5:1.5 ${t}_hq:Standing:0:40:3:0.5:1.5 ${t}_t:Standing:0:15:3:0.8:0.95 ${t}_r:Standing:0:25:-10:1.0:0.45 2>&1 | tail -1 | cut -c1-70; done
python3 $P/scripts/vshot.py $R/sheet_closeups.png 5 \
 armpit1:Fidget2:1.667:150:-5:0.6:1.1 armpit2:Fidget2:1.667:-30:-5:0.6:1.1 armpit3:AttackMelee:0.3:-40:0:0.7:1.05 armpit4:Aware:0.5:0:0:0.7:1.05 armpit5:AttackMelee:0.3:40:0:0.7:1.05 \
 elbow1:Fidget2:1.2:60:0:0.6:1.2 elbow2:AttackMelee2:0.5:-70:0:0.7:0.95 elbow3:Fidget:2.5:-30:0:0.9:1.0 elbow4:Hit2:0.37:30:0:1.0:1.1 elbow5:Walking:0.3:-80:0:0.7:0.9 \
 neck1:Standing:0:30:15:0.45:1.3 neck2:Hit2:0.37:0:10:0.6:1.25 neck3:Fidget2:1.2:0:25:0.5:1.3 neck4:AttackRanged:0.3:180:20:0.5:1.3 neck5:Death:0.3:0:10:0.7:1.25 \
 mouth1:Standing:0:0:-5:0.3:1.53 mouth2:Standing:0:50:-5:0.3:1.53 mouth3:Fidget:1.5:0:-5:1.0:1.5 mouth4:Hit:0.4:30:0:1.0:1.5 mouth5:AttackMelee:0.5:40:0:1.0:1.4 2>&1 | tail -1 | cut -c1-80
python3 $P/scripts/vshot.py $R/sheet_seethrough.png 5 \
 s1:Standing:0.5:0:5:2.7:0.8 s2:Standing:0.5:60:5:2.7:0.8 s3:Standing:0.5:120:5:2.7:0.8 s4:Standing:0.5:180:5:2.7:0.8 s5:Standing:0.5:-120:5:2.7:0.8 \
 t1:Fidget:3.6:0:-20:2.2:0.8 t2:Fidget:3.6:60:-20:2.2:0.8 t3:Fidget:3.6:120:-20:2.2:0.8 t4:Fidget:3.6:180:-20:2.2:0.8 t5:Fidget:3.6:-120:-20:2.2:0.8 \
 u1:AttackMelee2:0.55:0:30:2.2:0.8 u2:AttackMelee2:0.55:60:30:2.2:0.8 u3:AttackMelee2:0.55:120:30:2.2:0.8 u4:AttackMelee2:0.55:180:30:2.2:0.8 u5:AttackMelee2:0.55:-120:30:2.2:0.8 \
 v1:Walking:0.3:0:-55:1.6:0.3 v2:Hit:0.5:60:-30:1.8:0.5 v3:Hit2:0.37:150:0:2.5:0.8 v4:AttackRanged:0.3:90:0:2.2:0.9 v5:Fidget2:1.2:-90:0:2.2:1.0 2>&1 | tail -1 | cut -c1-80
for t in ghost_a ghost_b ghost_c; do python3 $P/scripts/strips.py $t 2>&1 | tail -1 | cut -c1-80; done
