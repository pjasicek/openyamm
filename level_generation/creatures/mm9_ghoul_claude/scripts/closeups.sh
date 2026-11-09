#!/bin/bash
# joint-framed viewer close-ups: knees, groin, armpits, elbows, neck, mouth in the crouch (Fidget2), the deep attack, and both death poses. Usage: scripts/closeups.sh <tier letter>
cd /home/pjasicek/github/OpenYAMM/level_generation/creatures/mm9_ghoul_claude
G=../claude_shared/gltf_venv/bin/python; t=$1; o=review/close_$t; mkdir -p $o
S=""
for cs in Fidget2:0.8 AttackMelee:0.5; do
  c=${cs%%:*}
  S="$S $($G scripts/close_specs.py export/mm9_ghoul.glb ${c}_ $cs 'Bip01 L Calf:0.3,0.3,1:0.5' 'Bip01 R Calf:-0.3,0.3,1:0.5' 'Bip01 L Calf:0.3,0.3,-1:0.5' 'Bip01 Pelvis:0.1,-0.5,1:0.65' 'Bip01 L UpperArm:0.7,-0.5,0.6:0.5' 'Bip01 R UpperArm:-0.7,-0.5,0.6:0.5' 'Bip01 L Forearm:0.5,0.3,-1:0.45' 'Bip01 Neck:-0.6,0.1,1:0.5' 'Bip01 Head:0.1,-0.1,1:0.42' 2>/dev/null)"
done
# corpses lie on the floor: every camera from above, or it stands inside the body
for cs in Death:1.45 Death2:1.45; do
  c=${cs%%:*}
  S="$S $($G scripts/close_specs.py export/mm9_ghoul.glb ${c}_ $cs 'Bip01 L Calf:0.2,1,0.3:0.55' 'Bip01 R Calf:-0.2,1,0.3:0.55' 'Bip01 L Calf:0.6,1,-0.3:0.55' 'Bip01 Pelvis:0.1,1,0.2:0.7' 'Bip01 L UpperArm:0.3,1,0:0.55' 'Bip01 R UpperArm:-0.3,1,0:0.55' 'Bip01 L Forearm:0.3,1,0.3:0.5' 'Bip01 Neck:0,1,0.2:0.6' 'Bip01 Head:0.2,1,0.1:0.5' 2>/dev/null)"
done
scripts/vs.sh ghoul_$t $o $S
python3 scripts/shots_sheet.py review/sheet_closeups_$t.png 9 300 $(for c in Fidget2 AttackMelee Death Death2; do for k in 0 1 2 3 4 5 6 7 8; do echo $o/${c}_$k.png; done; done)
